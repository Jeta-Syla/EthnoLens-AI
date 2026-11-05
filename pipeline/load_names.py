"""Load the Albanian plant names into the `plant_names` table, joined on GBIF accepted names.

Records get GBIF's accepted canonical name (pipeline.taxonomy), but Mustafa et al. (2012) sometimes
uses older names, e.g. Matricaria recutita for chamomile, now Matricaria chamomilla. Each published
name is therefore matched with GBIF too, and stored under the accepted name when the match is high or
medium. Genus-only entries (Iris sp., Thymus spp.) and unmatched names keep the published name; they
cannot join a species-level record.

The CSV stays as published in the article; only the database copy uses accepted names.

Usage (from the repo root, after pipeline.albanian_names):
  python -m pipeline.load_names
"""

import csv

from backend.app import db
from pipeline.albanian_names import OUT_PATH as CSV_PATH, SOURCE
from pipeline.taxonomy import match


def accepted_canonical(row: dict) -> str:
    result = match(row["scientific_name"])
    if result["mapping_confidence"] in ("high", "medium"):
        return result["canonical_name"]
    return row["canonical_name"]


def load() -> None:
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    renamed = {}
    for row in rows:
        canonical = accepted_canonical(row)
        if canonical != row["canonical_name"]:
            renamed[row["canonical_name"]] = canonical
        row["canonical_name"] = canonical

    db.init_db()
    with db.connect() as conn:
        # Nothing references plant_names, so a source is reloaded by replacing its rows.
        conn.execute("DELETE FROM plant_names WHERE source = ?", (SOURCE,))
        conn.executemany(
            "INSERT OR IGNORE INTO plant_names (canonical_name, local_name, language, region, source) "
            "VALUES (:canonical_name, :local_name, :language, :region, :source)",
            rows,
        )
        count = conn.execute("SELECT count(*) FROM plant_names WHERE source = ?", (SOURCE,)).fetchone()[0]

    print(f"{count} Albanian names loaded into {db.DB_PATH}")
    for old, new in sorted(renamed.items()):
        print(f"  {old} -> {new}")


if __name__ == "__main__":
    load()
