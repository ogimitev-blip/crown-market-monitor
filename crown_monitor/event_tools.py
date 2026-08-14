
from __future__ import annotations
import pandas as pd

def _first_col(df,names):
    lower={str(c).lower():c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    for c in df.columns:
        cl=str(c).lower()
        if any(n.lower() in cl for n in names):
            return c
    return None

def events_from_bundle(bundle):
    rows=[]
    for key in ("upcoming_events","event_transmission","event_interactions","upcoming_event_risk"):
        df=bundle.get(key)
        if not isinstance(df,pd.DataFrame) or df.empty:
            continue
        date_col=_first_col(df,["date","event_date","as_of","datetime","time"])
        name_col=_first_col(df,["event","event_name","name","description","event_id"])
        if not date_col:
            continue
        for _,r in df.iterrows():
            try:
                dt=pd.Timestamp(r[date_col])
            except Exception:
                continue
            name=str(r[name_col]) if name_col else key
            rows.append({"date":dt,"label":name,"source":"CROWN"})
    # dedupe
    out=[]
    seen=set()
    for r in sorted(rows,key=lambda x:x["date"]):
        k=(str(r["date"]),r["label"])
        if k not in seen:
            seen.add(k); out.append(r)
    return out

def all_events(bundle,manual_events):
    rows=events_from_bundle(bundle or {})
    for e in manual_events or []:
        try:
            rows.append({"date":pd.Timestamp(e["date"]),"label":str(e["label"]),"source":"MANUAL"})
        except Exception:
            pass
    return sorted(rows,key=lambda x:x["date"])
