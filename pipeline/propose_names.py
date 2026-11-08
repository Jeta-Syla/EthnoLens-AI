"""Propose a candidate scientific name for each normalised plant name, then let GBIF check it.

The extraction prompt leaves candidate_scientific_name empty unless the passage itself writes a Latin name,
so records cannot be joined to GBIF or to the Albanian names. This step asks the LLM once for all distinct
normalised names (e.g. "sage" -> "Salvia officinalis"), with null for anything that is not a plant or is too
ambiguous. The proposal is only a candidate: evidence.scientific_name stays "inferred", and pipeline/taxonomy.py
decides the mapping confidence (high only for an exact species-level GBIF match).

Usage (from the repo root, needs LLM_API_KEY in .env):
  python -m pipeline.propose_names
"""

import json
import os
import time

import requests

from backend.app import db
from pipeline.extract import _decode_json_content  # also loads .env

PROMPT = """You map common English plant names, normalised from Middle English medical recipes (c. 1400), to the
plant most likely meant in medieval English herbal usage.
Return one JSON object {"names": {"<name>": "<Genus species>" or null}} with every given name as a key.
Rules:
- Give a binomial (genus and species, no author) only for a plant or a plant product named after its plant.
- Use null for anything that is not a plant (minerals, animals, fats, metals) and for names too vague or
  ambiguous to point to one species (for example "herb").
- No commentary."""


def _llm(names: list[str]) -> dict[str, str | None]:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set; add it to the local .env file")
    provider = os.getenv("LLM_PROVIDER", "openai").casefold()
    default_base = ("https://api.groq.com/openai/v1/chat/completions" if provider == "groq"
                    else "https://api.openai.com/v1/chat/completions")
    default_model = "llama-3.3-70b-versatile" if provider == "groq" else "gpt-4o-mini"
    model = os.getenv("LLM_MODEL", default_model)
    payload = {"model": model, "temperature": 0, "max_tokens": 2500,
               "messages": [{"role": "system", "content": PROMPT},
                            {"role": "user", "content": json.dumps(names, ensure_ascii=False)}]}
    if "gpt-oss" in model:
        payload["reasoning_effort"] = "low"  # a lookup, not a puzzle: keep the reasoning tokens for the answer
    for attempt in range(6):  # the free tier allows 8,000 tokens a minute: wait and retry on 429
        response = requests.post(
            os.getenv("LLM_BASE_URL", default_base),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        if response.status_code != 429:
            break
        time.sleep(min(float(response.headers.get("retry-after") or 15), 60))
    response.raise_for_status()
    decoded = _decode_json_content(response.json()["choices"][0]["message"]["content"])
    return {str(k).casefold(): v for k, v in (decoded.get("names") or {}).items()}


def propose(passage_ids: list[str] | None = None) -> int:
    """Fill candidate_scientific_name where it is empty (only for these passages, if given)."""
    only = ""
    params: list[str] = []
    if passage_ids is not None:
        if not passage_ids:
            return 0
        only = f" AND passage_id IN ({','.join('?' * len(passage_ids))})"
        params = list(passage_ids)
    with db.connect() as conn:
        names = [r[0] for r in conn.execute(
            "SELECT DISTINCT lower(normalised_name) FROM records WHERE candidate_scientific_name IS NULL "
            "AND normalised_name IS NOT NULL AND review_status != 'rejected'" + only + " ORDER BY 1", params)]
    if not names:
        return 0
    proposals: dict[str, str | None] = {}
    for start in range(0, len(names), 25):  # small batches, so the answer fits in max_tokens
        proposals.update(_llm(names[start:start + 25]))
    updated = 0
    with db.connect() as conn:
        for name in names:
            latin = proposals.get(name)
            if isinstance(latin, str) and len(latin.split()) >= 2:
                updated += conn.execute(
                    "UPDATE records SET candidate_scientific_name = ? WHERE lower(normalised_name) = ? "
                    "AND candidate_scientific_name IS NULL AND review_status != 'rejected'",
                    (" ".join(latin.split()[:2]), name)).rowcount
    return updated


if __name__ == "__main__":
    print(f"{propose()} record(s) given a candidate scientific name")
    from pipeline.rebuild import export_records
    from pipeline.taxonomy import map_records

    print(f"{map_records()} record(s) checked with GBIF")
    print(f"{export_records()} record(s) saved to the export")
