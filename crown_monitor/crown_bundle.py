
from __future__ import annotations
from io import BytesIO, StringIO
import json, zipfile
import pandas as pd

PREFERRED_FILES = {
    "research_registry": [
        "crown_research_signal_registry_latest.csv",
        "canonical_signal_registry_latest.csv",
    ],
    "strategic_gate": ["strategic_gate_latest.csv"],
    "tactical_gate": ["tactical_event_gate_latest.csv"],
    "capital_layer": ["capital_layer_state_latest.csv"],
    "event_summary": ["event_aware_summary_latest.json"],
    "allocation": [
        "allocation_latest.csv","master_allocation_latest.csv",
        "portfolio_allocation_latest.csv"
    ],
    "portfolio": [
        "current_portfolio_latest.csv","portfolio_snapshot_latest.csv",
        "portfolio_latest.csv"
    ],
    "audit_summary": [
        "audit_summary_latest.json","self_audit_summary_latest.json"
    ],
}

def _basename(name):
    return name.rsplit("/",1)[-1]

def _find_member(names,candidates):
    lower={_basename(n).lower():n for n in names if not n.endswith("/")}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    # relaxed suffix match
    for n in names:
        b=_basename(n).lower()
        for c in candidates:
            if b.endswith(c.lower()):
                return n
    return None

def _read_csv(z,member):
    with z.open(member) as f:
        return pd.read_csv(f)

def _read_json(z,member):
    with z.open(member) as f:
        return json.load(f)

def parse_crown_zip(uploaded_file):
    raw=uploaded_file.getvalue() if hasattr(uploaded_file,"getvalue") else uploaded_file.read()
    out={"found":{}, "errors":[], "source_name":getattr(uploaded_file,"name","uploaded.zip")}
    with zipfile.ZipFile(BytesIO(raw)) as z:
        names=z.namelist()
        for key,cands in PREFERRED_FILES.items():
            member=_find_member(names,cands)
            if not member:
                continue
            try:
                out["found"][key]=member
                out[key]=_read_json(z,member) if member.lower().endswith(".json") else _read_csv(z,member)
            except Exception as e:
                out["errors"].append(f"{key}: {e}")

        # If no explicit event summary JSON, recover state-like registry rows.
        if "research_registry" in out:
            df=out["research_registry"]
            cols={c.lower():c for c in df.columns}
            if "signal_id" in cols:
                out["signals"]=df.copy()

    return out

def extract_crown_status(bundle):
    status={
        "source":bundle.get("source_name"),
        "strategic_gate":"UNAVAILABLE",
        "strategic_deployment":"UNAVAILABLE",
        "tactical_gate":"UNAVAILABLE",
        "tactical_multiplier":"UNAVAILABLE",
        "dominant_event_phase":"UNAVAILABLE",
        "strategic_score":"UNAVAILABLE",
        "active_states":pd.DataFrame(),
    }

    es=bundle.get("event_summary")
    if isinstance(es,dict):
        sg=es.get("strategic_gate",{})
        status["strategic_gate"]=sg.get("state","UNAVAILABLE")
        status["strategic_deployment"]=sg.get("deployment_pct","UNAVAILABLE")
        status["tactical_multiplier"]=es.get("tactical_risk_multiplier","UNAVAILABLE")
        status["dominant_event_phase"]=es.get("dominant_event_phase","UNAVAILABLE")
        ra=es.get("research_adapter",{})
        status["strategic_score"]=ra.get("strategic_score","UNAVAILABLE")
        cs=ra.get("condition_states",{})
        if isinstance(cs,dict) and cs:
            rows=[]
            for k,v in cs.items():
                vv=str(v)
                inactive={"UNKNOWN","UNAVAILABLE","DATA_INSUFFICIENT","INSUFFICIENT_DATA"}
                state_status="UNAVAILABLE" if vv.upper() in inactive else "OBSERVED"
                rows.append({"Signal":k,"State":vv,"Status":state_status})
            status["active_states"]=pd.DataFrame(rows)

    tg=bundle.get("tactical_gate")
    if isinstance(tg,pd.DataFrame) and len(tg):
        r=tg.iloc[-1]
        for c in tg.columns:
            cl=c.lower()
            if "gate" in cl and status["tactical_gate"]=="UNAVAILABLE":
                status["tactical_gate"]=r[c]

    return status
