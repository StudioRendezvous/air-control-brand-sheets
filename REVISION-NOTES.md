# Endorsed Lockup Brand Sheet — Revision v2

## What changed (per client feedback)

| Removed | Added |
|---------|-------|
| Typography section (Gotham samples) | Endorsed lockup overview |
| Colors section (swatches) | Lockup Do's & Don'ts |
| | Field Applications grid (9 touchpoints) |
| | AIRlink portal + marketing contact footer |

**Page count:** Still one page (11" × 8.5" landscape).

## Layout structure

```
┌─────────────────────────┬──────────────────────────────────────┐
│ LOGO                    │ ENDORSED LOCKUP                      │
│                         │                                      │
│ Primary lockup          │ Intro paragraph                      │
│ Secondary (reversed)    │                                      │
│                         │ ┌─────────────┬─────────────┐        │
│ Don'ts (8-up grid)      │ │ Do          │ Don't       │        │
│                         │ └─────────────┴─────────────┘        │
│                         │                                      │
│                         │ Field Applications (3×3 grid)        │
│                         │                                      │
│                         │ AIRlink portal · Questions footer    │
└─────────────────────────┴──────────────────────────────────────┘
```

## Illustrator update checklist

Open `01 Design/Air Control - Small Brand Sheets - Design.ai` and:

1. **Delete** the Typography and Colors columns/frames on the right.
2. **Add** a new right column titled **Endorsed Lockup** (Metropolis Bold or Gotham Bold, 15pt).
3. **Paste** intro copy from `template/brand-sheet-template.html` (or this doc).
4. **Build** Do / Don't lists using Gotham Book 6.25–7pt with green ✓ and red ✕ markers.
5. **Build** Field Applications as a 3-column grid with Required/Optional badges.
6. **Add** footer rule with AIRlink + marketing@aircontrolconcepts.com.
7. **Keep** the left Logo column unchanged (Primary, Secondary, Don'ts).
8. **Create** a `[COMPANY]` layer or use Illustrator Variables for the two logo placements.

## Per-company logo swap (Illustrator)

For each of the ~46 OpCos in `Logo Taglines/03 Exports/`:

- **Primary:** `RGB - Digital/Primary Logo - RGB/*.svg`
- **Reverse:** `RGB - Digital/Reverse Logo - RGB/*.svg`

File naming pattern: `Air Control - {Company Name} - An Air Company - Brand Sheet.pdf`

## Automated HTML workflow (for review & batch export)

```bash
# Refresh company list from exports folder
python3 scripts/generate-sheets.py --refresh-data

# Generate one draft (e.g. Hobbs)
python3 scripts/generate-sheets.py --company hobbs

# Generate all companies
python3 scripts/generate-sheets.py

# Self-contained folders (portable HTML + assets)
python3 scripts/generate-sheets.py --self-contained
```

Open any HTML file in Chrome → Print → Save as PDF (landscape, no margins).

## Questions for tomorrow's meeting

1. **Tagline naming:** Client doc says "AN AIR COMPANY" — confirm this is final (vs. "An Air Control Company" in some filenames).
2. **Don'ts grid:** Keep the original 8 logo don'ts, or replace with lockup-specific examples?
3. **Field Applications density:** Is the 3×3 grid readable at print size, or should any items move to a separate reference doc?
4. **Company-specific colors:** Since color swatches are removed, should any OpCo-specific notes appear on their sheet?

## Source content

Lockup usage copy sourced from `AIR_CC_Lockup_Field_Applications_2.docx`.
