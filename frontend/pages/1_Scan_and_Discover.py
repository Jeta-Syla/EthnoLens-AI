import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import api_url, disclaimer, page_heading, render_passage, render_plant

page_heading("Scan and discover", "A page goes in. The plant name comes back marked in its passage.")
disclaimer()

with st.container(border=True):
    upload = st.file_uploader("Document", type=["pdf", "png", "jpg", "jpeg", "tif", "tiff", "txt"])
    send = st.button("Send to API", type="primary", icon=":material/upload:")
if upload is None or not send:
    st.caption("Nothing is sent until you choose a file and press Send to API.")
    st.stop()

try:
    response = requests.post(
        f"{api_url()}/documents",
        files={"file": (upload.name, upload.getvalue(), upload.type or "application/octet-stream")},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
except requests.RequestException:
    st.info("POST /documents is not available. Start the API, then send the file again.")
    st.stop()
except ValueError:
    st.info("POST /documents answered, but the response was not JSON.")
    st.stop()

records = payload.get("records") if isinstance(payload, dict) else None
passages = payload.get("passages") if isinstance(payload, dict) else None
if isinstance(records, list) and records:
    st.success(f"{len(records)} records came back from {api_url()}/documents.")
    for record in records:
        render_plant(record)
        st.divider()
elif isinstance(passages, list) and passages:
    st.info("The file was stored. Extraction has not returned plant records yet, so there is nothing to highlight.")
    for passage in passages:
        st.markdown(f"**{passage.get('folio', 'page')}**")
        render_passage({"passage": passage.get("text") or "", "span": None})
else:
    st.info("The API answered, but it returned no records.")
