
import streamlit as st
import pandas as pd
from crown_monitor.portfolio_tools import portfolio_board

st.title("💼 Portfolio")
st.caption("Position-level Crown state, live technical context and execution relevance")

bundle=st.session_state.get("crown_bundle")
if not bundle:
    st.warning("Upload Crown results in the sidebar.")
    st.stop()

with st.spinner("Loading portfolio and market data…"):
    board=portfolio_board(bundle)

if board.empty:
    st.error("No current portfolio snapshot found.")
    st.stop()

total=pd.to_numeric(board.get("Value"),errors="coerce").sum() if "Value" in board else 0
known_cost=pd.to_numeric(board.get("Total_Cost_EUR"),errors="coerce").sum() if "Total_Cost_EUR" in board else 0
a,b,c=st.columns(3)
a.metric("Positions",len(board))
b.metric("Snapshot invested value",f"€{total:,.0f}" if total else "N/A")
c.metric("Cash",f"€{pd.to_numeric(board['Cash_EUR'],errors='coerce').dropna().iloc[0]:,.0f}" if "Cash_EUR" in board and board["Cash_EUR"].notna().any() else "N/A")

for _,r in board.iterrows():
    ticker=str(r.get("Ticker",""))
    action=r.get("Review_Action") if pd.notna(r.get("Review_Action")) else r.get("Decision","HOLD")
    with st.expander(f"{ticker} · {action}"):
        a,b,c,d=st.columns(4)
        a.metric("Live price",f"{r.get('Live_price'):.2f}" if isinstance(r.get("Live_price"),(int,float)) else "N/A")
        pnl=r.get("Unrealized_Pct")
        b.metric("P&L vs known avg cost",f"{pnl:+.2f}%" if isinstance(pnl,(int,float)) else "N/A")
        c.metric("Technical",str(r.get("Display_Technical","UNKNOWN")))
        d.metric("Entry",str(r.get("Display_Entry","UNKNOWN")))
        st.write(f"**Support:** {r.get('Display_Support','N/A')} · **Resistance:** {r.get('Display_Resistance','N/A')}")
        if pd.notna(r.get("Reason")):
            st.write(f"**Crown reason:** {r.get('Reason')}")
        if pd.notna(r.get("Final_Status")):
            st.write(f"**Execution governance:** {r.get('Final_Status')}")
