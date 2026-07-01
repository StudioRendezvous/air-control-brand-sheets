#!/usr/bin/env python3
"""Generate PDF brand sheets from self-contained HTML using Playwright."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
DATA_FILE = ROOT / "data" / "companies.json"

# Letter portrait — full sheet (11in wide) is scaled to fit on one page.
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11.0
SHEET_WIDTH_IN = 11.0
# Keep in sync with @media print body padding in brand-sheet-template.html
PRINT_TOP_PADDING_IN = 0.5
PRINT_BOTTOM_PADDING_IN = 0.15
CSS_PX_PER_IN = 96.0


def company_pdf_filename(company: dict) -> str:
    return f"Air Control - {company['name']} - An Air Company - Brand Sheet.pdf"


def sheet_scale_for_letter(content_height_px: float) -> float:
    content_height_in = content_height_px / CSS_PX_PER_IN
    width_scale = PAGE_WIDTH_IN / SHEET_WIDTH_IN
    height_scale = PAGE_HEIGHT_IN / content_height_in
    return min(width_scale, height_scale, 1.0)


def generate_pdf(html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    html_path = html_path.resolve()
    pdf_path = pdf_path.resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.emulate_media(media="print")
        content_height_px = page.evaluate("() => document.body.scrollHeight")
        scale = sheet_scale_for_letter(content_height_px)
        page.pdf(
            path=str(pdf_path),
            format="Letter",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            scale=scale,
        )
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PDF brand sheets from HTML")
    parser.add_argument(
        "--company",
        help="Company id or name substring (omit to require --all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate PDFs for every company with index.html",
    )
    args = parser.parse_args()

    companies = json.loads(DATA_FILE.read_text(encoding="utf-8"))

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
    elif not args.all:
        raise SystemExit("Specify --company or --all")

    generated = 0
    for company in companies:
        company_dir = OUTPUT_DIR / company["id"]
        html_path = company_dir / "index.html"
        if not html_path.is_file():
            print(f"Skipping {company['name']} — no index.html at {html_path}")
            continue

        pdf_path = company_dir / company_pdf_filename(company)
        print(f"Generating {pdf_path.name}...")
        generate_pdf(html_path, pdf_path)
        generated += 1
        print(f"Generated {pdf_path}")

    print(f"Done — {generated} PDF(s) created")


if __name__ == "__main__":
    main()
