#!/usr/bin/env python3
"""Generate one-page endorsed lockup brand sheets for each OpCo."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dont_generator import (
    generate_company_donts,
    generate_dont_variant,
    has_opaque_dark_backdrop,
    remove_pure_black_backdrop,
)
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template" / "brand-sheet-template.html"
INDEX_TEMPLATE = ROOT / "template" / "index-template.html"
DATA_FILE = ROOT / "data" / "companies.json"
OUTPUT_DIR = ROOT / "output"
LOCAL_EXPORTS = ROOT / "assets" / "03 Exports"
LEGACY_EXPORTS = ROOT.parents[1] / "Logo Taglines" / "03 Exports"
DONTS_DIR = ROOT / "template" / "assets" / "donts"
DONTS_OVERRIDES = ROOT / "assets" / "donts-overrides"
DONT_SYMBOLS_DIR = ROOT / "assets" / "donts-symbols"
NO_SYMBOL_DONTS_FILE = ROOT / "data" / "no-symbol-donts.json"
COMPANY_OVERRIDES_FILE = ROOT / "data" / "company-overrides.json"
SYMBOL_DONT_FILES = {"06-without-symbol.png", "07-symbol-only.png"}
TAGLINE_DONT_FILE = "01-without-air-tagline.png"
LOGO_OVERRIDES = ROOT / "assets" / "logo-overrides"
AIR_LOGO_SOURCE = ROOT / "assets" / "AIR Control Concepts - Primary Logo.svg"
AIR_LOGO_NAME = "air-control-primary-logo.svg"


def resolve_exports_root() -> Path:
    if LOCAL_EXPORTS.exists():
        return LOCAL_EXPORTS
    return LEGACY_EXPORTS


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower())
    return slug.strip("-")


def discover_companies(exports_root: Path) -> list[dict]:
    companies: list[dict] = []
    if not exports_root.exists():
        return companies

    for folder in sorted(exports_root.iterdir()):
        if not folder.is_dir() or folder.suffix == ".zip":
            continue

        display_name = folder.name.replace(" - An Air Company", "").strip()
        primary = folder / "RGB - Digital" / "Primary Logo - RGB"
        reverse = folder / "RGB - Digital" / "Reverse Logo - RGB"

        primary_logo = None
        reverse_logo = None

        if primary.exists():
            primary_logo = pick_logo_file(primary)

        if reverse.exists():
            reverse_logo = pick_logo_file(reverse)

        companies.append(
            {
                "id": slugify(display_name),
                "name": display_name,
                "folder": folder.name,
                "primary_logo": primary_logo,
                "reverse_logo": reverse_logo,
            }
        )

    return companies


LOGO_EXTENSIONS = (".svg", ".png", ".jpg", ".jpeg")


def pick_logo_file(directory: Path) -> str | None:
    def rank(path: Path) -> tuple[int, int, str]:
        ext_rank = 0 if path.suffix.lower() == ".png" else 1
        numbered = bool(re.search(r"-\d+$", path.stem))
        return (1 if numbered else 0, ext_rank, path.name.lower())

    candidates = sorted(
        (p for p in directory.iterdir() if p.suffix.lower() in LOGO_EXTENSIONS),
        key=rank,
    )
    return str(candidates[0].resolve()) if candidates else None


def apply_logo_overrides(companies: list[dict]) -> list[dict]:
    """Fill missing primary/reverse logos from assets/logo-overrides/."""
    if not LOGO_OVERRIDES.exists():
        return companies

    by_id = {company["id"]: company for company in companies}
    flat_files = [
        path
        for path in LOGO_OVERRIDES.iterdir()
        if path.is_file() and path.suffix.lower() in LOGO_EXTENSIONS
    ]

    for path in flat_files:
        stem = path.stem.lower()
        for suffix, key in (("-reverse", "reverse_logo"), ("-primary", "primary_logo")):
            if not stem.endswith(suffix):
                continue
            company_id = stem[: -len(suffix)]
            company = by_id.get(company_id)
            if company and not company.get(key):
                company[key] = str(path.resolve())
            break

    for subdir in sorted(LOGO_OVERRIDES.iterdir()):
        if not subdir.is_dir():
            continue
        company = by_id.get(subdir.name)
        if not company:
            continue
        if not company.get("primary_logo"):
            for name in ("primary", "Primary"):
                for ext in LOGO_EXTENSIONS:
                    candidate = subdir / f"{name}{ext}"
                    if candidate.exists():
                        company["primary_logo"] = str(candidate.resolve())
                        break
        if not company.get("reverse_logo"):
            for name in ("reverse", "Reverse", "reversed"):
                for ext in LOGO_EXTENSIONS:
                    candidate = subdir / f"{name}{ext}"
                    if candidate.exists():
                        company["reverse_logo"] = str(candidate.resolve())
                        break

    return companies


def finalize_company_logos(companies: list[dict]) -> list[dict]:
    """Use primary lockup for Reversed when no separate reverse file exists."""
    for company in companies:
        if company.get("primary_logo") and not company.get("reverse_logo"):
            company["reverse_logo"] = company["primary_logo"]
    return companies


def load_template() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def ready_companies(companies: list[dict]) -> list[dict]:
    return [
        c
        for c in companies
        if c.get("primary_logo") and c.get("reverse_logo")
    ]


def build_company_nav(companies: list[dict], current_id: str) -> str:
    ready = ready_companies(companies)
    if not ready:
        return ""

    options = []
    for company in ready:
        selected = " selected" if company["id"] == current_id else ""
        options.append(
            f'<option value="../{company["id"]}/index.html"{selected}>'
            f'{company["name"]}</option>'
        )

    current_idx = next(
        (i for i, c in enumerate(ready) if c["id"] == current_id),
        None,
    )
    prev_href = (
        f'../{ready[current_idx - 1]["id"]}/index.html'
        if current_idx is not None and current_idx > 0
        else ""
    )
    next_href = (
        f'../{ready[current_idx + 1]["id"]}/index.html'
        if current_idx is not None and current_idx < len(ready) - 1
        else ""
    )

    prev_link = (
        f'<a class="nav-btn" href="{prev_href}">← Prev</a>'
        if prev_href
        else '<span class="nav-btn disabled">← Prev</span>'
    )
    next_link = (
        f'<a class="nav-btn" href="{next_href}">Next →</a>'
        if next_href
        else '<span class="nav-btn disabled">Next →</span>'
    )

    return f"""<div class="sheet-top-bar">
  <a class="sheet-brand" href="../index.html">
    <img src="assets/air-control-primary-logo.svg" alt="AIR Control Concepts">
  </a>
  <nav class="sheet-nav" aria-label="Brand sheet navigation">
    <div class="nav-controls">
      <select class="nav-select" aria-label="Select company" onchange="if(this.value) window.location.href=this.value">
        {''.join(options)}
      </select>
      {prev_link}
      {next_link}
    </div>
    <a class="nav-home" href="../index.html">All Companies</a>
  </nav>
