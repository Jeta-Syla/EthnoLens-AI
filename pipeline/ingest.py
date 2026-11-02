"""Download Curious Cures transcriptions from the Cambridge Digital Library (CUDL).

For each manuscript id (e.g. MS-ADD-09308) this writes, under data/raw/cudl/<id>/:
  document.json   metadata in the shape of the `documents` table
  passages.jsonl  one line per transcribed page, in the shape of the `passages` table
  html/<seq>.html the raw transcription pages (cached, so re-runs skip them)

The transcription licence is not stated by CUDL, so everything stays in data/raw/ (not in Git).

Usage (from the repo root):
  python -m pipeline.ingest MS-ADD-09308
  python -m pipeline.ingest MS-ADD-09308 --limit 20
"""

import argparse
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "cudl"

ITEM_URL = "https://cudl.lib.cam.ac.uk/view/{id}.json"
VIEW_URL = "https://cudl.lib.cam.ac.uk/view/{id}/{seq}"
SERVICES_URL = "https://services.cudl.lib.cam.ac.uk"
HEADERS = {"User-Agent": "EthnoLens-AI/0.1 (student research prototype)"}
DELAY_SECONDS = 1.0


class _TranscriptionText(HTMLParser):
    """Collects the text inside <div class="body">, one manuscript line per output line."""

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.depth = 0  # div nesting depth inside the body div; 0 = outside

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if self.depth:
                self.depth += 1
            elif dict(attrs).get("class") == "body":
                self.depth = 1
        elif self.depth and tag == "br":
            self.parts.append("\n")
        elif self.depth and tag == "p":
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag == "div" and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)


def extract_text(html: str) -> str:
    parser = _TranscriptionText()
    parser.feed(html)
    text = "".join(parser.parts)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _first(parts: list[dict], key: str):
    return next((p[key] for p in parts if key in p), None)


def document_metadata(doc_id: str, item: dict) -> dict:
    parts = item["descriptiveMetadata"]
    top = parts[0]
    languages = _first(parts, "languageStrings")
    creations = _first(parts, "creations")
    creation = creations["value"][0] if creations else {}
    places = creation.get("places", {}).get("value", [])
    return {
        "id": doc_id,
        "source": top["shelfLocator"]["displayForm"].removeprefix("Cambridge, University Library, "),
        "collection": "curious_cures",
        "title": top["title"]["displayForm"],
        "url": f"https://cudl.lib.cam.ac.uk/view/{doc_id}",
        "language": languages["value"][0]["displayForm"] if languages else None,
        "period": creation.get("dateDisplay", {}).get("displayForm"),
        "region": places[0]["displayForm"].rstrip(".") if places else None,
        "licence": "Transcription licence not stated; images CC BY-NC 3.0 (Cambridge University Library)",
    }


def ingest(doc_id: str, limit: int | None = None) -> None:
    out_dir = RAW_DIR / doc_id
    html_dir = out_dir / "html"
    html_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    item = session.get(ITEM_URL.format(id=doc_id), timeout=30).json()
    document = document_metadata(doc_id, item)
    (out_dir / "document.json").write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")

    pages = [p for p in item["pages"] if p.get("transcriptionDiplomaticURL")]
    if limit:
        pages = pages[:limit]
    print(f"{doc_id}: {len(pages)} transcribed pages")

    written = 0
    with open(out_dir / "passages.jsonl", "w", encoding="utf-8") as out:
        for page in pages:
            seq = page["sequence"]
            cached = html_dir / f"{seq}.html"
            if cached.exists():
                html = cached.read_text(encoding="utf-8")
            else:
                resp = session.get(SERVICES_URL + page["transcriptionDiplomaticURL"], timeout=30)
                resp.raise_for_status()
                resp.encoding = "utf-8"
                html = resp.text
                cached.write_text(html, encoding="utf-8")
                time.sleep(DELAY_SECONDS)

            text = extract_text(html)
            if not text:
                continue
            passage = {
                "id": f"{doc_id}:{seq}",
                "document_id": doc_id,
                "folio": page["label"],
                "seq": seq,
                "text": text,
                "method": "transcription",
                "url": VIEW_URL.format(id=doc_id, seq=seq),
            }
            out.write(json.dumps(passage, ensure_ascii=False) + "\n")
            written += 1

    print(f"{doc_id}: {written} passages -> {out_dir / 'passages.jsonl'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Curious Cures transcriptions from CUDL.")
    parser.add_argument("ids", nargs="+", help="CUDL manuscript ids, e.g. MS-ADD-09308")
    parser.add_argument("--limit", type=int, help="only the first N transcribed pages per manuscript")
    args = parser.parse_args()
    for doc_id in args.ids:
        ingest(doc_id, args.limit)


if __name__ == "__main__":
    main()
