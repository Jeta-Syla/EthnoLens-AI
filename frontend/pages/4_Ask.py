import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import NO_DATA, REFUSAL, api_url, disclaimer, is_medical_question, load_records, page_heading, render_citations

page_heading("Ask", "A question is answered only from a passage you can open. Without a source, it is declined.")
disclaimer()

records, _source = load_records()
if "ask_messages" not in st.session_state:
    st.session_state.ask_messages = []

for index, message in enumerate(st.session_state.ask_messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_citations(message.get("citations") or [], records, f"cite-{index}")

question = st.chat_input("Ask about a plant in the archive")
if not st.session_state.ask_messages:
    st.info(
        "Ask about a plant that might be in the archive. A dose or a treatment is refused. "
        "If no passage supports the answer, EthnoLens says the archive has no data.",
        title="No question yet",
    )
if not question:
    st.stop()

st.session_state.ask_messages.append({"role": "user", "content": question})
with st.chat_message("user"):
    st.markdown(question)

citations = []
if is_medical_question(question):
    answer = REFUSAL
else:
    answer = NO_DATA
    try:
        with st.spinner("Looking in the archive…"):
            response = requests.post(f"{api_url()}/ask", json={"question": question}, timeout=8)
            response.raise_for_status()
            payload = response.json()
        text = payload.get("answer") if isinstance(payload, dict) else None
        found = payload.get("citations") if isinstance(payload, dict) else None
        if payload.get("mode") == "refused":  # the server's rule is the authority, not the local pattern
            answer = REFUSAL
        elif text and found:
            answer = text
            citations = found
    except (requests.RequestException, ValueError, AttributeError):
        answer = NO_DATA

st.session_state.ask_messages.append({"role": "assistant", "content": answer, "citations": citations})
with st.chat_message("assistant"):
    st.markdown(answer)
    render_citations(citations, records, f"cite-{len(st.session_state.ask_messages) - 1}")
