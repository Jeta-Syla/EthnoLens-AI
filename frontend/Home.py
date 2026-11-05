"""EthnoLens AI frontend.

Run from the repository root:

    streamlit run frontend/Home.py
"""

import streamlit as st

from common import DISCLAIMER, page_heading

st.set_page_config(page_title="EthnoLens AI", page_icon=":material/local_florist:", layout="wide")
page_heading(
    "EthnoLens AI",
    "Historical plant knowledge, kept beside the passage it came from.",
    kicker="A herbarium for the archive",
)
st.warning(DISCLAIMER)

st.subheader("Choose a way through the archive")
scan, archive, mapped, ask = st.columns(4, vertical_alignment="top")
with scan.container(border=True, height="stretch"):
    st.markdown(":material/document_scanner: **Scan and discover**")
    st.write("Upload a page. The plant name is marked in gold inside the passage.")
    st.page_link("pages/1_Scan_and_Discover.py", label="Open scan", icon=":material/arrow_forward:")
with archive.container(border=True, height="stretch"):
    st.markdown(":material/menu_book: **Archive**")
    st.write("Search by name, part, preparation, source, or language.")
    st.page_link("pages/2_Archive.py", label="Open archive", icon=":material/arrow_forward:")
with mapped.container(border=True, height="stretch"):
    st.markdown(":material/map: **EthnoMap**")
    st.write("A point only where a region in Kosovo or Albania is documented.")
    st.page_link("pages/3_EthnoMap.py", label="Open map", icon=":material/arrow_forward:")
with ask.container(border=True, height="stretch"):
    st.markdown(":material/forum: **Ask**")
    st.write("An answer appears only when a passage can be opened beside it.")
    st.page_link("pages/4_Ask.py", label="Open ask", icon=":material/arrow_forward:")
