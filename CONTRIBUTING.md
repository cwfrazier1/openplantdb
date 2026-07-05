# Contributing to OpenPlantDB

Thanks for helping build a free, open plant reference. Corrections and new
plants are both welcome.

## Ground rules

1. **Original wording only.** The `directions` field (and everything else) must
   be written in your own words. Do **not** paste text from seed-catalog
   listings, extension articles, or other websites — that data can't be CC0.
   Facts (germination days, spacing, zones) aren't copyrightable; sentences are.
2. **Be accurate and conservative.** Use typical published ranges, not the best
   case. When varieties differ a lot, pick a representative middle and mention
   the spread in `directions`.
3. **One plant = one object**, following [`SCHEMA.md`](SCHEMA.md) exactly.

## Adding or fixing a plant

1. Edit the right file in [`data/raw/`](data/raw) (grouped by category). Add a
   new object or correct an existing one.
2. Give new plants a unique, lowercase, hyphenated `slug`.
3. Regenerate and validate:
   ```bash
   python scripts/build.py
   ```
   It rebuilds `data/plants.json`, `data/plants.csv` and `schema/plants.sql`,
   and **exits non-zero** if any record breaks the schema. Fix anything it flags.
4. Commit the raw file **and** the regenerated artifacts together, then open a PR
   describing what you changed and (roughly) where your numbers come from.

## Field cheat-sheet

- Ranges are always `{"min": n, "max": n}`. Use `null` bounds when a field
  genuinely doesn't apply (e.g. germination for a bulb-grown plant).
- `planting.weeks_from_anchor`: **negative = before** the anchor, positive after.
- Perennials/trees/berries: set `season: "perennial"`, use `usda_zones` as the
  hardiness survival range, and express years-to-first-harvest as days in
  `days_to_maturity` (note the years in `directions`).

## Reporting a bad value

No code needed — open an issue with the plant, the field, what it says, what it
should be, and your source. We'll fix it.
