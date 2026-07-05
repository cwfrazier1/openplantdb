# OpenPlantDB — record schema

Every plant is one JSON object. Category files under `data/raw/*.json` are a
JSON array of these objects. The build script merges, validates and flattens
them into `data/plants.json` and `data/plants.csv`.

All numeric ranges are `{"min": <n>, "max": <n>}`. Use `null` for a bound that
genuinely doesn't apply (e.g. germination for a plant grown only from bulbs).

| Field | Type | Meaning |
|-------|------|---------|
| `slug` | string | lowercase, hyphenated, unique id (`"cherokee-purple-tomato"` or `"tomato"`) |
| `common_name` | string | display name (`"Tomato"`) |
| `scientific_name` | string | binomial (`"Solanum lycopersicum"`) |
| `category` | enum | `vegetable` \| `herb` \| `fruit` \| `berry` \| `flower` \| `cover-crop` |
| `subcategory` | string | free text (`"fruiting"`, `"brassica"`, `"annual"`, `"cane fruit"`) |
| `days_to_germination` | range | days from sowing to sprout |
| `germination_soil_temp_f` | range | ideal soil temp band (°F) for germination |
| `days_to_maturity` | range | days to first harvest / bloom, measured from `maturity_from` |
| `maturity_from` | enum | `seed` \| `transplant` |
| `sow_method` | enum | `direct` \| `indoor-start` \| `transplant` \| `bulb` \| `tuber` \| `cutting` \| `division` |
| `season` | enum | `cool` \| `warm` \| `perennial` |
| `frost_tolerance` | enum | `tender` \| `half-hardy` \| `hardy` |
| `planting` | object | when to plant relative to a seasonal anchor (see below) |
| `usda_zones` | range | recommended USDA hardiness zones (1–13). For perennials this is survival range; for annuals, where it's commonly grown |
| `spacing_in` | range | in-row spacing between plants (inches) |
| `height_in` | range | mature height (inches) |
| `spread_in` | range | mature width / spread (inches) |
| `sun` | enum | `full` \| `partial` \| `shade` (full = 6+ hrs direct) |
| `water` | enum | `low` \| `moderate` \| `high` |
| `directions` | string | 2–4 sentence growing directions: sowing depth, care, harvest cue |
| `sources` | string[] | short provenance notes (keep generic; never copy proprietary text) |

### `planting` object

```json
"planting": {
  "anchor": "last_frost",
  "weeks_from_anchor": {"min": -8, "max": -6},
  "note": "Start indoors 6–8 weeks before the last spring frost; transplant 1–2 weeks after."
}
```

- `anchor`: `last_frost` \| `first_frost` \| `soil_workable` \| `spring` \| `fall`
- `weeks_from_anchor`: weeks relative to the anchor. **Negative = before** the
  anchor, positive = after. A per-zone calendar date is computed downstream by
  adding this offset to that zone's frost date (see `data/zones.json`).
- `note`: human-readable planting instruction.

### Two worked examples

```json
{
  "slug": "tomato",
  "common_name": "Tomato",
  "scientific_name": "Solanum lycopersicum",
  "category": "vegetable",
  "subcategory": "fruiting",
  "days_to_germination": {"min": 5, "max": 10},
  "germination_soil_temp_f": {"min": 70, "max": 85},
  "days_to_maturity": {"min": 60, "max": 85},
  "maturity_from": "transplant",
  "sow_method": "indoor-start",
  "season": "warm",
  "frost_tolerance": "tender",
  "planting": {"anchor": "last_frost", "weeks_from_anchor": {"min": -8, "max": -6},
    "note": "Start indoors 6–8 weeks before last frost; transplant 1–2 weeks after."},
  "usda_zones": {"min": 3, "max": 11},
  "spacing_in": {"min": 24, "max": 36},
  "height_in": {"min": 36, "max": 96},
  "spread_in": {"min": 24, "max": 48},
  "sun": "full",
  "water": "moderate",
  "directions": "Sow seed 1/4 in deep in warm mix. Transplant after nights stay above 50°F, burying two-thirds of the stem for stronger roots. Cage or stake indeterminate types and water evenly to prevent blossom-end rot. Harvest when fruit is fully colored and slightly soft.",
  "sources": ["general horticultural reference"]
},
{
  "slug": "carrot",
  "common_name": "Carrot",
  "scientific_name": "Daucus carota subsp. sativus",
  "category": "vegetable",
  "subcategory": "root",
  "days_to_germination": {"min": 10, "max": 21},
  "germination_soil_temp_f": {"min": 45, "max": 85},
  "days_to_maturity": {"min": 60, "max": 80},
  "maturity_from": "seed",
  "sow_method": "direct",
  "season": "cool",
  "frost_tolerance": "half-hardy",
  "planting": {"anchor": "last_frost", "weeks_from_anchor": {"min": -3, "max": 2},
    "note": "Direct sow 3 weeks before to 2 weeks after last frost; succession sow every 3 weeks."},
  "usda_zones": {"min": 3, "max": 11},
  "spacing_in": {"min": 2, "max": 3},
  "height_in": {"min": 8, "max": 12},
  "spread_in": {"min": 2, "max": 3},
  "sun": "full",
  "water": "moderate",
  "directions": "Sow seed 1/4 in deep in loose, stone-free soil and keep the surface consistently moist until sprouting, which is slow. Thin seedlings to 2–3 in so roots can size up. Harvest when shoulders reach desired diameter; flavor sweetens after a light frost.",
  "sources": ["general horticultural reference"]
}
```
