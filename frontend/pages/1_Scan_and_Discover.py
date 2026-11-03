import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import api_url, disclaimer, load_records, render_plant, source_caption

st.title("Scan and Discover")
disclaimer()
st.write("Upload a PDF or image. The API returns records, and each historical name is highlighted in its passage.")

upload = st.file_uploader("Document", type=["pdf", "png", "jpg", "jpeg", "tif", "tiff", "txt"])
records, source = load_records()

if upload is not None and st.button("Send to API"):
    try:
        response = requests.post(
            f"{api_url()}/documents",
            files={"file": (upload.name, upload.getvalue(), upload.type or "application/octet-stream")},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        returned = payload["records"] if isinstance(payload, dict) else payload
        if isinstance(returned, list) and returned:
            st.success(f"{api_url()}/documents returned {len(returned)} records.")
            for record in returned:
                render_plant(record)
                st.divider()
        else:
            st.info("The API answered, but it returned no records.")
    except (requests.RequestException, ValueError, KeyError, TypeError):
        st.info("POST /documents is not available yet. The highlight below uses an illustrative record.")
        render_plant(records[0])
elif records:
    source_caption(source)
    st.markdown("**Highlight preview**")
    labels = {record["id"]: f"{record['id']} · {record['historical_name']}" for record in records}
    selected = st.selectbox("Record", list(labels), format_func=labels.get)
    render_plant(next(record for record in records if record["id"] == selected))
