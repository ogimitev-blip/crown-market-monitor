
import streamlit as st
import pandas as pd
from crown_monitor.portfolio_tools import portfolio_board, isoe_action

st.title("📈 Trading Desk")
st.caption("Fast decision screen: position → technical state → Crown action → key levels")

bundle=st.session_state.get("crown_bundle")
if not bundle:
    st.warning("Upload the latest Crown results ZIP in the sidebar to populate the trading board.")
    st.stop()

with st.spinner("Building trading board…"):
    board=portfolio_board(bundle)

if board.empty:
    st.error("No portfolio snapshot was found in the Crown ZIP.")
    st.stop()

isoe=isoe_action(board)
if isoe:
    st.subheader("IS0E focus")
    a,b,c,d=st.columns(4)
    a.metric("Crown Action",str(isoe.get("action","HOLD")))
    price=isoe.get("price")
    a2=f"{price:.2f}" if isinstance(price,(int,float)) else "N/A"
    b.metric("Live Price",a2, f"{isoe.get('pnl_pct'):+.2f}%" if isinstance(isoe.get("pnl_pct"),(int,float)) else None)
    c.metric("Technical",str(isoe.get("trend","UNKNOWN")))
    d.metric("Entry State",str(isoe.get("entry","UNKNOWN")))
    st.write(
        f"**Support:** {isoe.get('support','N/A')}  ·  "
        f"**Resistance:** {isoe.get('resistance','N/A')}  ·  "
        f"**RSI:** {isoe.get('rsi','N/A')}  ·  "
        f"**SuperTrend:** {isoe.get('supertrend','N/A')}"
    )

st.subheader("Portfolio trading board")
cols=[
    "Ticker","Sleeve","Units","Average_Cost_EUR","Live_price","Unrealized_Pct",
    "Display_Technical","Display_Entry","Review_Action","Decision",
    "Display_Support","Display_Resistance"
]
cols=[c for c in cols if c in board.columns]
view=board[cols].copy()
view=view.rename(columns={
    "Live_price":"Price","Unrealized_Pct":"P&L %",
    "Display_Technical":"Technical","Display_Entry":"Entry",
    "Review_Action":"Action","Display_Support":"Support","Display_Resistance":"Resistance"
})
st.dataframe(view,hide_index=True,width="stretch",height=520)

st.caption("Crown states/actions are taken from the uploaded results. Missing technical fields are filled with live daily diagnostics rather than interpreted as neutral.")
