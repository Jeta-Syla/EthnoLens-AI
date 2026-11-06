"""LLM extraction pipeline: passage -> JSON -> Pydantic -> SQLite."""

from __future__ import annotations

import hashlib
import json
import os
import argparse
import re
import time
from typing import Any

import requests
from dotenv import load_dotenv

from backend.app import db
from backend.app.models import Passage, Record
from pipeline.extraction_prompt import extraction_messages

load_dotenv(db.REPO_ROOT / ".env")


def _records_from_response(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]
    raise ValueError("LLM response must contain a records array")


def _call_llm(passage: Passage, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set; add it to the local .env file")
    provider = os.getenv("LLM_PROVIDER", "openai").casefold()
    if provider not in {"openai", "groq"}:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")
    default_base = ("https://api.groq.com/openai/v1/chat/completions" if provider == "groq"
                    else "https://api.openai.com/v1/chat/completions")
    default_model = "llama-3.3-70b-versatile" if provider == "groq" else "gpt-4o-mini"
    payload = {"model": os.getenv("LLM_MODEL", default_model),
               "messages": extraction_messages(passage.text, metadata),
               "temperature": 0,
               "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096"))}
    if provider == "openai":
        payload["response_format"] = {"type": "json_object"}
    url = os.getenv("LLM_BASE_URL", default_base)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = None
    for attempt in range(3):
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code != 429 or attempt == 2:
            break
        retry_after = response.headers.get("retry-after")
        time.sleep(float(retry_after) if retry_after else 10 * (attempt + 1))
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
    try:
        decoded = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            raise
        decoded = json.loads(match.group(0))
    return _records_from_response(decoded)


def _validate(raw_records: list[dict[str, Any]], passage: Passage, metadata: dict[str, Any]) -> list[Record]:
    result: list[Record] = []
    for raw in raw_records:
        data = {**raw, "id": "rec_0000", "passage": passage.text, **metadata}
        name = str(data.get("historical_name", "")).strip()
        if not name:
            continue
        start = passage.text.find(name)
        confidence = float(data.get("extraction_confidence", 0.0))
        evidence = dict(data.get("evidence") or {})
        if start < 0:
            span = None
            confidence *= 0.7
            evidence["plant"] = "inferred"
        else:
            span = (start, start + len(name))
            evidence["plant"] = "stated"
        data.update({"id": "rec_0000", "span": span,
                     "evidence": {"plant": evidence.get("plant", "stated"),
                                  "scientific_name": evidence.get("scientific_name", "inferred")},
                     "extraction_confidence": max(0.0, min(1.0, confidence)),
                     "mapping_confidence": None, "review_status": "pending"})
        result.append(Record.model_validate(data))
    return result


def _record_id(passage_id: str, name: str, index: int) -> str:
    digest = hashlib.sha1(f"{passage_id}|{name}|{index}".encode()).hexdigest()
    return f"rec_{int(digest[:12], 16) % 10000000000:010d}"


def extract_passage(passage: Passage) -> list[Record]:
    """Extract, validate and persist records for one stored passage."""
    metadata: dict[str, Any] = {"source": "Unknown", "folio": passage.folio,
                                "language": None, "region": None, "period": None}
    with db.connect() as conn:
        row = conn.execute("SELECT source, language, region, period FROM documents WHERE id = ?",
                           (passage.document_id,)).fetchone()
    if row:
        metadata.update(dict(row))
    raw_records = _call_llm(passage, metadata)
    try:
        records = _validate(raw_records, passage, metadata)
    except Exception:
        # A malformed model response gets one fresh JSON-mode attempt.
        records = _validate(_call_llm(passage, metadata), passage, metadata)
    rows = []
    for index, record in enumerate(records):
        item = record.model_dump()
        item["id"] = _record_id(passage.id, record.historical_name, index)
        rows.append({"id": item["id"], "passage_id": passage.id,
                     "historical_name": item["historical_name"], "normalised_name": item["normalised_name"],
                     "candidate_scientific_name": item["candidate_scientific_name"], "canonical_name": None,
                     "plant_part": item["plant_part"], "preparation": item["preparation"],
                     "described_use": item["described_use"],
                     "other_ingredients": json.dumps(item["other_ingredients"], ensure_ascii=False),
                     "span_start": item["span"][0] if item["span"] else None,
                     "span_end": item["span"][1] if item["span"] else None,
                     "evidence": json.dumps(item["evidence"], ensure_ascii=False),
                     "extraction_confidence": item["extraction_confidence"],
                     "mapping_confidence": item["mapping_confidence"], "review_status": item["review_status"]})
    with db.connect() as conn:
        db.upsert_records(conn, rows)
    return records


def extract_all(limit: int | None = None, skip_existing: bool = False) -> int:
    """Run extraction for every passage currently in the local database."""
    db.init_db()
    with db.connect() as conn:
        passages = [Passage(**dict(row)) for row in conn.execute(
            "SELECT id, document_id, folio, seq, text, method FROM passages ORDER BY id"
        ).fetchall()]
        if skip_existing:
            existing = {row[0] for row in conn.execute("SELECT DISTINCT passage_id FROM records")}
            passages = [passage for passage in passages if passage.id not in existing]
    if limit is not None:
        passages = passages[:limit]
    failed = []
    for number, passage in enumerate(passages, start=1):
        try:
            extract_passage(passage)
        except Exception as error:  # one bad response or network error must not stop the whole run
            failed.append(passage.id)
            print(f"{number}/{len(passages)} FAILED: {passage.id}: {error}")
            continue
        print(f"{number}/{len(passages)} extracted: {passage.id}")
    if failed:
        print(f"{len(failed)} passage(s) failed: {', '.join(failed)}")
    return len(passages) - len(failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract plant records from stored passages.")
    parser.add_argument("--limit", type=int, help="Only process the first N passages")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip passages that already have at least one stored record")
    args = parser.parse_args()
    extract_all(args.limit, args.skip_existing)
