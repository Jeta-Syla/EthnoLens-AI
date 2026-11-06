"""Evaluate extracted plant mentions against hand annotation CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from backend.app import db

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION_DIR = ROOT / "eval" / "annotations"


def _normalise(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _key(passage_id: str, historical_name: str, plant_part: str | None) -> tuple[str, str, str]:
    return (_normalise(passage_id), _normalise(historical_name), _normalise(plant_part))


def load_gold(paths: list[Path]) -> set[tuple[str, str, str]]:
    gold: set[tuple[str, str, str]] = set()
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if _normalise(row.get("historical_name")):
                    gold.add(_key(row.get("passage_id", ""), row["historical_name"], row.get("plant_part")))
    return gold


def load_predictions() -> set[tuple[str, str, str]]:
    db.init_db()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT passage_id, historical_name, plant_part FROM records"
        ).fetchall()
    return {_key(row["passage_id"], row["historical_name"], row["plant_part"]) for row in rows}


def evaluate(gold_paths: list[Path] | None = None) -> dict[str, float | int]:
    paths = gold_paths or sorted(ANNOTATION_DIR.glob("*.csv"))
    gold = load_gold(paths)
    predicted = load_predictions()
    true_positive = len(gold & predicted)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"gold": len(gold), "predicted": len(predicted), "true_positive": true_positive,
            "false_positive": false_positive, "false_negative": false_negative,
            "precision": precision, "recall": recall, "f1": f1}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate EthnoLens extraction records.")
    parser.add_argument("--annotator", action="append", choices=("dafina", "ereza", "jeta"),
                        help="Evaluate selected annotation set(s); defaults to all CSV files")
    args = parser.parse_args()
    paths = [ANNOTATION_DIR / f"{name}.csv" for name in args.annotator] if args.annotator else None
    print(json.dumps(evaluate(paths), indent=2))


if __name__ == "__main__":
    main()
