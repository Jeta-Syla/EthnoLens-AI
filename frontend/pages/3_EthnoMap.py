import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REGION_POINTS, disclaimer, load_records, source_caption

st.title("EthnoMap")
disclaimer()
st.write("A point appears only where a record documents a region. Manuscripts with no region are listed, not pinned.")

records, source = load_records()
source_caption(source)

by_region: dict[str, list[dict]] = {}
without_region = []
for record in records:
    region = record.get("region")
    if region:
        by_region.setdefault(region, []).append(record)
    else:
        without_region.append(record)

try:
    import folium
    from streamlit_folium import st_folium
except ImportError:
    st.info("Install folium and streamlit-folium from requirements.txt to draw the map.")
else:
    chart = folium.Map(location=[42.2, 20.2], zoom_start=7)
    for region, group in by_region.items():
        point = REGION_POINTS.get(region)
        if point is None:
            continue
        names = ", ".join(sorted({record.get("local_name") or record.get("historical_name") for record in group}))
        sources = ", ".join(sorted({record.get("source") or "" for record in group}))
        folium.Marker(
            point,
            tooltip=region,
            popup=folium.Popup(
                f"<b>{region}</b><br>Local name: {names}<br>Source: {sources}"
                "<br>This marker is the documented region, not a village coordinate.",
                max_width=320,
            ),
        ).add_to(chart)
    st_folium(chart, height=480, use_container_width=True)

unplaced = [region for region in by_region if region not in REGION_POINTS]
if unplaced:
    st.write("Documented regions without a placed point: " + ", ".join(unplaced))
st.caption(f"{len(without_region)} records have no documented region, so they are not on the map.")
