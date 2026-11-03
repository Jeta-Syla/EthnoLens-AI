"""Shared helpers for the Streamlit pages.

Records come from GET /records when that endpoint answers, and otherwise from
frontend/mock.json. The mock file is illustrative. It is not an extraction.
"""

import html
import json
import os
import re
from pathlib import Path

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent
MOCK_PATH = ROOT / "mock.json"
REPO_ROOT = ROOT.parent

DISCLAIMER = (
    "EthnoLens does not provide medical advice, dosages, or treatment recommendations. "
    "Described uses are historical records, not instructions."
)
REFUSAL = (
    "EthnoLens nuk jep këshilla mjekësore, doza ose trajtime. "
    "Përdorimet në arkivë janë përshkrime historike, jo udhëzime."
)
NO_DATA = "Nuk ka të dhëna në arkivë."

_REFUSAL_PATTERN = re.compile(
    r"doz|sa herë|trajtim|a duhet ta marr|dosage|treatment|should i take|how many times",
    re.IGNORECASE,
)

# One point per documented region. These are region labels, not village coordinates.
REGION_POINTS = {
    "Albanian Alps, Kosovo": (42.55, 20.10),
}


def api_url() -> str:
    configured = os.environ.get("API_URL")
    if configured:
        return configured.rstrip("/")
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("API_URL="):
                value = line.split("=", 1)[1].strip()
                if value:
                    return value.rstrip("/")
    return "http://localhost:8000"


def load_records() -> tuple[list[dict], str]:
    """Return (records, source) where source is 'api' or 'mock'."""
    try:
        response = requests.get(f"{api_url()}/records", timeout=1.5)
        response.raise_for_status()
        payload = response.json()
        records = payload["records"] if isinstance(payload, dict) else payload
        if isinstance(records, list):
            return records, "api"
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    records = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
    return records, "mock"


def disclaimer() -> None:
    st.warning(DISCLAIMER)


def source_caption(source: str) -> None:
    if source == "api":
        st.caption(f"Records from {api_url()}/records")
    else:
        st.caption("GET /records is not available yet. These 10 records are illustrative mock data, not extractions.")


def is_medical_question(question: str) -> bool:
    return _REFUSAL_PATTERN.search(question) is not None


def highlight_html(passage: str, span) -> str:
    """Split the passage at span and wrap the middle part in <mark>."""
    if not _valid_span(passage, span):
        return html.escape(passage)
    start, end = span
    return (
        html.escape(passage[:start])
        + "<mark>"
        + html.escape(passage[start:end])
        + "</mark>"
        + html.escape(passage[end:])
    )


def render_passage(record: dict) -> None:
    passage = record.get("passage") or ""
    span = record.get("span")
    st.markdown(highlight_html(passage, span), unsafe_allow_html=True)
    if _valid_span(passage, span):
        st.caption(f"Highlighted span {span[0]}:{span[1]} is the historical name as written.")
    else:
        st.caption("The historical name is not in this passage, so nothing is highlighted. The plant evidence is inferred.")


def render_plant(record: dict) -> None:
    """Plant page: mentions, original passage, confidence, and stated/inferred."""
    st.subheader(record.get("historical_name") or record.get("id"))
    scientific = record.get("candidate_scientific_name") or "No candidate yet"
    st.markdown(f"**Candidate scientific name:** {scientific}")
    st.caption("A candidate is not a confirmed identification.")

    left, right = st.columns(2)
    left.metric("Extraction confidence", _confidence(record.get("extraction_confidence")))
    right.metric("Mapping confidence", record.get("mapping_confidence") or "none")

    evidence = record.get("evidence") or {}
    st.write(
        f"Plant name: **{evidence.get('plant', 'unknown')}**. "
        f"Scientific name: **{evidence.get('scientific_name', 'unknown')}**."
    )
    rows = [
        ("Normalised name", record.get("normalised_name")),
        ("Local name", record.get("local_name")),
        ("Plant part", record.get("plant_part")),
        ("Preparation", record.get("preparation")),
        ("Described use", record.get("described_use")),
        ("Other ingredients", ", ".join(record.get("other_ingredients") or []) or None),
        ("Source", record.get("source")),
        ("Folio", record.get("folio")),
        ("Language", record.get("language")),
        ("Region", record.get("region")),
        ("Period", record.get("period")),
        ("Review status", record.get("review_status")),
    ]
    for label, value in rows:
        st.write(f"**{label}:** {value if value else '—'}")

    st.markdown("**Original passage**")
    render_passage(record)


def filter_records(records: list[dict], query: str, part: str, preparation: str, source: str, language: str) -> list[dict]:
    query = query.strip().casefold()
    chosen = []
    for record in records:
        if part != "All" and (record.get("plant_part") or "") != part:
            continue
        if preparation != "All" and (record.get("preparation") or "") != preparation:
            continue
        if source != "All" and (record.get("source") or "") != source:
            continue
        if language != "All" and (record.get("language") or "") != language:
            continue
        if query and query not in _search_text(record):
            continue
        chosen.append(record)
    return chosen


def options(records: list[dict], key: str) -> list[str]:
    values = sorted({record.get(key) for record in records if record.get(key)})
    return ["All", *values]


def _search_text(record: dict) -> str:
    parts = [
        record.get("historical_name"),
        record.get("normalised_name"),
        record.get("local_name"),
        record.get("candidate_scientific_name"),
        record.get("passage"),
        record.get("source"),
    ]
    return " ".join(part for part in parts if part).casefold()


def _confidence(value) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "—"


def _valid_span(passage: str, span) -> bool:
    if not isinstance(span, (list, tuple)) or len(span) != 2:
        return False
    start, end = span
    return isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(passage)