</div>"""


def load_no_symbol_dont_ids() -> set[str]:
    if NO_SYMBOL_DONTS_FILE.exists():
        return set(json.loads(NO_SYMBOL_DONTS_FILE.read_text(encoding="utf-8")))
    return set()


def load_company_overrides() -> dict[str, dict]:
    if COMPANY_OVERRIDES_FILE.exists():
        return json.loads(COMPANY_OVERRIDES_FILE.read_text(encoding="utf-8"))
    return {}


def company_override(company_id: str, overrides: dict[str, dict]) -> dict:
    return overrides.get(company_id, {})


def hidden_dont_files(company_id: str, overrides: dict[str, dict]) -> set[str]:
    hidden = company_override(company_id, overrides).get("hidden_donts", [])
    files: set[str] = set()
    for item in hidden:
        name = item if item.endswith(".png") else f"{item}.png"
        files.add(name)
    return files


def exact_dont_overrides(company_id: str, overrides: dict[str, dict]) -> set[str]:
    exact = company_override(company_id, overrides).get("exact_dont_overrides", [])
    return set(exact) if isinstance(exact, list) else set()


DONT_VARIANT_KEYS = (
    "angle_rotation",
    "angle_scale",
    "angle_max_w",
    "angle_max_h",
    "tagline_max_w",
    "tagline_max_h",
    "symbol_only_max_w",
    "symbol_only_max_h",
    "wordmark_max_w",
    "wordmark_max_h",
)


def dont_variant_options(company_id: str, overrides: dict[str, dict]) -> dict:
    cfg = company_override(company_id, overrides)
    return {key: cfg[key] for key in DONT_VARIANT_KEYS if key in cfg}


def build_logo_extra_css(company_id: str, overrides: dict[str, dict]) -> str:
    height = company_override(company_id, overrides).get("logo_height")
    if not height:
        return ""
    return f"""
    .logo-display img {{ height: {height}; }}
    .logo-primary {{ min-height: {height}; }}
