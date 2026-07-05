#!/usr/bin/env python3
"""Load the dataset into PostgreSQL.

Usage:
    python scripts/load_postgres.py                 # uses $DATABASE_URL or $DSN
    python scripts/load_postgres.py "postgresql://user:pw@host/db"

Requires psycopg2 (`pip install psycopg2-binary`). Pure-SQL alternative with no
Python deps:  psql "$DSN" -f schema/plants.sql
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    dsn = (sys.argv[1] if len(sys.argv) > 1
           else os.environ.get("DATABASE_URL") or os.environ.get("DSN"))
    if not dsn:
        print("No DSN. Pass one as an argument or set $DATABASE_URL / $DSN.",
              file=sys.stderr)
        return 2
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed. Either `pip install psycopg2-binary` or "
              "run:  psql \"$DSN\" -f schema/plants.sql", file=sys.stderr)
        return 2
    sql = open(os.path.join(ROOT, "schema", "plants.sql")).read()
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute("SELECT count(*) FROM plants")
        print(f"Loaded. plants table now has {cur.fetchone()[0]} rows.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
