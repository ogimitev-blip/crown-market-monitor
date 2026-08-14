
import streamlit as st
from crown_monitor.crown_bundle import parse_crown_zip, extract_crown_status

st.set_page_config(
    page_title="Crown Trading Desk",
    page_icon="♛",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.header("Crown Trading Desk")
    uploaded=st.file_uploader(
        "Upload latest Crown results ZIP",
        type=["zip"],
        help="Latest Crown Framework results/output ZIP."
    )
    if uploaded is not None:
        try:
            bundle=parse_crown_zip(uploaded)
            status=extract_crown_status(bundle)
            st.session_state["crown_bundle"]=bundle
            st.session_state["crown_status"]=status
            st.success("Crown results loaded")
            st.caption(f"Recognized datasets: {len(bundle.get('found',{}))}")
            if bundle.get("errors"):
                st.warning("Some optional files could not be read.")
        except Exception as e:
            st.error(f"Could not read Crown ZIP: {e}")
    elif "crown_status" not in st.session_state:
        st.info("Live market tools work without Crown results. Upload the latest Crown ZIP for portfolio/action integration.")

pages={
    "Cockpit":[
        st.Page("pages/1_Crown_Now.py",title="Crown Now",icon=":material/dashboard:"),
        st.Page("pages/4_Trading_Desk.py",title="Trading Desk",icon=":material/candlestick_chart:"),
    ],
    "Analysis":[
        st.Page("pages/5_Instrument_Workbench.py",title="Instrument Workbench",icon=":material/query_stats:"),
        st.Page("pages/6_Cross_Asset_Lab.py",title="Cross-Asset Lab",icon=":material/compare_arrows:"),
        st.Page("pages/2_Cross_Asset.py",title="Cross-Asset Snapshot",icon=":material/show_chart:"),
    ],
    "Portfolio":[
        st.Page("pages/7_Portfolio.py",title="Portfolio",icon=":material/account_balance_wallet:"),
        st.Page("pages/3_State_Explorer.py",title="State Explorer",icon=":material/search:"),
    ]
}
pg=st.navigation(pages)
pg.run()
