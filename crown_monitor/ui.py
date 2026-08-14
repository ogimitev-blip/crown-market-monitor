import streamlit as st
STATUS_ICON={"ACTIVE":"🔴","WATCH":"🟠","NOT_CONFIRMED":"🟡","CLEARED":"🟢"}
def state_card(row):
    icon=STATUS_ICON.get(str(row.get("Status","")).upper(),"⚪")
    with st.container(border=True):
        st.markdown(f"### {icon} {row.get('State','')}")
        st.caption(f"{row.get('Status','')} · confidence {row.get('Confidence','')}%")
        st.write(row.get("Evidence",""))
        st.markdown(f"**Portfolio:** {row.get('Portfolio_Implication','')}")
