# 🌱 OpenPlantDB

An open, machine-readable database of garden plants — **germination times,
days to maturity, when to plant by USDA zone, mature size, and growing
directions** — released into the public domain (CC0) so anyone can build on it.

It exists because the best-known open crop dataset (OpenFarm) went offline and
its data disappeared with it. This one lives in flat files in git, so it can't
vanish, and anyone can fork, correct, or extend it.

> ⚠️ **Accuracy note.** Values are typical published horticultural ranges and
> vary by variety, region and microclimate. Treat them as planning guidance,
> not guarantees. Corrections via PR are very welcome.

## What's in it

| File | What |
|------|------|
| [`data/plants.json`](data/plants.json) | The full dataset — one rich JSON object per plant |
| [`data/plants.csv`](data/plants.csv) | The same data flattened to a spreadsheet-friendly CSV |
| [`data/zones.json`](data/zones.json) | USDA hardiness zones 1–13 with typical frost dates |
| [`schema/plants.sql`](schema/plants.sql) | Ready-to-load PostgreSQL (`CREATE TABLE` + upserts) |
| [`SCHEMA.md`](SCHEMA.md) | Field-by-field record schema |

Currently **22,901 plants** across vegetables, herbs, fruits, berries, flowers and
cover crops. (Run `python scripts/build.py` to see the live breakdown.)

## Each record has

- **Germination** — days to sprout + ideal soil-temperature band
- **Maturity** — days to first harvest/bloom, measured from seed *or* transplant
- **When to plant** — a seasonal anchor (`last_frost`, `first_frost`, `fall`, …)
  plus a week offset, so a per-zone calendar date can be *computed* from
  `data/zones.json` rather than hard-coded 13 times
- **Size** — mature height and spread (inches) + recommended spacing
- **Conditions** — sun, water, USDA zone range, frost tolerance, season
- **Directions** — 2–4 sentences: sow depth, care, and a harvest cue
- Plus scientific name, category/subcategory, and sow method

See [`SCHEMA.md`](SCHEMA.md) for the exact shape and two worked examples.

## When-to-plant, by zone

Planting dates aren't stored per zone — they're derived. Each plant records an
offset like *"6–8 weeks before last frost"*; combine it with a zone's frost date
from `data/zones.json`:

```python
import json, datetime as dt
plants = {p["slug"]: p for p in json.load(open("data/plants.json"))}
zones  = {z["zone"]: z for z in json.load(open("data/zones.json"))["zones"]}

def plant_window(slug, zone):
    p = plants[slug]; z = zones[str(zone)]
    anchor = {"last_frost": z["last_spring_frost"],
              "first_frost": z["first_fall_frost"]}.get(p["planting"]["anchor"])
    if not anchor:                       # frost-free zone or non-frost anchor
        return p["planting"]["note"]
    base = dt.datetime.strptime(f"{anchor} 2025", "%b %d %Y")
    w = p["planting"]["weeks_from_anchor"]
    start = base + dt.timedelta(weeks=w["min"]); end = base + dt.timedelta(weeks=w["max"])
    return f'{start:%b %d} – {end:%b %d}'

print("Tomato, zone 8:", plant_window("tomato", 8))
```

## Load it into PostgreSQL

```bash
psql "$YOUR_DSN" -f schema/plants.sql        # creates table `plants` + upserts every row
```

The table keeps flat columns for the common queryable fields **and** the full
original record in a `data JSONB` column, so nothing is lost:

```sql
SELECT common_name, germ_days_min, germ_days_max, maturity_days_min, maturity_days_max
  FROM plants WHERE category='vegetable' AND season='cool' ORDER BY maturity_days_min;
```

## Build the artifacts

The published files are generated from the per-category sources in
[`data/raw/`](data/raw). After editing a raw file:

```bash
python scripts/build.py     # validates, dedupes, regenerates plants.json / .csv / plants.sql
```

The build **fails loudly** on any schema violation, so a bad PR can't land.

## Contributing

Add or fix plants in the relevant `data/raw/*.json` file, run
`python scripts/build.py`, and open a PR. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
Only original wording in `directions` — never paste text from seed catalogs or
other sites.

## License

[CC0 1.0 Universal](LICENSE) — public domain. Use it for anything, no attribution
required (though a link back is appreciated).
