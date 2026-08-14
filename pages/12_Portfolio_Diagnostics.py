
import streamlit as st

from crown_monitor.relationship_engine import get_preset, evaluate_relationship
from crown_monitor.universal_charts import comparison_chart

st.title("🧭 Portfolio Diagnostics")
st.caption("Select a holding and Crown automatically loads the relationships most relevant to its transmission mechanism.")

profiles={
    "IS0E":[
        "IS0E vs bullion — IS0E / GLD",
        "Miners vs bullion — GDX / GLD",
        "Real yield vs gold",
        "Gold vs equities — GLD / SPY",
        "Breakeven inflation vs Brent",
    ],
    "SEC0":[
        "Semiconductor leadership — SOXX / SPY",
        "Concentration — QQQ / RSP",
        "Breadth — RSP / SPY",
        "30Y - 2Y curve",
        "High Yield OAS vs SPY",
    ],
    "VWCE":[
        "Breadth — RSP / SPY",
        "Credit appetite — HYG / LQD",
        "30Y - 2Y curve",
        "High Yield OAS vs SPY",
        "Cyclicals vs defensives — XLY / XLP",
    ],
    "CBUX":[
        "30Y - 2Y curve",
        "Breakeven inflation vs Brent",
        "Cyclicals vs defensives — XLY / XLP",
        "High Yield OAS vs SPY",
    ],
    "QDVE":[
        "Concentration — QQQ / RSP",
        "Semiconductor leadership — SOXX / SPY",
        "30Y - 2Y curve",
        "Real yield vs gold",
    ],
    "XDWH":[
        "Cyclicals vs defensives — XLY / XLP",
        "Credit appetite — HYG / LQD",
        "Breadth — RSP / SPY",
    ],
}

ticker=st.selectbox("Holding / focus instrument",list(profiles),index=0)
st.info(f"Crown diagnostic profile: **{ticker}**")

for name in profiles[ticker]:
    p=get_preset(name)
    if not p:
        continue
    r=evaluate_relationship(p)
    with st.container(border=True):
        st.markdown(f"### {name}")
        st.caption(p["why"])
        if not r.get("ok"):
            st.warning(r.get("error","Data unavailable"))
            continue
        interp=r["interpretation"]
        a,b,c=st.columns(3)
        a.metric("Crown state",interp["state"])
        obs=r.get("alert_value_observed")
        b.metric("Alert metric",f"{obs:+.2f}" if isinstance(obs,(int,float)) else "N/A")
        c.metric("Threshold","TRIGGERED" if r["triggered"] else "NORMAL")
        st.plotly_chart(
            comparison_chart(r["transformed"],name,p["operation"]),
            width="stretch",config={"displaylogo":False}
        )
        st.write(interp["meaning"])
        st.caption(interp["caveat"])
