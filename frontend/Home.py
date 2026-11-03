"""EthnoLens AI frontend.

Run from the repository root:

    streamlit run frontend/Home.py
"""

import streamlit as st

from common import DISCLAIMER

st.set_page_config(page_title="EthnoLens AI", layout="wide")
st.title("EthnoLens AI")
st.warning(DISCLAIMER)
st.write(
    "Historical botanical documents become a searchable archive. "
    "Every shown fact stays tied to its source passage."
)

st.subheader("Pages")
st.markdown(
    """
- **Scan and Discover** — upload a document and see the returned records highlighted in the passage.
- **Archive** — search, filter, and open a plant page.
- **EthnoMap** — documented regions only, with the local name and the source.
- **Ask** — questions answered only from the archive, with a citation, or refused.
"""
)
st.caption("Open a page from the sidebar. Until the API serves records, the pages read frontend/mock.json.")
st.caption(DISCLAIMER)
