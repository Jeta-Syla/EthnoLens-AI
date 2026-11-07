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


def load_gold(paths: list[Path], human_only: bool = False) -> tuple[set[tuple[str, str, str]], set[str]]:
    """Gold plant mentions, and every annotated passage (including recipes with no plant).

    A row with neither a plant name nor a note is a recipe not annotated yet, and is left out; a recipe
    without plants is marked with a note such as "no plant named".
    human_only drops recipes annotated with AI assistance (notes starting "[AI-assisted]").
    """
    gold: set[tuple[str, str, str]] = set()
    passages: set[str] = set()
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if human_only and (row.get("notes") or "").startswith("[AI-assisted]"):
                    continue
                if not _normalise(row.get("historical_name")) and not _normalise(row.get("notes")):
                    continue  # not annotated yet
                passages.add(_normalise(row.get("passage_id")))
                if _normalise(row.get("historical_name")):
                    gold.add(_key(row.get("passage_id", ""), row["historical_name"], row.get("plant_part")))
    return gold, passages


def load_predictions(passages: set[str]) -> set[tuple[str, str, str]]:
    """Extracted records, only for the annotated passages: the other recipes have no gold to compare with."""
    db.init_db()
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT passage_id, historical_name, plant_part FROM records"
        ).fetchall()
    keys = {_key(row["passage_id"], row["historical_name"], row["plant_part"]) for row in rows}
    return {key for key in keys if key[0] in passages}


def archive_quality() -> dict[str, float | int]:
    """Measure source traceability and highlight-span validity for all records."""
    db.init_db()
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT r.passage_id, r.historical_name, r.span_start, r.span_end, p.text
               FROM records r JOIN passages p ON p.id = r.passage_id"""
        ).fetchall()
    total = len(rows)
    traceable = sum(bool(row["passage_id"] and row["text"]) for row in rows)
    valid_spans = sum(
        row["span_start"] is not None
        and row["span_end"] is not None
        and row["text"][row["span_start"]:row["span_end"]] == row["historical_name"]
        for row in rows
    )
    return {
        "records_checked": total,
        "traceable_records": traceable,
        "traceability": traceable / total if total else 0.0,
        "valid_spans": valid_spans,
        "span_validity": valid_spans / total if total else 0.0,
    }


def evaluate(gold_paths: list[Path] | None = None, human_only: bool = False) -> dict[str, float | int]:
    paths = gold_paths or sorted(ANNOTATION_DIR.glob("*.csv"))
    gold, passages = load_gold(paths, human_only)
    predicted = load_predictions(passages)
    true_positive = len(gold & predicted)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {**archive_quality(), "passages": len(passages), "gold": len(gold), "predicted": len(predicted), "true_positive": true_positive,
            "false_positive": false_positive, "false_negative": false_negative,
            "precision": precision, "recall": recall, "f1": f1}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate EthnoLens extraction records.")
    parser.add_argument("--annotator", action="append", choices=("dafina", "ereza", "jeta"),
                        help="Evaluate selected annotation set(s); defaults to all CSV files")
    parser.add_argument("--human-only", action="store_true",
                        help="Leave out recipes annotated with AI assistance ([AI-assisted] in notes)")
    args = parser.parse_args()
    paths = [ANNOTATION_DIR / f"{name}.csv" for name in args.annotator] if args.annotator else None
    print(json.dumps(evaluate(paths, args.human_only), indent=2))


if __name__ == "__main__":
    main()
