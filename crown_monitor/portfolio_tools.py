
from __future__ import annotations
import pandas as pd
from crown_monitor.market_tools import yahoo_symbol, load_history, technical_snapshot

def _bundle_df(bundle, key):
    x=bundle.get(key)
    return x.copy() if isinstance(x,pd.DataFrame) else pd.DataFrame()

def portfolio_board(bundle):
    p=_bundle_df(bundle,"portfolio_snapshot")
    if p.empty:
        return pd.DataFrame()

    review=_bundle_df(bundle,"portfolio_review")
    assess=_bundle_df(bundle,"watchlist_assessment")
    execg=_bundle_df(bundle,"execution_governance")

    p=p.copy()
    p["Ticker"]=p["Ticker"].astype(str)
    p["Yahoo_Symbol"]=p["Ticker"].map(yahoo_symbol)

    if not review.empty and "Ticker" in review:
        keep=[c for c in ["Ticker","Technical_State","Entry_State","Decision","Review_Action","Reason"] if c in review]
        p=p.merge(review[keep],on="Ticker",how="left")

    if not assess.empty and "Ticker" in assess:
        keep=[c for c in [
            "Ticker","Support_1","Support_2","Resistance_1","Resistance_2",
            "Technical_Score","Technical_Quality_Score","Entry_Timing_Score",
            "Market_Data_Status","Market_Data_Age_Business_Days"
        ] if c in assess]
        p=p.merge(assess[keep],on="Ticker",how="left",suffixes=("","_Assess"))

    # Add execution status where matching ETF
    if not execg.empty and "ETF" in execg:
        ex=execg.rename(columns={"ETF":"Ticker"})
        keep=[c for c in ["Ticker","Canonical_Execute_Now_EUR","Final_Status","Support","Resistance"] if c in ex]
        p=p.merge(ex[keep],on="Ticker",how="left")

    live_rows=[]
    for _,r in p.iterrows():
        sym=r["Yahoo_Symbol"]
        try:
            hist=load_history(sym,"1d","6mo")
            snap=technical_snapshot(hist)
        except Exception:
            snap={}
        live_rows.append(snap)

    live=pd.DataFrame(live_rows)
    if len(live):
        live=live.add_prefix("Live_")
        p=pd.concat([p.reset_index(drop=True),live.reset_index(drop=True)],axis=1)

    if "Average_Cost_EUR" in p and "Live_price" in p:
        p["Unrealized_Pct"]=(pd.to_numeric(p["Live_price"],errors="coerce")/
                             pd.to_numeric(p["Average_Cost_EUR"],errors="coerce")-1)*100

    # Fill Crown gaps with live technical diagnostics
    if "Technical_State" not in p:
        p["Technical_State"]=None
    p["Display_Technical"]=p["Technical_State"].where(
        p["Technical_State"].notna() & (p["Technical_State"].astype(str)!=""),
        p.get("Live_trend")
    )
    if "Entry_State" not in p:
        p["Entry_State"]=None
    p["Display_Entry"]=p["Entry_State"].where(
        p["Entry_State"].notna() & (p["Entry_State"].astype(str)!=""),
        p.get("Live_entry")
    )

    # Support/resistance: prefer Crown, then live
    def firstval(row, cols):
        for c in cols:
            if c in row.index:
                v=row[c]
                if pd.notna(v) and str(v).strip() not in ("","nan"):
                    return v
        return None
    p["Display_Support"]=[firstval(r,["Support_1","Support","Live_support"]) for _,r in p.iterrows()]
    p["Display_Resistance"]=[firstval(r,["Resistance_1","Resistance","Live_resistance"]) for _,r in p.iterrows()]
    return p

def isoe_action(board):
    if board is None or board.empty:
        return {}
    x=board[board["Ticker"].astype(str).str.upper()=="IS0E"]
    if x.empty:
        return {}
    r=x.iloc[0]
    return {
        "action": r.get("Review_Action") if pd.notna(r.get("Review_Action")) else "HOLD",
        "decision": r.get("Decision") if pd.notna(r.get("Decision")) else "HOLD",
        "price": r.get("Live_price"),
        "cost": r.get("Average_Cost_EUR"),
        "pnl_pct": r.get("Unrealized_Pct"),
        "trend": r.get("Display_Technical"),
        "entry": r.get("Display_Entry"),
        "support": r.get("Display_Support"),
        "resistance": r.get("Display_Resistance"),
        "rsi": r.get("Live_rsi"),
        "supertrend": r.get("Live_supertrend"),
    }