"""


def build_tagline_dont_item(
    asset_version: str,
    company_id: str,
    overrides: dict[str, dict],
) -> str:
    if TAGLINE_DONT_FILE in hidden_dont_files(company_id, overrides):
        return ""
    v = f"?v={asset_version}" if asset_version else ""
    return f"""        <div class="dont-item">
          <div class="dont-label">Without AIR Tagline</div>
          <div class="dont-art-frame"><img class="dont-art" src="assets/donts/{TAGLINE_DONT_FILE}{v}" alt=""></div>
        </div>
"""


def build_symbol_donts_items(asset_version: str) -> str:
    v = f"?v={asset_version}" if asset_version else ""
    return f"""        <div class="dont-item">
          <div class="dont-label">Without Symbol</div>
          <div class="dont-art-frame"><img class="dont-art" src="assets/donts/06-without-symbol.png{v}" alt=""></div>
        </div>
        <div class="dont-item">
          <div class="dont-label">Symbol Only</div>
          <div class="dont-art-frame"><img class="dont-art" src="assets/donts/07-symbol-only.png{v}" alt=""></div>
        </div>
"""


def render_sheet(
    template: str,
    company: dict,
    *,
    assets_mode: str = "absolute",
    nav_html: str = "",
    asset_version: str = "",
    no_symbol_dont_ids: set[str] | None = None,
    company_overrides: dict[str, dict] | None = None,
) -> str:
    primary = company.get("primary_logo") or ""
    reverse = company.get("reverse_logo") or ""
    company_id = company.get("id", "")
    company_overrides = company_overrides or {}

    if assets_mode == "relative" and primary and reverse:
        primary = f"assets/{Path(primary).name}"
        reverse = f"assets/{Path(reverse).name}"

    html = template
    html = html.replace("{{COMPANY_NAME}}", company["name"])
    html = html.replace("{{PRIMARY_LOGO}}", primary)
    html = html.replace("{{REVERSE_LOGO}}", reverse)
    html = html.replace("{{COMPANY_NAV}}", nav_html)
    html = html.replace("{{ASSET_VERSION}}", asset_version)
    html = html.replace("{{LOGO_EXTRA_CSS}}", build_logo_extra_css(company_id, company_overrides))
    html = html.replace(
        "{{TAGLINE_DONT_ITEM}}",
        build_tagline_dont_item(asset_version, company_id, company_overrides),
    )
    skip_symbol = no_symbol_dont_ids and company_id in no_symbol_dont_ids
    symbol_donts = "" if skip_symbol else build_symbol_donts_items(asset_version)
    html = html.replace("{{SYMBOL_DONTS_ITEMS}}", symbol_donts)
    return html


def output_primary_logo_name(company_id: str) -> str | None:
    """Primary logo filename already copied into output/{id}/assets/."""
    assets_dir = OUTPUT_DIR / company_id / "assets"
    if not assets_dir.is_dir():
        return None

    def is_primary_logo(path: Path) -> bool:
        name = path.name.lower()
        if path.suffix.lower() not in LOGO_EXTENSIONS:
            return False
        if "air-control" in name:
            return False
        return "reverse" not in name

    def rank(path: Path) -> tuple[int, int, str]:
        numbered = bool(re.search(r"-\d+$", path.stem))
        ext_rank = 0 if path.suffix.lower() == ".png" else 1
        return (1 if numbered else 0, ext_rank, path.name.lower())

    candidates = sorted(
        (p for p in assets_dir.iterdir() if is_primary_logo(p)),
        key=rank,
    )
    return candidates[0].name if candidates else None


def write_index_page(companies: list[dict], dest: Path) -> None:
    ready = ready_companies(companies)
    cards = []
    for c in ready:
        logo_name = output_primary_logo_name(c["id"]) or Path(c["primary_logo"]).name
        cards.append(
            f'      <a class="company-card" href="{c["id"]}/index.html">'
            f'<img class="company-logo" src="{c["id"]}/assets/{logo_name}" '
            f'alt="" loading="lazy">'
            f'<span class="company-name">{c["name"]}</span>'
            f'<span class="company-arrow">→</span></a>'
        )
    cards_html = "\n".join(cards)
    options = "\n".join(
        f'        <option value="{c["id"]}/index.html">{c["name"]}</option>'
        for c in ready
    )

    template = INDEX_TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("{{COMPANY_COUNT}}", str(len(ready)))
    html = html.replace("{{COMPANY_CARDS}}", cards_html)
    html = html.replace("{{COMPANY_OPTIONS}}", options)
    dest.write_text(html, encoding="utf-8")


def copy_dont_assets(dest_dir: Path) -> None:
    dest_donts = dest_dir / "assets" / "donts"
    dest_donts.mkdir(parents=True, exist_ok=True)
    if not DONTS_DIR.exists():
        return
    for source in DONTS_DIR.glob("*.png"):
        if source.name == "full_page.png":
            continue
        target = dest_donts / source.name
        target.write_bytes(source.read_bytes())


def copy_air_logo(dest_dir: Path) -> None:
    if not AIR_LOGO_SOURCE.exists():
        return
    assets_dir = dest_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    target = assets_dir / AIR_LOGO_NAME
    if not target.exists():
        target.write_bytes(AIR_LOGO_SOURCE.read_bytes())


def write_logo_asset(source: Path, dest: Path, *, reverse: bool = False) -> None:
    """Copy logo art into the sheet folder, stripping black plates from reverse PNGs."""
    if source.suffix.lower() == ".png":
        image = Image.open(source).convert("RGBA")
        if reverse and has_opaque_dark_backdrop(image):
            image = remove_pure_black_backdrop(image)
        image.save(dest, format="PNG")
        return
    dest.write_bytes(source.read_bytes())


def write_company_assets(
    company: dict,
    dest_dir: Path,
    *,
    no_symbol_dont_ids: set[str] | None = None,
    company_overrides: dict[str, dict] | None = None,
) -> None:
    assets_dir = dest_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    for key in ("primary_logo", "reverse_logo"):
        src = company.get(key)
        if not src:
            continue
        source = Path(src)
        if source.exists():
            target = assets_dir / source.name
            write_logo_asset(source, target, reverse=(key == "reverse_logo"))

    no_symbol_dont_ids = no_symbol_dont_ids or set()
    company_overrides = company_overrides or {}
    primary = company.get("primary_logo")
    override_dir = DONTS_OVERRIDES / company["id"]
    symbols_dir = DONT_SYMBOLS_DIR / company["id"]
    skip_files = hidden_dont_files(company["id"], company_overrides)
    if company.get("id") in no_symbol_dont_ids:
        skip_files |= SYMBOL_DONT_FILES
    if company.get("id") == "hobbs":
        copy_dont_assets(dest_dir)
        if primary and Path(primary).exists():
            generate_dont_variant(
                Path(primary),
                dest_dir / "assets" / "donts" / "05-on-colored-background.png",
                "05-on-colored-background.png",
            )
    elif primary and Path(primary).exists():
        generate_company_donts(
            Path(primary),
            dest_dir / "assets" / "donts",
            override_dir=override_dir if override_dir.exists() else None,
            symbols_dir=symbols_dir if symbols_dir.exists() else None,
            skip_files=skip_files or None,
            variant_options=dont_variant_options(company["id"], company_overrides),
            exact_overrides=exact_dont_overrides(company["id"], company_overrides),
        )
    else:
        copy_dont_assets(dest_dir)
    copy_air_logo(dest_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", help="Generate only one company id or name")
    parser.add_argument(
        "--refresh-data",
        action="store_true",
        help="Rebuild data/companies.json from packaged logo exports",
    )
    parser.add_argument(
        "--self-contained",
        action="store_true",
        help="Copy logo assets into each output folder for portable HTML",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip generating output/index.html navigation page",
    )
    args = parser.parse_args()

    exports_root = resolve_exports_root()

    if args.refresh_data or not DATA_FILE.exists():
        companies = discover_companies(exports_root)
        companies = apply_logo_overrides(companies)
        companies = finalize_company_logos(companies)
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(companies, indent=2), encoding="utf-8")
        print(f"Wrote {len(companies)} companies to {DATA_FILE}")

    companies = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    companies = apply_logo_overrides(companies)
    companies = finalize_company_logos(companies)
    all_companies = companies
    template = load_template()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    asset_version = datetime.now().strftime("%Y%m%d%H%M")
    no_symbol_dont_ids = load_no_symbol_dont_ids()
    company_overrides = load_company_overrides()

    use_folders = args.self_contained or not args.company

    if args.company:
        needle = args.company.lower()
        companies = [
            c
            for c in companies
            if c["id"] == needle
            or c["name"].lower() == needle
            or needle in c["name"].lower()
        ]
        if not companies:
            raise SystemExit(f"No company matched '{args.company}'")

    generated = 0
    for company in companies:
        if not company.get("primary_logo"):
            print(f"Skipping {company['name']} — missing primary logo")
            continue

        filename = f"Air Control - {company['name']} - An Air Company - Brand Sheet.html"
        out_path = OUTPUT_DIR / filename

        if use_folders:
            company_dir = OUTPUT_DIR / company["id"]
            company_dir.mkdir(parents=True, exist_ok=True)
            write_company_assets(
                company,
                company_dir,
                no_symbol_dont_ids=no_symbol_dont_ids,
                company_overrides=company_overrides,
            )
            nav_html = build_company_nav(all_companies, company["id"])
            html = render_sheet(
                template,
                company,
                assets_mode="relative",
                nav_html=nav_html,
                asset_version=asset_version,
                no_symbol_dont_ids=no_symbol_dont_ids,
                company_overrides=company_overrides,
            )
            out_path = company_dir / "index.html"
        else:
            copy_dont_assets(OUTPUT_DIR)
            copy_air_logo(OUTPUT_DIR)
            html = render_sheet(
                template,
                company,
                assets_mode="absolute",
                asset_version=asset_version,
                no_symbol_dont_ids=no_symbol_dont_ids,
                company_overrides=company_overrides,
            )
            out_path = OUTPUT_DIR / filename

        out_path.write_text(html, encoding="utf-8")
        generated += 1
        print(f"Generated {out_path}")

    if use_folders and not args.no_index and generated:
        index_path = OUTPUT_DIR / "index.html"
        write_index_page(all_companies, index_path)
        print(f"Generated {index_path}")

    print(f"Done — {generated} sheet(s) created in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
