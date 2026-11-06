"""Run the extraction prompt on the ten UI sample passages and validate the JSON.

Requires LLM_API_KEY in the local .env file. Results are printed only; nothing is
written to the database. The UI samples are smoke-test inputs, not gold labels.
Run from the repository root: python -m eval.extraction_smoke
"""

import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from backend.app.models import Record
from pipeline.extraction_prompt import extraction_messages

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "frontend" / "mock.json"


def main() -> None:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise SystemExit("Set LLM_API_KEY in your local .env, then run this command again.")
    if os.getenv("LLM_PROVIDER", "openai").casefold() != "openai":
        raise SystemExit("This smoke runner currently supports LLM_PROVIDER=openai.")

    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    samples = json.loads(SAMPLES.read_text(encoding="utf-8"))
    if len(samples) != 10:
        raise SystemExit(f"Expected 10 sample passages, found {len(samples)}.")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    passed = 0
    for index, sample in enumerate(samples, start=1):
        passage = sample["passage"]
        metadata = {key: sample.get(key) for key in ("source", "folio", "language", "region", "period")}
        response = session.post(
            "https://api.openai.com/v1/chat/completions",
            json={"model": model, "messages": extraction_messages(passage, metadata),
                  "response_format": {"type": "json_object"}, "temperature": 0},
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        # JSON mode accepts an object root; the prompt requires a record array.
        decoded = json.loads(content)
        records = decoded if isinstance(decoded, list) else decoded.get("records")
        if not isinstance(records, list):
            raise ValueError(f"Sample {index}: expected a JSON array (or {{\"records\": [...]}}).")
        for record_data in records:
            Record.model_validate(record_data)
            if record_data["passage"] != passage:
                raise ValueError(f"Sample {index}: model changed the source passage.")
            name = record_data["historical_name"]
            span = record_data["span"]
            if span is not None:
                start, end = span
                if not (0 <= start < end <= len(passage) and passage[start:end] == name):
                    raise ValueError(f"Sample {index}: span does not match historical_name {name!r}.")
            elif re.search(re.escape(name), passage, re.IGNORECASE):
                raise ValueError(f"Sample {index}: exact plant name exists but span is null: {name!r}.")
        passed += 1
        print(f"{index}/10 OK: {len(records)} record(s)")
    print(f"PASS: {passed}/10 prompts returned schema-valid records. Review output quality manually before tuning.")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"LLM request failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
