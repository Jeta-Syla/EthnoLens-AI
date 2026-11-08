"""Rebuild the local database from zero with one command.

Steps:
  1. keep the extracted records: export them to data/raw/records_export.jsonl, then move the old
     database to data/ethnolens.db.bak (LLM extraction costs money, so records are never thrown away)
  2. create the empty schema
  3. download the Curious Cures transcriptions if they are not in data/raw/ yet
  4. split them into recipes and load them
  5. load the Albanian names (GBIF accepted names)
  6. put the exported records back
  7. with --extract: run the LLM on recipes that have no records yet (needs LLM_API_KEY in .env)
  8. map scientific names with GBIF
  9. index the passages for Ask EthnoLens

A teammate's records can be shared by copying their data/raw/records_export.jsonl into yours.
That file is not in Git: the records quote the transcriptions, whose licence is not stated.

Usage (from the repo root):
  python -m pipeline.rebuild
  python -m pipeline.rebuild --extract
"""

import argparse
import json
import os
import shutil

import requests

from backend.app import db
from pipeline import ingest, load_cudl, load_names

MANUSCRIPT = "MS-ADD-09308"
EXPORT_PATH = db.Path(os.environ.get("ETHNOLENS_RECORDS_EXPORT",
                                     db.REPO_ROOT / "data" / "raw" / "records_export.jsonl"))
RECORD_COLUMNS = ["id", "passage_id", "historical_name", "normalised_name", "candidate_scientific_name",
                  "canonical_name", "plant_part", "preparation", "described_use", "other_ingredients",
                  "span_start", "span_end", "evidence", "extraction_confidence", "mapping_confidence",
                  "review_status"]


def export_records() -> int:
    """Append the current database's records to the export file (existing ids are replaced)."""
    if not db.DB_PATH.exists():
        return 0
    with db.connect() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "records" not in tables:
            return 0
        rows = [dict(row) for row in conn.execute(f"SELECT {', '.join(RECORD_COLUMNS)} FROM records")]
    if not rows:
        return 0
    merged = {r["id"]: r for r in read_export()}
    merged.update({r["id"]: r for r in rows})
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPORT_PATH, "w", encoding="utf-8") as f:
        for row in merged.values():
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def read_export() -> list[dict]:
    if not EXPORT_PATH.exists():
        return []
    with open(EXPORT_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def import_records() -> int:
    """Load exported records whose passage exists in the new database."""
    with db.connect() as conn:
        passages = {row[0] for row in conn.execute("SELECT id FROM passages")}
        rows = [r for r in read_export() if r["passage_id"] in passages]
        db.upsert_records(conn, rows)
    return len(rows)


def rebuild(limit: int, extract: bool) -> None:
    exported = export_records()
    if db.DB_PATH.exists():
        shutil.move(db.DB_PATH, db.DB_PATH.with_suffix(".db.bak"))
        print(f"1. {exported} records exported to {EXPORT_PATH}; old database kept as {db.DB_PATH.name}.bak")
    else:
        print("1. no existing database")

    db.init_db()
    print(f"2. empty database created: {db.DB_PATH}")

    if not (ingest.RAW_DIR / MANUSCRIPT / "passages.jsonl").exists():
        print("3. downloading transcriptions from CUDL (about 3 minutes)")
        ingest.ingest(MANUSCRIPT)
    else:
        print("3. transcriptions already in data/raw/")

    print(f"4. {load_cudl.load(MANUSCRIPT, limit)} recipes loaded")

    print("5. Albanian names:")
    load_names.load()

    print(f"6. {import_records()} records restored from the export")

    if extract:
        from backend.app.models import Passage
        from pipeline.extract import extract_passage  # also loads .env

        if not os.getenv("LLM_API_KEY"):
            print("7. extraction skipped: LLM_API_KEY is not set in .env")
        else:
            with db.connect() as conn:
                todo = [Passage(**dict(row)) for row in conn.execute(
                    "SELECT id, document_id, folio, seq, text, method FROM passages p "
                    "WHERE NOT EXISTS (SELECT 1 FROM records r WHERE r.passage_id = p.id) ORDER BY seq")]
            failed = 0
            for passage in todo:
                try:
                    extract_passage(passage)
                except Exception as error:
                    failed += 1
                    print(f"   failed {passage.id}: {error}")
            print(f"7. extraction: {len(todo) - failed} of {len(todo)} recipes without records extracted")
            from pipeline.propose_names import propose

            print(f"   {propose()} record(s) given a candidate scientific name (checked by GBIF in step 8)")
            export_records()
    else:
        print("7. extraction skipped (add --extract to run the LLM on recipes without records)")

    from pipeline.taxonomy import map_records

    try:
        print(f"8. {map_records()} records mapped with GBIF")
    except requests.RequestException as error:
        print(f"8. GBIF unreachable, mapping skipped: {error}")

    from pipeline.rag import index_passages

    print(f"9. {index_passages()} passages indexed for Ask EthnoLens")

    with db.connect() as conn:
        counts = {table: conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                  for table in ("documents", "passages", "records", "plant_names")}
    print("Done:", ", ".join(f"{n} {table}" for table, n in counts.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the EthnoLens database from zero.")
    parser.add_argument("--limit", type=int, default=100, help="recipes to load (default 100)")
    parser.add_argument("--extract", action="store_true", help="run LLM extraction on recipes without records")
    args = parser.parse_args()
    rebuild(args.limit, args.extract)


if __name__ == "__main__":
    main()
