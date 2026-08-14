
import streamlit as st
import pandas as pd
from crown_monitor.data import load_market,load_active_states
from crown_monitor.ui import state_card

st.title("♛ Crown Now")
st.caption("Live market monitor + uploaded Crown decision layer")

@st.fragment(run_every="60s")
def live_panel():
    market=load_market()
    live_states=load_active_states()
    crown=st.session_state.get("crown_status")

    st.caption(f"Market refresh: {market['last_update']}")

    if crown:
        freshness=crown.get("run_freshness","UNKNOWN")
        age=crown.get("run_age_hours")
        asof=crown.get("run_as_of") or "unknown"
        if freshness=="STALE":
            st.error(f"⚠ Crown run is STALE — as of {asof} ({age:.1f}h old). Live market data may have moved beyond the framework decision layer.")
        elif freshness=="AGING":
            st.warning(f"◷ Crown run is aging — as of {asof} ({age:.1f}h old).")
        elif freshness=="FRESH":
            st.success(f"✓ Crown run fresh — as of {asof} ({age:.1f}h old).")
        else:
            st.info("Crown run timestamp could not be determined.")

        a,b,c,d=st.columns(4)
        a.metric("Strategic Gate",str(crown.get("strategic_gate","UNAVAILABLE")))
        dep=crown.get("strategic_deployment","UNAVAILABLE")
        dep_text=f"{dep}%" if isinstance(dep,(int,float)) else str(dep)
        b.metric("Strategic Deployment",dep_text)
        c.metric("Tactical Multiplier",str(crown.get("tactical_multiplier","UNAVAILABLE")))
        d.metric("Event Phase",str(crown.get("dominant_event_phase","UNAVAILABLE")))
    else:
        a,b,c=st.columns(3)
        a.metric("Overall Risk",market["overall_risk"])
        b.metric("Rates",market["rates"])
        c.metric("Portfolio Action",market["portfolio_action"])

    st.subheader("Market strip")
    metrics=market["metrics"]
    for i in range(0,len(metrics),3):
        cols=st.columns(3)
        for j,m in enumerate(metrics[i:i+3]):
            cols[j].metric(m["name"],m["value"],m["delta"])
            fr=m.get("freshness","")
            stale=" ⚠ STALE" if fr=="STALE" else ""
            cols[j].caption(f"{m.get('frequency','')} · {m.get('source','')}{stale}")

    # Explicit live-data freshness summary
    stale_live=[m for m in metrics if m.get("freshness")=="STALE"]
    if stale_live:
        names=", ".join(m["name"] for m in stale_live)
        st.warning(f"Stale live-source inputs: {names}. These are latest available DAILY observations, not intraday readings.")

    if crown:
        st.subheader("Actual Crown decision layer")
        a,b=st.columns(2)
        a.write(f"**Strategic score:** {crown.get('strategic_score','UNAVAILABLE')}")
        a.write(f"**Source:** {crown.get('source','')}")
        b.write("**Live monitor:** market prices refresh independently of the uploaded Crown run.")
        b.write("**Treasuries:** FRED observations are daily, not intraday.")

        stale=crown.get("stale_inputs",[])
        unver=crown.get("unverified_inputs",[])
        if stale or unver:
            with st.expander("⚠ Crown input-quality flags", expanded=True):
                if stale:
                    st.write("**Stale Crown inputs:** " + ", ".join(map(str,stale)))
                if unver:
                    st.write("**Unverified / unavailable Crown inputs:** " + ", ".join(map(str,unver)))

        states=crown.get("active_states")
        if isinstance(states,pd.DataFrame) and len(states):
            st.subheader("Crown condition states")
            st.caption("Status now preserves Crown uncertainty/confirmation semantics instead of labeling every row OBSERVED.")
            st.dataframe(states,hide_index=True,width="stretch",height=500)
        else:
            st.info("No condition-state dictionary was found in the uploaded ZIP.")
    else:
        st.subheader("What Crown currently cares about")
        for x in market["changes"]:
            st.write("•",x)

        st.subheader("Live monitor states")
        if len(live_states):
            for _,row in live_states.iterrows():
                state_card(row)
        else:
            st.success("No MVP live-state trigger is active.")

live_panel()
