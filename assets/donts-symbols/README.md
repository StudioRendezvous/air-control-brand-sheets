# Symbol & Wordmark Source Art

Drop **source logo pieces** here for OpCos that have an icon/mark + typography, so the **Without Symbol** and **Symbol Only** don'ts are built correctly.

## Drop folder

```
assets/donts-symbols/
  advanced-thermal-solutions/
    symbol.png       ← icon/mark only (no type)
    wordmark.png     ← typography only (no icon)
  hobbs/
    symbol.svg
    wordmark.svg
  …
```

Use the company **id** from `data/companies.json` as the folder name (same as the URL slug, e.g. `air-components`, `hobbs`).

## Files to include

| File name | Used for | Sheet label |
|-----------|----------|-------------|
| `symbol.png` (or `.svg`) | Symbol Only don't | **Symbol Only** |
| `wordmark.png` (or `.svg`) | Without Symbol don't | **Without Symbol** |

You can drop one or both:

- **Both files** — best results; each don't is built from your art
- **Symbol only** — Symbol Only uses your file; Without Symbol still auto-generates from the primary logo
- **Wordmark only** — the reverse

Supported formats: `.png`, `.svg`, `.jpg`, `.jpeg`

## Artwork tips

- Export on **transparent** background when possible
- Show only the relevant piece (no extra padding or background boxes)
- Color should match the **primary** lockup
- **Do not** draw the red X — it is added automatically
- Any size is fine; the generator scales to fit the don't frame

## Companies that need symbol art

These OpCos **show** the Without Symbol / Symbol Only don'ts (wordmark + icon lockups):

advanced-thermal-solutions, air-components, air-mission-critical, airetech, bcs-building-controls-and-services, bay-associates, bluefield-systems, c-j-building-solutions, cg-wood, dorse, enerfit, energy-transfer-solutions, engineered-products, etairos-hvac, fes-fluid-equipment-solutions, force-equipment, hd-grant-co, hobbs, insight-partners, jm-oconnor, mechanical-and-plumbing-systems, midwest-machinery, mms-midwest-mechanical-solutions, nationwide-electric-supply, northrich-company, odell-hvac, rl-craig-company, technical-air-systems, thermair-systems

## Companies that skip symbol don'ts

These OpCos are **wordmark-only** — no folder needed here (see `data/no-symbol-donts.json`):

air-carolinas, ebs, eci, georgia-air-associates, jjp-mechanical-reps, jmb-associates, jobe-industrial-control-measurement, jorban-riscoe, klima-nj, klima-ny, marrs, mri-mechanical-reps, rea, slade-ross-inc, stan-weaver, tko

## Regenerate after adding files

```bash
python3 scripts/generate-sheets.py --company "Advanced Thermal Solutions" --self-contained
# or all sheets:
python3 scripts/generate-sheets.py --self-contained
```

## Finished overrides (optional)

If you prefer to drop a fully composed don't frame instead of source pieces, use `assets/donts-overrides/{company-id}/06-without-symbol.png` and `07-symbol-only.png`. Overrides there take priority over files in this folder.
