
from pathlib import Path
import json
import pandas as pd
from crown_monitor.live_data import live_snapshot

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def load_market():
    try:
        snap = live_snapshot()
        metrics = snap["metrics"]
        rates = snap["rates_df"]
        market = snap["market_df"]

        y30 = rates[rates["name"]=="US 30Y"]
        long_stress = bool(len(y30) and y30.iloc[0].get("value_raw") is not None and float(y30.iloc[0]["value_raw"]) >= 5.0)

        return {
            "last_update": snap["last_update"],
            "overall_risk": "ELEVATED" if long_stress else "NORMAL / MIXED",
            "macro": "LIVE MONITOR",
            "market": "MONITORING",
            "rates": "LONG_END_STRESS" if long_stress else "NORMAL",
            "liquidity": "NOT YET CONNECTED",
            "positioning": "NOT YET CONNECTED",
            "event_risk": "NOT YET CONNECTED",
            "portfolio_action": "NO AUTOMATIC ACTION",
            "metrics": metrics,
            "changes": [
                "Live market and FRED data connected.",
                "State logic is deliberately limited to high-confidence MVP rules.",
                "Full Crown state engine comes in the next integration step."
            ],
        }
    except Exception:
        return json.loads((DATA/"demo_market.json").read_text(encoding="utf-8"))

def load_active_states():
    try:
        snap = live_snapshot()
        if len(snap["states_df"]):
            return snap["states_df"]
    except Exception:
        pass
    return pd.DataFrame(json.loads((DATA/"demo_active_states.json").read_text(encoding="utf-8")))

def load_state_dictionary():
    return pd.read_csv(DATA/"state_dictionary.csv")

def load_cross_asset():
    try:
        snap = live_snapshot()
        r = snap["rates_df"].set_index("name")
        m = snap["market_df"].set_index("name")
        rows = []
        for name, expected, source_df in [
            ("US 2Y","↓",r),("US 10Y","↓",r),("US 30Y","↓",r),
            ("DXY","↓",m),("Gold","↑",m)
        ]:
            if name in source_df.index:
                obs = str(source_df.loc[name,"delta"])
                raw = source_df.loc[name,"delta_raw"]
                if pd.isna(raw):
                    verdict = "No data"
                elif expected=="↓":
                    verdict = "Confirmed" if float(raw)<0 else "Divergence"
                else:
                    verdict = "Confirmed" if float(raw)>0 else "Divergence"
                rows.append({"Asset":name,"Expected":expected,"Observed":obs,"Verdict":verdict})
        return pd.DataFrame(rows)
    except Exception:
        return pd.read_csv(DATA/"demo_cross_asset.csv")
