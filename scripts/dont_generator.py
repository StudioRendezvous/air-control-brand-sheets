"""Generate per-company don't example images from primary logo assets."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

CANVAS_SIZE = (720, 640)
X_COLOR = (237, 28, 36, 255)
CYAN_BG = (0, 184, 212, 255)

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
    result = image.convert("RGBA")
    draw = ImageDraw.Draw(result)
    w, h = result.size
    pad = int(min(w, h) * 0.06)
    line_w = max(6, int(min(w, h) * 0.055))
    draw.line([(pad, pad), (w - pad, h - pad)], fill=X_COLOR, width=line_w)
    draw.line([(w - pad, pad), (pad, h - pad)], fill=X_COLOR, width=line_w)
    return result


def blank_canvas(color: tuple[int, int, int, int] = (255, 255, 255, 255)) -> Image.Image:
    return Image.new("RGBA", CANVAS_SIZE, color)


def compose_variant(logo: Image.Image, variant: str) -> Image.Image:
    working = logo.copy()

    if variant == "01-without-air-tagline":
        w, h = working.size
        working = working.crop((0, 0, w, int(h * 0.82)))

    elif variant == "02-on-an-angle":
        working = working.rotate(
            18,
            expand=True,
            resample=Image.Resampling.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        )

    elif variant == "03-colors-changed":
        r, g, b, a = working.split()
        working = Image.merge("RGBA", (b, g, r, a))
        working = ImageEnhance.Color(working).enhance(1.8)

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
        alpha = working.split()[3]
        gray = working.convert("L")
        contour = gray.filter(ImageFilter.CONTOUR)
        contour = ImageOps.autocontrast(contour)
        contour = contour.point(lambda p: 0 if p < 120 else 255)
        working = Image.merge("RGBA", (contour, contour, contour, alpha))

    max_w = int(CANVAS_SIZE[0] * 0.86)
    max_h = int(CANVAS_SIZE[1] * 0.72)
    working = fit_logo(working, max_w, max_h)

    bg = CYAN_BG if variant == "05-on-colored-background" else (255, 255, 255, 255)
    canvas = blank_canvas(bg)
    canvas = paste_centered(canvas, working)
    return draw_red_x(canvas)


def generate_company_donts(primary_logo: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    logo = load_logo_image(primary_logo)

    for filename in DONT_FILES:
        variant = filename.replace(".png", "")
        image = compose_variant(logo, variant)
        image.convert("RGB").save(dest_dir / filename, format="PNG")

