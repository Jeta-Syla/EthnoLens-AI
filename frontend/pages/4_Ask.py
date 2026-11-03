import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import NO_DATA, REFUSAL, api_url, disclaimer, is_medical_question

st.title("Ask EthnoLens")
disclaimer()
st.write("Answers come only from archived passages. Each answer cites its source and folio. A question with no source is declined.")

if "ask_messages" not in st.session_state:
    st.session_state.ask_messages = []

for message in st.session_state.ask_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about a plant in the archive")
if not question:
    st.stop()

st.session_state.ask_messages.append({"role": "user", "content": question})
with st.chat_message("user"):
    st.markdown(question)

if is_medical_question(question):
    answer = REFUSAL
else:
    answer = NO_DATA
    try:
        response = requests.post(f"{api_url()}/ask", json={"question": question}, timeout=8)
        response.raise_for_status()
        payload = response.json()
        text = payload.get("answer") if isinstance(payload, dict) else None
        citations = payload.get("citations") if isinstance(payload, dict) else None
        if text and citations:
            lines = [text, "", "**Citations**"]
            for citation in citations:
                if isinstance(citation, dict):
                    lines.append(f"- {citation.get('source', 'source')}, {citation.get('folio', 'folio')}")
                else:
                    lines.append(f"- {citation}")
            answer = "\n".join(lines)
        elif text:
            answer = NO_DATA
    except (requests.RequestException, ValueError, AttributeError):
        answer = NO_DATA

st.session_state.ask_messages.append({"role": "assistant", "content": answer})
with st.chat_message("assistant"):
    st.markdown(answer)
