# Logo Overrides

Drop missing or corrected logo files here when the standard `assets/03 Exports/` package is incomplete.

## Naming (flat folder)

Use the company **id** from `data/companies.json`:

```
assets/logo-overrides/
  cardinal-control-systems-reverse.svg
  cardinal-control-systems-primary.png   (optional)
```

Suffix must be `-primary` or `-reverse`. Formats: `.svg`, `.png`, `.jpg`, `.jpeg`

## Or use a subfolder

```
assets/logo-overrides/
  cardinal-control-systems/
    reverse.svg
    primary.svg
```

## Standard export path (preferred)

You can also add files to the normal export tree:

```
assets/03 Exports/Cardinal Control Systems - An Air Company/RGB - Digital/Reverse Logo - RGB/
  Cardinal Control Systems Logo-Air Company-Reverse-RGB.svg
```

Then run:

```bash
python3 scripts/generate-sheets.py --refresh-data --self-contained
```
