"""
Load data/raw/**.csv into Postgres (Supabase) raw_* schemas.

Usage:
    export DATABASE_URL="postgresql://..."   # or put it in .env
    python scripts/load_raw.py

Safe to rerun: every table is emptied before it's reloaded, so rows never
double up.
"""
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

# CREATE ... IF NOT EXISTS (not DROP + CREATE): dbt staging views depend on
# these tables, so Postgres refuses to drop them. Each table is emptied
# before loading instead (see TRUNCATE below).
YOUTUBE_DDL = """
CREATE TABLE IF NOT EXISTS raw_youtube.channels (
    channel_id        TEXT,
    handle            TEXT,
    channel_title     TEXT,
    owner_group       TEXT,
    brand             TEXT,
    subscriber_count  BIGINT,
    view_count        BIGINT,
    video_count       BIGINT,
    pulled_at         TIMESTAMP
);
CREATE TABLE IF NOT EXISTS raw_youtube.videos (
    video_id          TEXT,
    channel_id        TEXT,
    title             TEXT,
    published_at      TIMESTAMP,
    duration_iso      TEXT,
    made_for_kids     BOOLEAN,
    view_count        BIGINT,
    like_count        BIGINT,
    comment_count     BIGINT,
    pulled_at         TIMESTAMP
);
"""

# Household-level measurement (mock iSpot-style). No child-level or
# device-level fields by design - see README "Privacy-first by design".
MEASUREMENT_DDL = """
CREATE SCHEMA IF NOT EXISTS raw_measurement;
CREATE TABLE IF NOT EXISTS raw_measurement.household_reach (
    as_line_id                         TEXT,
    vendor                             TEXT,
    measured_through                   DATE,
    measured_impressions               BIGINT,
    households_reached                 BIGINT,
    impressions_in_kids_households     BIGINT,
    impressions_with_adult_coviewer    BIGINT,
    cord_free_households               BIGINT,
    households_also_reached_by_linear  BIGINT
);
"""


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    load_env()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Set DATABASE_URL (in .env or your shell) first.")

    loaded = []
    with psycopg.connect(url, autocommit=True) as conn:
        cur = conn.cursor()
        print("Creating raw schemas ...")
        cur.execute((ROOT / "sql" / "00_raw_schema.sql").read_text())

        yt_dir = RAW / "raw_youtube"
        if yt_dir.exists() and any(yt_dir.glob("*.csv")):
            cur.execute(YOUTUBE_DDL)
        else:
            print("  (no YouTube CSVs yet - run scripts/fetch_youtube.py; skipping raw_youtube)")

        if (RAW / "raw_measurement").exists():
            cur.execute(MEASUREMENT_DDL)

        for schema_dir in sorted(p for p in RAW.iterdir() if p.is_dir()):
            for csv_path in sorted(schema_dir.glob("*.csv")):
                table = f"{schema_dir.name}.{csv_path.stem}"
                header = csv_path.open().readline().strip()
                cur.execute(f"TRUNCATE {table}")   # rerun-safe: never double-load
                sql = (f"COPY {table} ({header}) FROM STDIN "
                       f"WITH (FORMAT csv, HEADER true, NULL '')")
                with cur.copy(sql) as copy, csv_path.open("rb") as f:
                    while chunk := f.read(1 << 16):
                        copy.write(chunk)
                cur.execute(f"SELECT count(*) FROM {table}")
                print(f"  loaded {table:45s} {cur.fetchone()[0]:>7,} rows")
                loaded.append(table)

        # Row Level Security: with RLS on and no policies, Supabase's public
        # API roles (anon/authenticated) can't read or write these tables.
        # The postgres role used by this script, dbt, and the Supabase MCP
        # bypasses RLS, so nothing in the pipeline or the Claude skill breaks.
        for table in loaded:
            cur.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        print(f"Row Level Security enabled on {len(loaded)} raw tables.")
    print("Done.")


if __name__ == "__main__":
    main()