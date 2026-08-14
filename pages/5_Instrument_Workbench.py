
import streamlit as st
import pandas as pd
from crown_monitor.market_tools import instrument_registry, yahoo_symbol, load_history, interval_period, technical_snapshot
from crown_monitor.charts import instrument_chart
from crown_monitor.portfolio_tools import portfolio_board

st.title("🔎 Instrument Workbench")
st.caption("Interactive technical chart + Crown portfolio context")

reg=instrument_registry()
default_idx=0
options=reg["Ticker"].tolist()
if "IS0E" in options:
    default_idx=options.index("IS0E")

c1,c2,c3=st.columns([1,1,2])
ticker=c1.selectbox("Instrument",options,index=default_idx)
interval=c2.selectbox("Timeframe",["15m","1h","1D"],index=2)
overlays=c3.multiselect(
    "Overlays",
    ["SMA 20","SMA 50","SMA 100","SMA 200","VWAP 20","SuperTrend","Ichimoku"],
    default=["SMA 20","SMA 50","SMA 200","SuperTrend"]
)

sym=yahoo_symbol(ticker)
period,yint=interval_period(interval)
with st.spinner(f"Loading {ticker}…"):
    df=load_history(sym,yint,period)

if df.empty:
    st.error(f"No market data returned for {sym}.")
    st.stop()

snap=technical_snapshot(df)
levels={}
bundle=st.session_state.get("crown_bundle")
if bundle:
    try:
        board=portfolio_board(bundle)
        row=board[board["Ticker"].astype(str).str.upper()==ticker.upper()]
        if len(row):
            r=row.iloc[0]
            for label,col in [("Crown support","Display_Support"),("Crown resistance","Display_Resistance"),("Average cost","Average_Cost_EUR")]:
                v=r.get(col)
                if isinstance(v,(int,float)) and pd.notna(v):
                    levels[label]=float(v)
    except Exception:
        pass

a,b,c,d,e=st.columns(5)
a.metric("Price",f"{snap.get('price',0):.2f}")
b.metric("Trend",str(snap.get("trend","UNKNOWN")))
c.metric("Entry",str(snap.get("entry","UNKNOWN")))
rsi=snap.get("rsi")
d.metric("RSI 14",f"{rsi:.1f}" if isinstance(rsi,(int,float)) else "N/A")
e.metric("SuperTrend",str(snap.get("supertrend","UNKNOWN")))

st.plotly_chart(instrument_chart(df,ticker,overlays,levels),width="stretch",config={"displaylogo":False})

st.subheader("Live technical map")
a,b,c,d=st.columns(4)
a.write(f"**Support:** {snap.get('support','N/A')}")
b.write(f"**Resistance:** {snap.get('resistance','N/A')}")
c.write(f"**SMA20 / SMA50:** {snap.get('sma20','N/A')} / {snap.get('sma50','N/A')}")
d.write(f"**ATR14:** {snap.get('atr','N/A')}")
st.caption(f"Market symbol: {sym}. Intraday data are indicative/delayed depending on Yahoo availability.")
