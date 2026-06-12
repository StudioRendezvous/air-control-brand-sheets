#!/usr/bin/env python3
"""Generate one-page endorsed lockup brand sheets for each OpCo."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dont_generator import generate_company_donts

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template" / "brand-sheet-template.html"
INDEX_TEMPLATE = ROOT / "template" / "index-template.html"
DATA_FILE = ROOT / "data" / "companies.json"
OUTPUT_DIR = ROOT / "output"
LOCAL_EXPORTS = ROOT / "assets" / "03 Exports"
LEGACY_EXPORTS = ROOT.parents[1] / "Logo Taglines" / "03 Exports"
DONTS_DIR = ROOT / "template" / "assets" / "donts"
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
            for candidate in primary.iterdir():
                if candidate.suffix.lower() in {".svg", ".png"}:
                    primary_logo = str(candidate.resolve())
                    break

        if reverse.exists():
            for candidate in reverse.iterdir():
                if candidate.suffix.lower() in {".svg", ".png"}:
                    reverse_logo = str(candidate.resolve())
                    break

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


def render_sheet(
    template: str,
    company: dict,
    *,
    assets_mode: str = "absolute",
    nav_html: str = "",
) -> str:
    primary = company.get("primary_logo") or ""
    reverse = company.get("reverse_logo") or ""

    if assets_mode == "relative" and primary and reverse:
        primary = f"assets/{Path(primary).name}"
        reverse = f"assets/{Path(reverse).name}"

    html = template
    html = html.replace("{{COMPANY_NAME}}", company["name"])
    html = html.replace("{{PRIMARY_LOGO}}", primary)
    html = html.replace("{{REVERSE_LOGO}}", reverse)
    html = html.replace("{{COMPANY_NAV}}", nav_html)
    return html


def write_index_page(companies: list[dict], dest: Path) -> None:
    ready = ready_companies(companies)
    cards = "\n".join(
        f'      <a class="company-card" href="{c["id"]}/index.html">'
        f'<img class="company-logo" src="{c["id"]}/assets/{Path(c["primary_logo"]).name}" '
        f'alt="" loading="lazy">'
        f'<span class="company-name">{c["name"]}</span>'
        f'<span class="company-arrow">→</span></a>'
        for c in ready
    )
    options = "\n".join(
        f'        <option value="{c["id"]}/index.html">{c["name"]}</option>'
        for c in ready
    )

    template = INDEX_TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("{{COMPANY_COUNT}}", str(len(ready)))
    html = html.replace("{{COMPANY_CARDS}}", cards)
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


def write_company_assets(company: dict, dest_dir: Path) -> None:
    assets_dir = dest_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    for key in ("primary_logo", "reverse_logo"):
        src = company.get(key)
        if not src:
            continue
        source = Path(src)
        if source.exists():
            target = assets_dir / source.name
            if not target.exists():
                target.write_bytes(source.read_bytes())

    primary = company.get("primary_logo")
    if company.get("id") == "hobbs":
        copy_dont_assets(dest_dir)
    elif primary and Path(primary).exists():
        generate_company_donts(Path(primary), dest_dir / "assets" / "donts")
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
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(companies, indent=2), encoding="utf-8")
        print(f"Wrote {len(companies)} companies to {DATA_FILE}")

    companies = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    all_companies = companies
    template = load_template()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
        if not company.get("primary_logo") or not company.get("reverse_logo"):
            print(f"Skipping {company['name']} — missing logo files")
            continue

        filename = f"Air Control - {company['name']} - An Air Company - Brand Sheet.html"
        out_path = OUTPUT_DIR / filename

        if use_folders:
            company_dir = OUTPUT_DIR / company["id"]
            company_dir.mkdir(parents=True, exist_ok=True)
            write_company_assets(company, company_dir)
            nav_html = build_company_nav(all_companies, company["id"])
            html = render_sheet(
                template,
                company,
                assets_mode="relative",
                nav_html=nav_html,
            )
            out_path = company_dir / "index.html"
        else:
            copy_dont_assets(OUTPUT_DIR)
            copy_air_logo(OUTPUT_DIR)
            html = render_sheet(template, company, assets_mode="absolute")
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
