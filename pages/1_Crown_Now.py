
import streamlit as st
from crown_monitor.data import load_market, load_active_states
from crown_monitor.ui import state_card

st.title("♛ Crown Now")
st.caption("Live market monitor · market data ~60s cache · FRED rates ~15m cache")

@st.fragment(run_every="60s")
def live_panel():
    market = load_market()
    states = load_active_states()

    st.caption(f"Last update: {market['last_update']}")

    a,b,c = st.columns(3)
    a.metric("Overall Risk", market["overall_risk"])
    b.metric("Rates", market["rates"])
    c.metric("Portfolio Action", market["portfolio_action"])

    st.subheader("Market strip")
    metrics = market["metrics"]
    for i in range(0, len(metrics), 3):
        cols = st.columns(3)
        for j, m in enumerate(metrics[i:i+3]):
            cols[j].metric(m["name"], m["value"], m["delta"])

    st.subheader("What Crown currently cares about")
    for x in market["changes"]:
        st.write("•", x)

    st.subheader("Live Crown states")
    if len(states):
        for _, row in states.iterrows():
            state_card(row)
    else:
        st.success("No MVP live-state trigger is active.")

live_panel()
