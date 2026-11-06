import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import api_url, disclaimer, load_records, page_heading, region_point, source_caption

page_heading("EthnoMap", "One point for a documented region. The Albanian name and the source sit in the popup.")
disclaimer()

records, source = load_records()
source_caption(source)
if source != "api":
    st.stop()
try:
    with st.spinner("Loading the map…"):
        response = requests.get(f"{api_url()}/map", timeout=1.5)
        response.raise_for_status()
        payload = response.json()
    mapped = payload if isinstance(payload, list) else payload.get("records", records)
    if isinstance(mapped, list):
        records = mapped
        st.caption(f"Points from {api_url()}/map")
except (requests.RequestException, ValueError, AttributeError):
    st.info("GET /map did not answer. The points below come from the archive records.", title="Map endpoint quiet")

by_region: dict[str, list[dict]] = {}
without_region = []
for record in records:
    region = record.get("region")
    if region and region_point(region) is not None:
        by_region.setdefault(region, []).append(record)
    else:
        without_region.append(record)

try:
    import folium
    from streamlit_folium import st_folium
except ImportError:
    st.info("Install folium and streamlit-folium from requirements.txt to draw the map.")
else:
    chart = folium.Map(location=[41.9, 20.2], zoom_start=7, tiles="OpenStreetMap")
    for region, group in by_region.items():
        names = ", ".join(sorted({record.get("local_name") or record.get("historical_name") or "" for record in group}))
        sources = ", ".join(sorted({record.get("source") or "" for record in group}))
        folium.CircleMarker(
            region_point(region),
            radius=11,
            color="#1a5c45",
            weight=2,
            fill=True,
            fill_color="#e7c56a",
            fill_opacity=0.95,
            tooltip=region,
            popup=folium.Popup(
                f"<b>{region}</b><br>Albanian name: {names}<br>Source: {sources}"
                "<br>This marker is the documented region, not a village coordinate.",
                max_width=320,
            ),
        ).add_to(chart)
    st_folium(chart, height=480, use_container_width=True)

if not by_region:
    st.info(
        "No loaded record documents a region in Kosovo or Albania, so the map has no points.",
        title="No documented region",
    )
st.caption(f"{len(without_region)} records have no Kosovo or Albania region, so they are not on the map.")
