
import streamlit as st
from crown_monitor.crown_bundle import parse_crown_zip, extract_crown_status

st.set_page_config(
    page_title="Crown Market Monitor",
    page_icon="♛",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.header("Crown integration")
    uploaded=st.file_uploader(
        "Upload latest Crown results ZIP",
        type=["zip"],
        help="Upload the result/output ZIP from your latest Crown run. The app reads it in memory; it is not committed to GitHub."
    )
    if uploaded is not None:
        try:
            bundle=parse_crown_zip(uploaded)
            status=extract_crown_status(bundle)
            st.session_state["crown_bundle"]=bundle
            st.session_state["crown_status"]=status
            st.success("Crown results loaded")
            st.caption(f"Files recognized: {len(bundle.get('found',{}))}")
            if bundle.get("errors"):
                st.warning("Some optional files could not be read.")
        except Exception as e:
            st.error(f"Could not read Crown ZIP: {e}")
    elif "crown_status" not in st.session_state:
        st.info("Live market monitor is active. Upload Crown results to add the actual Crown decision layer.")

pages={
    "Monitor":[
        st.Page("pages/1_Crown_Now.py",title="Crown Now",icon=":material/dashboard:"),
        st.Page("pages/2_Cross_Asset.py",title="Cross-Asset",icon=":material/show_chart:"),
        st.Page("pages/3_State_Explorer.py",title="State Explorer",icon=":material/search:"),
    ]
}
pg=st.navigation(pages)
pg.run()
