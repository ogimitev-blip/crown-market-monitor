import streamlit as st
st.set_page_config(page_title="Crown Market Monitor",page_icon="♛",layout="wide",initial_sidebar_state="collapsed")
pages={"Monitor":[
    st.Page("pages/1_Crown_Now.py",title="Crown Now",icon=":material/dashboard:"),
    st.Page("pages/2_Cross_Asset.py",title="Cross-Asset",icon=":material/show_chart:"),
    st.Page("pages/3_State_Explorer.py",title="State Explorer",icon=":material/search:")
]}
st.navigation(pages).run()
