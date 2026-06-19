# Don't Example Overrides

Drop custom don't artwork here when auto-generated crops don't work for a logo layout.

For **Without Symbol** / **Symbol Only** source pieces (icon + wordmark art), use **`assets/donts-symbols/`** instead — see that folder's README.

## Folder structure

Create one folder per company using the company **id** from `data/companies.json`:

```
assets/donts-overrides/
  advanced-thermal-solutions/
    06-without-symbol.png
    07-symbol-only.png
  hobbs/
    (optional — Hobbs uses comp art from template/assets/donts by default)
```

## File names

Use the exact filenames below. You only need to include the variants you want to override; missing files are still auto-generated.

| File | Label on sheet |
|------|----------------|
| `01-without-air-tagline.png` | Without AIR Tagline |
| `02-on-an-angle.png` | On an Angle |
| `03-colors-changed.png` | Colors Changed |
| `04-imperfect-scaling.png` | Imperfect Scaling |
| `05-on-colored-background.png` | On Colored Background |
| `06-without-symbol.png` | Without Symbol (wordmark only — no icon/mark) |
| `07-symbol-only.png` | Symbol Only (icon/mark only — no typography) |
| `08-outlines.png` | Outlines |

## Artwork specs

- **Canvas:** 720 × 640 px (images are scaled to fit if different)
- **Background:** White for most variants; light slate blue `#8DA3B8` for `05-on-colored-background.png`
- **Red X:** Added automatically on export — do not draw the X in your source files
- **Format:** PNG (transparent backgrounds OK)

## Regenerate after adding files

```bash
python3 scripts/generate-sheets.py --company "Advanced Thermal Solutions" --self-contained
# or all sheets:
python3 scripts/generate-sheets.py --self-contained
```
