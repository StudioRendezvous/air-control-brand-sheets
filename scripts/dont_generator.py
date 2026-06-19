"""Generate per-company don't example images from primary logo assets."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

CANVAS_SIZE = (720, 640)
X_COLOR = (237, 28, 36, 255)
SLATE_BG = (141, 163, 184, 255)  # light slate blue for "on colored background" don't

DONT_FILES = [
    "01-without-air-tagline.png",
    "02-on-an-angle.png",
    "03-colors-changed.png",
    "04-imperfect-scaling.png",
    "05-on-colored-background.png",
    "06-without-symbol.png",
    "07-symbol-only.png",
    "08-outlines.png",
]

# Variants that usually need hand-built artwork (logo layout varies by OpCo).
MANUAL_VARIANT_HINTS = {
    "06-without-symbol.png",
    "07-symbol-only.png",
}


def load_logo_image(path: Path) -> Image.Image:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() == ".png":
        return Image.open(path).convert("RGBA")

    if path.suffix.lower() == ".svg":
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                ["qlmanage", "-t", "-s", "1400", "-o", tmp, str(path)],
                check=True,
                capture_output=True,
            )
            png_path = Path(tmp) / f"{path.name}.png"
            if not png_path.exists():
                raise RuntimeError(f"Failed to rasterize SVG: {path}")
            return Image.open(png_path).convert("RGBA")

    raise ValueError(f"Unsupported logo format: {path}")


def remove_near_white_background(image: Image.Image, threshold: int = 245) -> Image.Image:
    """Turn rasterized SVG backdrop pixels transparent."""
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a and r >= threshold and g >= threshold and b >= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def remove_near_dark_background(image: Image.Image, threshold: int = 42) -> Image.Image:
    """Turn near-black backdrop pixels transparent (e.g. badge exports on black)."""
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a and r <= threshold and g <= threshold and b <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def remove_pure_black_backdrop(image: Image.Image, threshold: int = 18) -> Image.Image:
    """Remove a solid black plate while keeping dark logo art (e.g. black type on black)."""
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a and max(r, g, b) <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def crop_to_alpha_bbox(image: Image.Image, threshold: int = 40) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.split()[3].point(lambda p: 255 if p > threshold else 0).getbbox()
    return rgba.crop(bbox) if bbox else rgba


def _darken_channel(channel: Image.Image, factor: float = 0.55, floor: int = 35) -> Image.Image:
    return channel.point(lambda p: max(floor, int(p * factor)) if p > 0 else 0)


def make_outline_logo(rgba: Image.Image) -> Image.Image:
    """Render full lockup as a visible colored stroke (hollow fill)."""
    rgba = crop_to_alpha_bbox(rgba)
    w, h = rgba.size
    max_dim = 900
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        rgba = rgba.resize(
            (max(1, int(w * ratio)), max(1, int(h * ratio))),
            Image.Resampling.LANCZOS,
        )
        w, h = rgba.size

    stroke_px = max(3, int(min(w, h) * 0.017))

    r, g, b, a = rgba.split()
    solid = a.point(lambda p: 255 if p > 40 else 0, mode="L")
    k = stroke_px * 2 + 1
    eroded = solid.filter(ImageFilter.MinFilter(k))
    stroke = ImageChops.subtract(solid, eroded)

    sr = ImageChops.multiply(r, solid)
    sg = ImageChops.multiply(g, solid)
    sb = ImageChops.multiply(b, solid)
    cr = _darken_channel(sr.filter(ImageFilter.MaxFilter(k)))
    cg = _darken_channel(sg.filter(ImageFilter.MaxFilter(k)))
    cb = _darken_channel(sb.filter(ImageFilter.MaxFilter(k)))

    # Light logos need a darker stroke to read on white.
    lum = Image.merge("RGB", (cr, cg, cb)).convert("L")
    weak = lum.point(lambda p: 255 if p < 90 else 0)
    off_black = (35, 33, 33)
    cr = Image.composite(cr, Image.new("L", rgba.size, off_black[0]), weak)
    cg = Image.composite(cg, Image.new("L", rgba.size, off_black[1]), weak)
    cb = Image.composite(cb, Image.new("L", rgba.size, off_black[2]), weak)

    return Image.merge(
        "RGBA",
        (
            ImageChops.multiply(cr, stroke),
            ImageChops.multiply(cg, stroke),
            ImageChops.multiply(cb, stroke),
            stroke,
        ),
    )


def apply_wrong_color_recolor(rgba: Image.Image) -> Image.Image:
    """Shift logo to an obviously wrong pink palette for the colors-changed don't."""
    rgba = rgba.convert("RGBA")
    r, g, b, a = rgba.split()
    lum = ImageOps.grayscale(rgba.convert("RGB"))
    tinted = ImageOps.colorize(lum, black="#C2185B", white="#F48FB1")
    tr, tg, tb = tinted.split()
    mask = a.point(lambda p: 255 if p > 40 else 0)
    return Image.merge(
        "RGBA",
        (
            ImageChops.multiply(tr, mask),
            ImageChops.multiply(tg, mask),
            ImageChops.multiply(tb, mask),
            a,
        ),
    )


