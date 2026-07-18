#!/usr/bin/env python3
"""Load the dataset into PostgreSQL, straight from data/plants.json.

Usage:
    python scripts/load_postgres.py                 # uses $DATABASE_URL or $DSN
    python scripts/load_postgres.py "postgresql://user:pw@host/db"

Requires psycopg2 (`pip install psycopg2-binary`). This loader reads
data/plants.json directly, so it does NOT need the large generated
schema/plants.sql. Pure-SQL alternative (no Python deps):

    python scripts/build.py            # (re)generates schema/plants.sql locally
    psql "$DSN" -f schema/plants.sql
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build import FLAT_COLUMNS, SQL_COLS  # noqa: E402  (column definitions live in build.py)


def main():
    dsn = (sys.argv[1] if len(sys.argv) > 1
           else os.environ.get("DATABASE_URL") or os.environ.get("DSN"))
    if not dsn:
        print("No DSN. Pass one as an argument or set $DATABASE_URL / $DSN.",
              file=sys.stderr)
        return 2
    try:
        import psycopg2
        from psycopg2.extras import execute_values, Json
    except ImportError:
        print("psycopg2 not installed. Either `pip install psycopg2-binary` or "
              "run:  python scripts/build.py && psql \"$DSN\" -f schema/plants.sql",
              file=sys.stderr)
        return 2

    records = json.load(open(os.path.join(ROOT, "data", "plants.json")))
    ddl = open(os.path.join(ROOT, "schema", "table.sql")).read()

    rows = []
    for r in records:
        vals = [fn(r) for _, fn in FLAT_COLUMNS]
        vals.append(Json(r.get("sources", [])))
        vals.append(Json(r))
        rows.append(vals)

    updates = ",\n    ".join(f"{c}=EXCLUDED.{c}" for c in SQL_COLS if c != "slug")
    insert = (
        "INSERT INTO plants (" + ",".join(SQL_COLS) + ") VALUES %s "
        "ON CONFLICT (slug) DO UPDATE SET\n    " + updates
    )

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(ddl)
        execute_values(cur, insert, rows, page_size=1000)
        cur.execute("SELECT count(*) FROM plants")
        print(f"Loaded {len(rows)} records. plants table now has {cur.fetchone()[0]} rows.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
