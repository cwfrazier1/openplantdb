#!/usr/bin/env python3
"""Merge, validate and flatten the raw category files into the published
artifacts:  data/plants.json, data/plants.csv, schema/plants.sql

Usage:  python scripts/build.py
Exit code is non-zero if any record fails validation.
"""
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")


def _norm(s):
    """Lowercase, drop parentheticals & punctuation for identity matching."""
    s = (s or "").lower().strip()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def identity(rec):
    """Two records are the same plant when their common name AND scientific
    name normalize equal. Cultivars with distinct scientific names stay
    separate (e.g. Blanket Flower Gaillardia pulchella vs. x grandiflora)."""
    return _norm(rec.get("common_name")) + "|" + _norm(rec.get("scientific_name"))


def _completeness(rec):
    """Rank duplicates so the richest record wins the slug."""
    filled = sum(1 for v in rec.values() if v not in (None, "", [], {}))
    return (filled, len(rec.get("directions") or ""))


def dedupe_identity(records):
    """Collapse same-plant/different-slug rows. Keep the most complete record;
    on a tie prefer the slug that reads like the common name, then the
    shortest. Returns (kept_records, removed_count)."""
    groups = {}
    order = []
    for rec in records:
        key = identity(rec)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(rec)

    kept, removed = [], 0
    for key in order:
        bucket = groups[key]
        if len(bucket) == 1:
            kept.append(bucket[0])
            continue
        name_slug = _norm(bucket[0].get("common_name")).replace(" ", "-")

        def score(r):
            comp = _completeness(r)
            slug = r.get("slug") or ""
            return (comp[0], comp[1], slug == name_slug, -len(slug), slug)

        winner = max(bucket, key=score)
        kept.append(winner)
        removed += len(bucket) - 1
    return kept, removed

CATEGORIES = {"vegetable", "herb", "fruit", "berry", "flower", "cover-crop"}
MATURITY_FROM = {"seed", "transplant"}
SOW = {"direct", "indoor-start", "transplant", "bulb", "tuber", "cutting", "division"}
SEASON = {"cool", "warm", "perennial"}
FROST = {"tender", "half-hardy", "hardy"}
ANCHOR = {"last_frost", "first_frost", "soil_workable", "spring", "fall"}
SUN = {"full", "partial", "shade"}
WATER = {"low", "moderate", "high"}

RANGE_FIELDS = ["days_to_germination", "germination_soil_temp_f",
                "days_to_maturity", "spacing_in", "height_in", "spread_in"]


def err(slug, msg, bag):
    bag.append(f"[{slug}] {msg}")


def is_range(v):
    return isinstance(v, dict) and set(v) >= {"min", "max"}


def validate(rec, bag):
    slug = rec.get("slug", "<no-slug>")
    for f in ("slug", "common_name", "category"):
        if not rec.get(f):
            err(slug, f"missing required field '{f}'", bag)
    if rec.get("category") not in CATEGORIES:
        err(slug, f"bad category {rec.get('category')!r}", bag)
    if rec.get("maturity_from") not in MATURITY_FROM:
        err(slug, f"bad maturity_from {rec.get('maturity_from')!r}", bag)
    if rec.get("sow_method") not in SOW:
        err(slug, f"bad sow_method {rec.get('sow_method')!r}", bag)
    if rec.get("season") not in SEASON:
        err(slug, f"bad season {rec.get('season')!r}", bag)
    if rec.get("frost_tolerance") not in FROST:
        err(slug, f"bad frost_tolerance {rec.get('frost_tolerance')!r}", bag)
    if rec.get("sun") not in SUN:
        err(slug, f"bad sun {rec.get('sun')!r}", bag)
    if rec.get("water") not in WATER:
        err(slug, f"bad water {rec.get('water')!r}", bag)
    for f in RANGE_FIELDS + ["usda_zones"]:
        if f in rec and rec[f] is not None and not is_range(rec[f]):
            err(slug, f"field '{f}' must be a {{min,max}} range", bag)
    p = rec.get("planting") or {}
    if p.get("anchor") not in ANCHOR:
        err(slug, f"bad planting.anchor {p.get('anchor')!r}", bag)
    if not is_range(p.get("weeks_from_anchor") or {}):
        err(slug, "planting.weeks_from_anchor must be a {min,max} range", bag)
    if not rec.get("directions"):
        err(slug, "missing directions", bag)


def rng(rec, field, key):
    v = rec.get(field)
    return v.get(key) if isinstance(v, dict) else None


