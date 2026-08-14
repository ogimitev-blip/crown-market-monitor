
from __future__ import annotations
from io import BytesIO
from datetime import datetime, timezone
import json, zipfile, re
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
    "portfolio_snapshot": [
        "current_portfolio_snapshot.csv","current_portfolio_snapshot_latest.csv"
    ],
    "portfolio_review": ["portfolio_review_latest.csv"],
    "watchlist_assessment": ["watchlist_assessment_latest.csv"],
    "watchlist_technical": ["watchlist_technical_latest.csv"],
    "execution_governance": ["canonical_execution_governance_latest.csv"],
    "trade_plan": ["three_layer_trade_plan_latest.csv"],
    "upcoming_event_risk": ["upcoming_event_risk_latest.csv"],
    "event_transmission": ["event_transmission_latest.csv"],
    "event_interactions": ["event_interactions_latest.csv"],
    "upcoming_events": ["upcoming_events_latest.csv","event_calendar_latest.csv"],
}

def _basename(name):
    return name.rsplit("/",1)[-1]

def _find_member(names,candidates):
    lower={_basename(n).lower():n for n in names if not n.endswith("/")}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
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
        if "research_registry" in out:
            df=out["research_registry"]
            cols={c.lower():c for c in df.columns}
            if "signal_id" in cols:
                out["signals"]=df.copy()
    return out

def _parse_dt(value):
    if value is None:
        return None
    try:
        ts=pd.Timestamp(value)
        if ts.tzinfo is None:
            ts=ts.tz_localize("UTC")
        else:
            ts=ts.tz_convert("UTC")
        return ts.to_pydatetime()
    except Exception:
        return None

def _infer_dt_from_name(name):
    # Recognizes e.g. Crown_Framework_Results_20260813_104755.zip
    m=re.search(r"(20\d{6})(?:[_-]?(\d{6}))?", str(name))
    if not m:
        return None
    d=m.group(1)
    t=m.group(2) or "000000"
    try:
        return datetime.strptime(d+t,"%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None

def _state_status(value):
    """Preserve meaningful Crown terminal/quality states instead of crude OBSERVED."""
    u=str(value).strip().upper()
    if not u:
        return "UNAVAILABLE"
    if "UNCONFIRMED" in u:
        return "UNCONFIRMED"
    if "INSUFFICIENT" in u:
        return "DATA_INSUFFICIENT"
    if "UNAVAILABLE" in u:
        return "UNAVAILABLE"
    if "UNKNOWN" in u:
        return "UNKNOWN"
    if "MIXED" in u or "TRANSITION" in u:
        return "MIXED / TRANSITION"
    if "NO_MATERIAL_SURPRISE" in u or u.startswith("NO_"):
        return "NO TRIGGER"
    if "HOLD_WAIT_FOR_CONFIRMATION" in u:
        return "WAIT / CONFIRM"
    if "CLEAR_EVENT_PATH" in u or "HEALTHY_CONTANGO" in u or "OPEN" == u:
        return "CLEAR / OPEN"
    return "ACTIVE STATE"

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
        "run_as_of":None,
        "run_age_hours":None,
        "run_freshness":"UNKNOWN",
        "stale_inputs":[],
        "unverified_inputs":[],
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

        # Prefer explicit framework as-of.
        dt=_parse_dt(es.get("as_of")) or _infer_dt_from_name(bundle.get("source_name"))
        if dt:
            now=datetime.now(timezone.utc)
            age=max(0.0,(now-dt).total_seconds()/3600.0)
            status["run_as_of"]=dt.strftime("%Y-%m-%d %H:%M UTC")
            status["run_age_hours"]=age
            if age <= 6:
                status["run_freshness"]="FRESH"
            elif age <= 24:
                status["run_freshness"]="AGING"
            else:
                status["run_freshness"]="STALE"

        lir=es.get("live_input_refresh",{}) or {}
        status["stale_inputs"]=list(lir.get("stale_inputs",[]) or [])
        status["unverified_inputs"]=list(lir.get("unverified_or_unavailable_inputs",[]) or [])

        cs=ra.get("condition_states",{})
        if isinstance(cs,dict) and cs:
            rows=[]
            for k,v in cs.items():
                rows.append({
                    "Signal":k,
                    "Crown State":str(v),
                    "Status":_state_status(v),
                })
            status["active_states"]=pd.DataFrame(rows)

    if status["run_as_of"] is None:
        dt=_infer_dt_from_name(bundle.get("source_name"))
        if dt:
            age=max(0.0,(datetime.now(timezone.utc)-dt).total_seconds()/3600.0)
            status["run_as_of"]=dt.strftime("%Y-%m-%d %H:%M UTC")
            status["run_age_hours"]=age
            status["run_freshness"]="FRESH" if age<=6 else ("AGING" if age<=24 else "STALE")

    tg=bundle.get("tactical_gate")
    if isinstance(tg,pd.DataFrame) and len(tg):
        r=tg.iloc[-1]
        for c in tg.columns:
            cl=c.lower()
            if "gate" in cl and status["tactical_gate"]=="UNAVAILABLE":
                status["tactical_gate"]=r[c]
    return status
