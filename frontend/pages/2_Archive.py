import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import disclaimer, filter_records, load_records, options, page_heading, render_plant, source_caption

page_heading("Archive", "Search the records, then open one plant as a specimen sheet.")
disclaimer()
records, source = load_records()
source_caption(source)
if source != "api":
    st.stop()
if not records:
    st.info("The API is running, and it has no plant records yet.", title="Empty archive")
    st.stop()

with st.container(border=True):
    query = st.text_input("Search", placeholder="Historical name, local name, or scientific name")
    part, preparation, source_name, language = st.columns(4)
    part_choice = part.selectbox("Plant part", options(records, "plant_part"))
    preparation_choice = preparation.selectbox("Preparation", options(records, "preparation"))
    source_choice = source_name.selectbox("Source", options(records, "source"))
    language_choice = language.selectbox("Language", options(records, "language"))

filtered = filter_records(records, query, part_choice, preparation_choice, source_choice, language_choice)
st.caption(f"{len(filtered)} records")

if not filtered:
    st.info("Nothing in the archive matches this search or these filters.", title="No matches")
else:
    labels = {
        record["id"]: f"{record['historical_name']} — {record['source']} {record['folio']}"
        for record in filtered
    }
    selected = st.selectbox("Open a plant", list(labels), format_func=labels.get)
    render_plant(next(record for record in filtered if record["id"] == selected))