FLAT_COLUMNS = [
    ("slug", lambda r: r.get("slug")),
    ("common_name", lambda r: r.get("common_name")),
    ("scientific_name", lambda r: r.get("scientific_name")),
    ("category", lambda r: r.get("category")),
    ("subcategory", lambda r: r.get("subcategory")),
    ("germ_days_min", lambda r: rng(r, "days_to_germination", "min")),
    ("germ_days_max", lambda r: rng(r, "days_to_germination", "max")),
    ("germ_soil_temp_f_min", lambda r: rng(r, "germination_soil_temp_f", "min")),
    ("germ_soil_temp_f_max", lambda r: rng(r, "germination_soil_temp_f", "max")),
    ("maturity_days_min", lambda r: rng(r, "days_to_maturity", "min")),
    ("maturity_days_max", lambda r: rng(r, "days_to_maturity", "max")),
    ("maturity_from", lambda r: r.get("maturity_from")),
    ("sow_method", lambda r: r.get("sow_method")),
    ("season", lambda r: r.get("season")),
    ("frost_tolerance", lambda r: r.get("frost_tolerance")),
    ("plant_anchor", lambda r: (r.get("planting") or {}).get("anchor")),
    ("plant_weeks_min", lambda r: ((r.get("planting") or {}).get("weeks_from_anchor") or {}).get("min")),
    ("plant_weeks_max", lambda r: ((r.get("planting") or {}).get("weeks_from_anchor") or {}).get("max")),
    ("plant_note", lambda r: (r.get("planting") or {}).get("note")),
    ("usda_zone_min", lambda r: rng(r, "usda_zones", "min")),
    ("usda_zone_max", lambda r: rng(r, "usda_zones", "max")),
    ("spacing_in_min", lambda r: rng(r, "spacing_in", "min")),
    ("spacing_in_max", lambda r: rng(r, "spacing_in", "max")),
    ("height_in_min", lambda r: rng(r, "height_in", "min")),
    ("height_in_max", lambda r: rng(r, "height_in", "max")),
    ("spread_in_min", lambda r: rng(r, "spread_in", "min")),
    ("spread_in_max", lambda r: rng(r, "spread_in", "max")),
    ("sun", lambda r: r.get("sun")),
    ("water", lambda r: r.get("water")),
    ("directions", lambda r: r.get("directions")),
]

SQL_COLS = [c for c, _ in FLAT_COLUMNS] + ["sources", "data"]


def sql_lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def main():
    files = sorted(glob.glob(os.path.join(RAW, "*.json")))
    records, seen, bag = [], {}, []
    for fp in files:
        with open(fp) as fh:
            try:
                arr = json.load(fh)
            except json.JSONDecodeError as e:
                bag.append(f"[{os.path.basename(fp)}] invalid JSON: {e}")
                continue
        if not isinstance(arr, list):
            bag.append(f"[{os.path.basename(fp)}] top level must be a JSON array")
            continue
        for rec in arr:
            slug = rec.get("slug")
            if slug in seen:
                continue  # first file wins; dedupe silently
            validate(rec, bag)
            seen[slug] = fp
            records.append(rec)

    if bag:
        print("VALIDATION FAILED:\n  " + "\n  ".join(bag), file=sys.stderr)
        return 1

    records, dup_removed = dedupe_identity(records)
    if dup_removed:
        print(f"dedupe: collapsed {dup_removed} duplicate record(s)")

    records.sort(key=lambda r: (r.get("category", ""), r.get("common_name", "")))

    with open(os.path.join(ROOT, "data", "plants.json"), "w") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    with open(os.path.join(ROOT, "data", "plants.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([c for c, _ in FLAT_COLUMNS])
        for r in records:
            w.writerow([fn(r) for _, fn in FLAT_COLUMNS])

    with open(os.path.join(ROOT, "schema", "plants.sql"), "w") as fh:
        fh.write(open(os.path.join(ROOT, "schema", "table.sql")).read())
        fh.write("\n\n")
        for r in records:
            vals = [sql_lit(fn(r)) for _, fn in FLAT_COLUMNS]
            vals.append(sql_lit(json.dumps(r.get("sources", []))))
            vals.append(sql_lit(json.dumps(r, ensure_ascii=False)))
            updates = ",\n    ".join(
                f"{c}=EXCLUDED.{c}" for c in SQL_COLS if c != "slug")
            fh.write(
                "INSERT INTO plants (" + ",".join(SQL_COLS) + ")\n"
                "  VALUES (" + ",".join(vals) + ")\n"
                "  ON CONFLICT (slug) DO UPDATE SET\n    " + updates + ";\n")

    by_cat = {}
    for r in records:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    print(f"OK  {len(records)} plants")
    for k in sorted(by_cat):
        print(f"    {k:12} {by_cat[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
