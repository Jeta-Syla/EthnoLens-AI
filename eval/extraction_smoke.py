"""Run the extraction prompt on the ten UI sample passages and validate the JSON.

Requires LLM_API_KEY in the local .env file. Results are printed only; nothing is
written to the database. The UI samples are smoke-test inputs, not gold labels.
Run from the repository root: python -m eval.extraction_smoke
"""

import json
import os
import re
import sys
import time
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
    provider = os.getenv("LLM_PROVIDER", "openai").casefold()
    if provider not in {"openai", "groq"}:
        raise SystemExit(f"Unsupported LLM_PROVIDER={provider!r}; use openai or groq.")
    endpoint = os.getenv(
        "LLM_BASE_URL",
        "https://api.groq.com/openai/v1/chat/completions"
        if provider == "groq" else "https://api.openai.com/v1/chat/completions",
    )
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-20b" if provider == "groq" else "gpt-4o-mini")
    samples = json.loads(SAMPLES.read_text(encoding="utf-8"))
    if len(samples) != 10:
        raise SystemExit(f"Expected 10 sample passages, found {len(samples)}.")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    passed = 0
    for index, sample in enumerate(samples, start=1):
        passage = sample["passage"]
        metadata = {key: sample.get(key) for key in ("source", "folio", "language", "region", "period")}
        payload = {"model": model, "messages": extraction_messages(passage, metadata),
                   "temperature": 0, "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096"))}
        if provider == "openai":
            payload["response_format"] = {"type": "json_object"}
        for attempt in range(3):
            response = session.post(endpoint, json=payload, timeout=90)
            if response.status_code != 429 or attempt == 2:
                break
            retry_after = response.headers.get("retry-after")
            time.sleep(float(retry_after) if retry_after else 10 * (attempt + 1))
        if response.status_code >= 400:
            detail = response.text[:500].replace("\n", " ")
            raise RuntimeError(f"{provider} request failed ({response.status_code}): {detail}")
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.I)
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
