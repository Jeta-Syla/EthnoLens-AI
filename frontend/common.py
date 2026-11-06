"""Shared helpers for the Streamlit pages.

Records come from the live API. When the backend is unavailable, pages receive
an empty list and show an explicit connection state instead of presenting demo
records as if they were extracted data.
"""

import html
import os
import re
from pathlib import Path

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent
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

# Same rule as pipeline/rag.py MEDICAL_RE, so a medical question is refused even when the API is down.
# When the API answers, its "refused" mode decides.
_REFUSAL_PATTERN = re.compile(
    r"\b(should|can|could|shall|may|do) i\b|\bis it safe|\brecommend|\bmy\b|\bi have\b"
    r"|\bdos(e|es|age|ing)\b|doz|how (much|many|often|long)|times (a|per) day"
    r"|\b(treat(ment)?|cure|heal)\s+(my|me|a|an|it|this|someone)\b|\btreatment\b"
    r"|sa herë|sa shumë|sa gjatë|trajt|kuro|shëro|mjeko|a duhet|si ta (marr|pi|përdor)|\bkam\b",
    re.IGNORECASE,
)

# One point per documented region. These are region labels, not village coordinates.
REGION_POINTS = {
    "Albanian Alps, Kosovo": (42.55, 20.10),
    "Kosovo": (42.55, 20.10),
    "Albania": (41.15, 20.17),
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
    """Return (records, source) where source is 'api' or 'unavailable'."""
    try:
        response = requests.get(f"{api_url()}/records", timeout=1.5)
        response.raise_for_status()
        payload = response.json()
        records = payload["records"] if isinstance(payload, dict) else payload
        if isinstance(records, list):
            return records, "api"
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    return [], "unavailable"


_SPRIG = """
<svg width="76" height="76" viewBox="0 0 76 76" fill="none" aria-hidden="true">
  <circle cx="38" cy="38" r="36" stroke="#e7c56a" stroke-width="1"/>
  <path d="M38 60c0 0-16-14-9-30 3.4-8 9-11 9-11s5.6 3 9 11c7 16-9 30-9 30z" stroke="#f6f0e4" stroke-width="1.5"/>
  <path d="M38 55V20" stroke="#e7c56a" stroke-width="1.2"/>
  <path d="M38 34c-7-2-10-8-10-8M38 42c7-2 10-7 10-7" stroke="#f6f0e4" stroke-width="1.15"/>
</svg>
"""


def apply_look() -> None:
    """Herbarium plate, paper, and the gold mark in a passage. Colors live in config.toml."""
    st.logo(str(ROOT / "mark.svg"), size="large", icon_image=str(ROOT / "mark-ink.svg"))
    st.html(
        """
        <style>
          .stApp {
            background-color: #f3ead7;
            background-image:
              radial-gradient(900px 420px at 0% -10%, rgba(255, 250, 241, 0.95), transparent 60%),
              radial-gradient(700px 380px at 100% 0%, rgba(231, 240, 228, 0.85), transparent 55%);
          }
          .el-plate {
            display: flex;
            gap: 1.15rem;
            align-items: center;
            background: linear-gradient(135deg, #163028 0%, #1c3329 55%, #27483b 100%);
            color: #f6f0e4;
            padding: 1.35rem 1.5rem;
            border-radius: 14px;
            margin: 0 0 1rem;
            box-shadow: 0 16px 40px rgba(22, 48, 40, 0.16);
          }
          .el-plate h1 {
            font-family: Fraunces, "Source Serif 4", Georgia, serif;
            font-weight: 560;
            font-size: 2.35rem;
            line-height: 1.05;
            letter-spacing: -0.03em;
            margin: 0;
            color: #f6f0e4;
          }
          .el-kicker {
            margin: 0 0 0.3rem;
            color: #e7c56a;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            font-size: 0.72rem;
          }
          .el-line {
            margin: 0.4rem 0 0;
            color: #d5e3d4;
            font-size: 1.02rem;
          }
          .el-passage {
            background: #fffaf1;
            border-left: 4px solid #e7c56a;
            border-radius: 0 10px 10px 0;
            padding: 0.95rem 1.05rem;
            color: #1f2a24;
            line-height: 1.7;
            box-shadow: inset 0 0 0 1px rgba(201, 184, 154, 0.45);
          }
          mark {
            background: #e7c56a;
            color: #1f2a24;
            padding: 0 0.15em;
            border-radius: 2px;
          }
        </style>
        """
    )


def page_heading(title: str, line: str, kicker: str = "EthnoLens AI") -> None:
    apply_look()
    st.html(
        "<header class='el-plate'>"
        + _SPRIG
        + "<div><p class='el-kicker'>"
        + html.escape(kicker)
        + "</p><h1>"
        + html.escape(title)
        + "</h1><p class='el-line'>"
        + html.escape(line)
        + "</p></div></header>"
    )


def disclaimer() -> None:
    apply_look()
    st.warning(DISCLAIMER)


def source_caption(source: str) -> None:
    if source == "api":
        st.caption(f"Records from {api_url()}/records")
    else:
        st.warning(f"Backend API is unavailable at {api_url()}. Start FastAPI to load archive records.")


def is_medical_question(question: str) -> bool:
    return _REFUSAL_PATTERN.search(question) is not None


def region_point(region: str | None):
    """Return a map point only when the region name documents Kosovo or Albania."""
    if not region:
        return None
    if region in REGION_POINTS:
        return REGION_POINTS[region]
    folded = region.casefold()
    if "kosovo" in folded:
        return REGION_POINTS["Kosovo"]
    if "albania" in folded or "shqip" in folded:
        return REGION_POINTS["Albania"]
    return None


def render_citations(citations, records: list[dict], key_prefix: str) -> None:
    """Show each citation as a control that opens its passage."""
    if not citations:
        return
    st.markdown("**Citations**")
    for index, citation in enumerate(citations):
        if isinstance(citation, str):
            source, folio, passage, url = citation, "", "", ""
        else:
            source = str(citation.get("source") or "source")
            folio = str(citation.get("folio") or "")
            passage = str(citation.get("passage") or "")
            url = str(citation.get("url") or "")
        label = ", ".join(part for part in (source, folio) if part)
        if url:
            st.link_button(label, url)
            continue
        open_key = f"open-{key_prefix}-{index}"
        if st.button(label, key=f"{key_prefix}-{index}"):
            st.session_state[open_key] = not st.session_state.get(open_key, False)
        if st.session_state.get(open_key):
            text = passage or _passage_for(records, source, folio)
            st.write(text or "This citation has no passage in the loaded records.")


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
    st.html(f"<div class='el-passage'>{highlight_html(passage, span)}</div>")
    if _valid_span(passage, span):
        st.caption(f"The gold mark, characters {span[0]}–{span[1]}, is the historical name as written.")
    else:
        st.caption("The historical name is not in this passage, so nothing is marked. The plant evidence is inferred.")


def render_plant(record: dict) -> None:
    """Plant page: mentions, original passage, confidence, and stated/inferred."""
    name = record.get("historical_name") or record.get("id")
    scientific = record.get("candidate_scientific_name") or "No candidate yet"
    evidence = record.get("evidence") or {}
    with st.container(border=True):
        st.subheader(name)
        st.markdown(f"*{scientific}*")
        st.caption("A candidate scientific name is not a confirmed identification.")
        local, extraction, mapping = st.columns(3)
        local.metric("Local name", record.get("local_name") or "—")
        extraction.metric("Extraction", _confidence(record.get("extraction_confidence")))
        mapping.metric("Mapping", record.get("mapping_confidence") or "none")
        st.write(
            f"Plant name in the text: **{evidence.get('plant', 'unknown')}**. "
            f"Scientific name: **{evidence.get('scientific_name', 'unknown')}**."
        )
    with st.container(border=True):
        rows = [
            ("Normalised name", record.get("normalised_name")),
            ("Plant part", record.get("plant_part")),
            ("Preparation", record.get("preparation")),
            ("Described use", record.get("described_use")),
            ("Other ingredients", ", ".join(record.get("other_ingredients") or []) or None),
            ("Source", record.get("source")),
            ("Folio", record.get("folio")),
            ("Language", record.get("language")),
            ("Region", record.get("region")),
            ("Period", record.get("period")),
            ("Review", record.get("review_status")),
        ]
        left_rows = rows[:6]
        right_rows = rows[6:]
        left, right = st.columns(2)
        for column, group in ((left, left_rows), (right, right_rows)):
            for label, value in group:
                column.markdown(f"**{label}**  \n{value if value else '—'}")
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


def _passage_for(records: list[dict], source: str, folio: str) -> str:
    for record in records:
        same_source = (record.get("source") or "") == source
        same_folio = not folio or (record.get("folio") or "") == folio
        if same_source and same_folio and record.get("passage"):
            return record["passage"]
    return ""


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