def fit_logo(logo: Image.Image, max_w: int, max_h: int) -> Image.Image:
    ratio = min(max_w / logo.width, max_h / logo.height)
    size = (max(1, int(logo.width * ratio)), max(1, int(logo.height * ratio)))
    return logo.resize(size, Image.Resampling.LANCZOS)


def paste_centered(canvas: Image.Image, layer: Image.Image) -> Image.Image:
    base = canvas.copy().convert("RGBA")
    x = (base.width - layer.width) // 2
    y = (base.height - layer.height) // 2
    base.paste(layer, (x, y), layer)
    return base


def draw_red_x(image: Image.Image) -> Image.Image:
    """Match Hobbs comp-art X proportions (measured from template/assets/donts)."""
    result = image.convert("RGBA")
    draw = ImageDraw.Draw(result)
    w, h = result.size
    pad_x = int(w * 0.132)
    pad_y = int(h * 0.086)
    line_w = max(3, int(min(w, h) * 0.0235))
    draw.line([(pad_x, pad_y), (w - pad_x, h - pad_y)], fill=X_COLOR, width=line_w)
    draw.line([(w - pad_x, pad_y), (pad_x, h - pad_y)], fill=X_COLOR, width=line_w)
    return result


def blank_canvas(color: tuple[int, int, int, int] = (255, 255, 255, 255)) -> Image.Image:
    return Image.new("RGBA", CANVAS_SIZE, color)


def compose_variant(
    logo: Image.Image,
    variant: str,
    *,
    variant_options: dict | None = None,
) -> Image.Image:
    opts = variant_options or {}
    # Full-color primary lockup on a colored field (wrong usage) — not the reversed mark.
    working = remove_near_white_background(logo.copy())

    if variant == "01-without-air-tagline":
        w, h = working.size
        working = working.crop((0, 0, w, int(h * 0.82)))

    elif variant == "02-on-an-angle":
        working = crop_to_alpha_bbox(working)
        rotation = float(opts.get("angle_rotation", 18))
        angle_scale = float(opts.get("angle_scale", 1.18))
        working = working.rotate(
            rotation,
            expand=True,
            resample=Image.Resampling.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        )
        working = working.resize(
            (
                max(1, int(working.width * angle_scale)),
                max(1, int(working.height * angle_scale)),
            ),
            Image.Resampling.LANCZOS,
        )
        working = crop_to_alpha_bbox(working)

    elif variant == "03-colors-changed":
        working = apply_wrong_color_recolor(working)

    elif variant == "04-imperfect-scaling":
        working = working.resize(
            (max(1, int(working.width * 1.35)), max(1, int(working.height * 0.72))),
            Image.Resampling.BICUBIC,
        )

    elif variant == "06-without-symbol":
        w, h = working.size
        working = working.crop((int(w * 0.32), 0, w, h))

    elif variant == "07-symbol-only":
        w, h = working.size
        working = working.crop((0, 0, int(w * 0.35), h))

    elif variant == "08-outlines":
        working = make_outline_logo(working)

    if variant == "05-on-colored-background":
        max_w = int(CANVAS_SIZE[0] * 0.90)
        max_h = int(CANVAS_SIZE[1] * 0.78)
    elif variant == "02-on-an-angle":
        max_w = int(CANVAS_SIZE[0] * float(opts.get("angle_max_w", 0.86)))
        max_h = int(CANVAS_SIZE[1] * float(opts.get("angle_max_h", 0.72)))
    elif variant == "07-symbol-only":
        max_w = int(CANVAS_SIZE[0] * float(opts.get("symbol_only_max_w", 0.86)))
        max_h = int(CANVAS_SIZE[1] * float(opts.get("symbol_only_max_h", 0.72)))
    else:
        max_w = int(CANVAS_SIZE[0] * 0.86)
        max_h = int(CANVAS_SIZE[1] * 0.72)
    working = fit_logo(working, max_w, max_h)

    bg = SLATE_BG if variant == "05-on-colored-background" else (255, 255, 255, 255)
    canvas = blank_canvas(bg)
    canvas = paste_centered(canvas, working)
    return draw_red_x(canvas)


def has_opaque_dark_backdrop(image: Image.Image, threshold: int = 42) -> bool:
    """True when corners look like a solid dark plate (not black logo art)."""
    rgba = image.convert("RGBA")
    w, h = rgba.size
    if w < 2 or h < 2:
        return False
    corners = (
        rgba.getpixel((0, 0)),
        rgba.getpixel((w - 1, 0)),
        rgba.getpixel((0, h - 1)),
        rgba.getpixel((w - 1, h - 1)),
    )
    dark_opaque = sum(
        1
        for r, g, b, a in corners
        if a > 200 and r <= threshold and g <= threshold and b <= threshold
    )
    return dark_opaque >= 3


