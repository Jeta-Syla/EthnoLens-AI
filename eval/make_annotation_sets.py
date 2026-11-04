"""Pick the 50 evaluation recipes and split them between the three annotators.

For each annotator this writes:
  eval/annotations/<name>.csv        one row per recipe to fill in (in Git)
  data/raw/annotation/<name>.md      the recipe texts to read while annotating (not in Git:
                                     the transcription licence is not stated)

Annotate by hand: these files are the gold standard the LLM extraction is measured against.
One CSV row per plant mention; copy a row when a recipe names more than one plant.

Usage (from the repo root, after pipeline.load_cudl):
  python -m eval.make_annotation_sets
"""

import csv
import random
from pathlib import Path

from backend.app import db

REPO_ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = REPO_ROOT / "eval" / "annotations"
TEXT_DIR = REPO_ROOT / "data" / "raw" / "annotation"

ANNOTATORS = {"dafina": 17, "ereza": 17, "jeta": 16}
MAX_CHARS = 1500  # very long passages are several salves merged by the splitter
SEED = 42
FIELDS = ["passage_id", "folio", "historical_name", "plant_part", "preparation", "described_use", "notes"]


def eligible_recipes() -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, folio, text FROM passages WHERE method = 'transcription' ORDER BY seq"
        ).fetchall()
    return [dict(r) for r in rows if not r["text"].startswith("A charm") and len(r["text"]) <= MAX_CHARS]


def main() -> None:
    recipes = eligible_recipes()
    total = sum(ANNOTATORS.values())
    chosen = sorted(random.Random(SEED).sample(recipes, total), key=lambda r: r["id"])
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    start = 0
    for name, count in ANNOTATORS.items():
        batch = chosen[start:start + count]
        start += count
        csv_path = CSV_DIR / f"{name}.csv"
        if csv_path.exists():
            print(f"{csv_path} exists, not overwritten")
        else:
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows({"passage_id": r["id"], "folio": r["folio"]} for r in batch)
        with open(TEXT_DIR / f"{name}.md", "w", encoding="utf-8") as f:
            for r in batch:
                f.write(f"## {r['id']} (f. {r['folio']})\n\n{r['text']}\n\n")
        print(f"{name}: {len(batch)} recipes -> {csv_path}")


if __name__ == "__main__":
    main()
