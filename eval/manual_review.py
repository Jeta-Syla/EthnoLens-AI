"""Review a reproducible sample of records against their source passages."""

from __future__ import annotations

import argparse
import random

from backend.app import db


def review(count: int = 10, seed: int = 42) -> int:
    db.init_db()
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT r.id, r.historical_name, r.span_start, r.span_end, p.id AS passage_id, p.text
               FROM records r JOIN passages p ON p.id = r.passage_id
               ORDER BY r.id"""
        ).fetchall()
    sample = random.Random(seed).sample(rows, min(count, len(rows)))
    failures = 0
    for row in sample:
        span_ok = (row["span_start"] is not None and row["span_end"] is not None
                   and row["text"][row["span_start"]:row["span_end"]] == row["historical_name"])
        traceable = bool(row["passage_id"] and row["text"])
        status = "OK" if span_ok and traceable else "FAIL"
        if status == "FAIL":
            failures += 1
        print(f"{status} {row['id']}: {row['historical_name']!r} -> {row['passage_id']}")
    print(f"Reviewed {len(sample)} record(s); failures={failures}")
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review random records against their source passage.")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    raise SystemExit(1 if review(args.count, args.seed) else 0)
