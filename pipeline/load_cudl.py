"""Load Curious Cures recipes into SQLite.

Reads data/raw/cudl/<id>/ (written by pipeline.ingest), splits the recipe section into
individual recipes and stores one `passages` row per recipe, with its folio(s).

Recipes are split before a capitalised heading: "For ...", "To make ...", "A charm ...",
"Her is ...", and "Also ..." when it follows a full stop. Text before the first heading belongs
to the previous item (the poem on f. 1v) and is dropped. Pieces shorter than MIN_CHARS are
merged into the previous recipe. This is a heuristic: check a sample by hand before relying on it.

Passages are upserted (db.upsert_passages), so records already extracted from them are kept.

Usage (from the repo root):
  python -m pipeline.load_cudl MS-ADD-09308
  python -m pipeline.load_cudl MS-ADD-09308 --limit 50
"""

import argparse
import json
import re
from pathlib import Path

from backend.app import db

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "cudl"

# Page ranges (CUDL sequence numbers) of the recipe collection, from the item's logicalStructures.
RECIPE_PAGES = {"MS-ADD-09308": (16, 191)}

HEADING_RE = re.compile(r"(?:^|(?<=\s))(?=(?:For|Ffor|To make|A charm|Her is)\b)|(?<=\.\s)(?=Also\b)")
MIN_CHARS = 40


def load_pages(doc_id: str) -> list[dict]:
    first, last = RECIPE_PAGES[doc_id]
    with open(RAW_DIR / doc_id / "passages.jsonl", encoding="utf-8") as f:
        pages = [json.loads(line) for line in f]
    return [p for p in pages if first <= p["seq"] <= last]


def split_recipes(pages: list[dict]) -> list[dict]:
    """Join the pages into one text and cut it into recipes, keeping the folio(s) of each."""
    text, page_starts = "", []
    for page in pages:
        page_starts.append((len(text), page["folio"]))
        text += " ".join(page["text"].split()) + " "

    def folio_at(offset: int) -> str:
        return [folio for start, folio in page_starts if start <= offset][-1]

    cuts = [m.start() for m in HEADING_RE.finditer(text)]
    pieces = [(start, text[start:end].strip()) for start, end in zip(cuts, cuts[1:] + [len(text)])]

    recipes: list[dict] = []
    for start, piece in pieces:
        if recipes and len(piece) < MIN_CHARS:
            recipes[-1]["text"] += " " + piece
            recipes[-1]["end"] = start + len(piece)
        elif piece:
            recipes.append({"start": start, "end": start + len(piece), "text": piece})

    for recipe in recipes:
        first, last = folio_at(recipe["start"]), folio_at(recipe["end"] - 1)
        recipe["folio"] = first if first == last else f"{first}–{last}"
    return recipes


def load(doc_id: str, limit: int | None = None) -> int:
    document = json.loads((RAW_DIR / doc_id / "document.json").read_text(encoding="utf-8"))
    recipes = split_recipes(load_pages(doc_id))[:limit]

    db.init_db()
    with db.connect() as conn:
        db.upsert_document(conn, document)
        db.upsert_passages(conn, [
            {"id": f"{doc_id}:r{n:03d}", "document_id": doc_id, "folio": r["folio"], "seq": n,
             "text": r["text"], "method": "transcription"}
            for n, r in enumerate(recipes, start=1)
        ])
    print(f"{doc_id}: {len(recipes)} recipes loaded into {db.DB_PATH}")
    return len(recipes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load Curious Cures recipes into SQLite.")
    parser.add_argument("ids", nargs="+", help="CUDL manuscript ids, e.g. MS-ADD-09308")
    parser.add_argument("--limit", type=int, default=100, help="maximum recipes per manuscript (default 100)")
    args = parser.parse_args()
    for doc_id in args.ids:
        load(doc_id, args.limit)


if __name__ == "__main__":
    main()
