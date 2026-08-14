
import streamlit as st
import pandas as pd
from crown_monitor.market_tools import normalized_cross_asset, rolling_corr, load_history
from crown_monitor.charts import normalized_chart, corr_chart

st.title("🔗 Cross-Asset Lab")
st.caption("Compare the position with its causal transmission channels")

profiles={
    "IS0E / Gold Miners":{
        "symbols":["IS0E.DE","GC=F","GDX","DX-Y.NYB","^GSPC","^VIX"],
        "names":{
            "IS0E.DE":"IS0E","GC=F":"Gold","GDX":"GDX",
            "DX-Y.NYB":"DXY","^GSPC":"S&P 500","^VIX":"VIX"
        },
        "anchor":"IS0E.DE"
    },
    "AI / Semiconductors":{
        "symbols":["SEC0.DE","^SOX","^NDX","^GSPC","^VIX","DX-Y.NYB"],
        "names":{"SEC0.DE":"SEC0","^SOX":"SOX","^NDX":"Nasdaq 100","^GSPC":"S&P 500","^VIX":"VIX","DX-Y.NYB":"DXY"},
        "anchor":"SEC0.DE"
    },
    "Global Equity":{
        "symbols":["VWCE.DE","^GSPC","^NDX","DX-Y.NYB","^VIX","GC=F","BZ=F"],
        "names":{"VWCE.DE":"VWCE","^GSPC":"S&P 500","^NDX":"Nasdaq 100","DX-Y.NYB":"DXY","^VIX":"VIX","GC=F":"Gold","BZ=F":"Brent"},
        "anchor":"VWCE.DE"
    }
}

profile_name=st.selectbox("Crown profile",list(profiles),index=0)
horizon=st.selectbox("Comparison horizon",["1mo","3mo","6mo","1y"],index=2)
p=profiles[profile_name]

with st.spinner("Loading cross-asset history…"):
    px=normalized_cross_asset(tuple(p["symbols"]),horizon)

if px.empty:
    st.error("Cross-asset data unavailable.")
    st.stop()

st.plotly_chart(normalized_chart(px,p["names"]),width="stretch",config={"displaylogo":False})

st.subheader("Rolling 20-session correlation to position")
corr=rolling_corr(px,p["anchor"],20)
st.plotly_chart(corr_chart(corr,p["names"]),width="stretch",config={"displaylogo":False})

if profile_name=="IS0E / Gold Miners":
    st.subheader("IS0E transmission check")
    # latest normalized changes over horizon are descriptive; correlations are the key diagnostic
    end=px.iloc[-1]
    start=px.iloc[0]
    rows=[]
    for s in p["symbols"]:
        if s in px:
            rows.append({"Channel":p["names"].get(s,s),"Normalized level":round(float(end[s]),2)})
    st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
    st.info("Read the chain as: macro catalyst → real/nominal yields & USD → bullion → miners. A falling IS0E/GDX while gold is resilient is a miner-transmission warning, not automatically a bearish bullion signal.")

st.caption("Normalized charts compare direction and relative performance, not economic units. Treasury-yield transmission remains on Crown Now/Cross-Asset Snapshot via FRED.")