def compose_asset_dont(
    asset: Image.Image,
    *,
    variant_options: dict | None = None,
    kind: str = "symbol",
) -> Image.Image:
    """Build a standard don't frame from a standalone symbol or wordmark asset."""
    opts = variant_options or {}
    working = asset.copy()
    if has_opaque_dark_backdrop(working):
        working = remove_pure_black_backdrop(working)
    working = remove_near_white_background(working)
    working = crop_to_alpha_bbox(working)
    if kind == "symbol":
        max_w = int(CANVAS_SIZE[0] * float(opts.get("symbol_only_max_w", 0.86)))
        max_h = int(CANVAS_SIZE[1] * float(opts.get("symbol_only_max_h", 0.72)))
    else:
        max_w = int(CANVAS_SIZE[0] * float(opts.get("wordmark_max_w", 0.86)))
        max_h = int(CANVAS_SIZE[1] * float(opts.get("wordmark_max_h", 0.72)))
    working = fit_logo(working, max_w, max_h)
    canvas = blank_canvas()
    canvas = paste_centered(canvas, working)
    return draw_red_x(canvas)


def find_symbol_asset(symbols_dir: Path, base_name: str) -> Path | None:
    for ext in (".png", ".svg", ".jpg", ".jpeg"):
        candidate = symbols_dir / f"{base_name}{ext}"
        if candidate.exists():
            return candidate
    return None


def apply_override(source: Path, dest: Path) -> None:
    image = Image.open(source).convert("RGBA")
    if image.size != CANVAS_SIZE:
        fitted = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
        ratio = min(CANVAS_SIZE[0] / image.width, CANVAS_SIZE[1] / image.height)
        size = (
            max(1, int(image.width * ratio)),
            max(1, int(image.height * ratio)),
        )
        resized = image.resize(size, Image.Resampling.LANCZOS)
        x = (CANVAS_SIZE[0] - size[0]) // 2
        y = (CANVAS_SIZE[1] - size[1]) // 2
        fitted.paste(resized, (x, y), resized)
        image = fitted
    result = draw_red_x(image)
    result.convert("RGB").save(dest, format="PNG")


def apply_tagline_override(
    source: Path,
    dest: Path,
    *,
    variant_options: dict | None = None,
) -> None:
    """Place a no-tagline lockup on white with breathing room and a red X."""
    opts = variant_options or {}
    image = load_logo_image(source)
    working = remove_near_dark_background(image, threshold=55)
    working = remove_near_white_background(working)
    working = crop_to_alpha_bbox(working)
    max_w = int(CANVAS_SIZE[0] * float(opts.get("tagline_max_w", 0.58)))
    max_h = int(CANVAS_SIZE[1] * float(opts.get("tagline_max_h", 0.46)))
    working = fit_logo(working, max_w, max_h)
    canvas = blank_canvas()
    canvas = paste_centered(canvas, working)
    result = draw_red_x(canvas)
    result.convert("RGB").save(dest, format="PNG")


def generate_dont_variant(primary_logo: Path, dest: Path, filename: str) -> None:
    """Generate one don't example image (e.g. Hobbs colored-background only)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    logo = load_logo_image(primary_logo)
    variant = filename.replace(".png", "")
    image = compose_variant(logo, variant)
    image.convert("RGB").save(dest, format="PNG")


def generate_company_donts(
    primary_logo: Path,
    dest_dir: Path,
    *,
    override_dir: Path | None = None,
    symbols_dir: Path | None = None,
    skip_files: set[str] | None = None,
    variant_options: dict | None = None,
) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    logo = load_logo_image(primary_logo)
    skip = skip_files or set()
    symbol_sources = {
        "06-without-symbol.png": "wordmark",
        "07-symbol-only.png": "symbol",
    }

    for filename in DONT_FILES:
        if filename in skip:
            continue
        dest = dest_dir / filename
        override_path = (override_dir / filename) if override_dir else None
        if override_path and override_path.exists():
            if filename == "01-without-air-tagline.png":
                apply_tagline_override(override_path, dest, variant_options=variant_options)
            else:
                apply_override(override_path, dest)
            continue

        if symbols_dir and filename in symbol_sources:
            asset_path = find_symbol_asset(symbols_dir, symbol_sources[filename])
            if asset_path:
                asset = load_logo_image(asset_path)
                kind = symbol_sources[filename]
                compose_asset_dont(
                    asset,
                    variant_options=variant_options,
                    kind=kind,
                ).convert("RGB").save(dest, format="PNG")
                continue

        variant = filename.replace(".png", "")
        image = compose_variant(logo, variant, variant_options=variant_options)
        image.convert("RGB").save(dest, format="PNG")
