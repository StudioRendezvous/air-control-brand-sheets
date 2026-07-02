#!/usr/bin/env python3
"""Build logo package ZIP files from 03 Exports folders for each OpCo."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
DATA_FILE = ROOT / "data" / "companies.json"
LOCAL_EXPORTS = ROOT / "assets" / "03 Exports"
LEGACY_EXPORTS = ROOT.parents[1] / "Logo Taglines" / "03 Exports"


def company_logos_zip_filename(company: dict) -> str:
    return f"Air Control - {company['name']} - An Air Company - Logos.zip"


def export_dir_for_company(company: dict) -> Path | None:
    folder = company.get("folder")
    if not folder:
        return None
    for root in (LOCAL_EXPORTS, LEGACY_EXPORTS):
        path = root / folder
        if path.is_dir():
            return path
    return None


def zip_export_folder(source: Path, dest_zip: Path) -> None:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    root_name = source.name

    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            if path.name == ".DS_Store" or "__MACOSX" in path.parts:
                continue
            arcname = Path(root_name) / path.relative_to(source)
            archive.write(path, arcname.as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate logo package ZIP files")
    parser.add_argument("--company", help="Company id or name substring")
    parser.add_argument("--all", action="store_true", help="Generate for all companies")
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
        source = export_dir_for_company(company)
        if source is None:
            print(f"Skipping {company['name']} — no export folder found")
            continue

        company_dir = OUTPUT_DIR / company["id"]
        dest_zip = company_dir / company_logos_zip_filename(company)
        print(f"Zipping {source.name} → {dest_zip.name}...")
        zip_export_folder(source, dest_zip)
        generated += 1
        print(f"Generated {dest_zip}")

    print(f"Done — {generated} logo package(s) created")


if __name__ == "__main__":
    main()
