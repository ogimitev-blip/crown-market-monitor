
import streamlit as st
import pandas as pd

from crown_monitor.relationship_engine import (
    built_in_presets, get_preset, evaluate_relationship, default_watch_names
)
from crown_monitor.preset_store import ensure_store, all_presets

st.title("🚨 Crown Live Watch")
st.caption("Only surfaces relationships crossing meaningful relative-value / macro thresholds.")

ensure_store()
allp=all_presets()
names=[p["name"] for p in allp]

if not st.session_state["watch_relationship_names"]:
    st.session_state["watch_relationship_names"]=[n for n in default_watch_names() if n in names]

with st.expander("Watch-list settings",expanded=False):
    st.session_state["watch_relationship_names"]=st.multiselect(
        "Relationships to monitor",
        names,
        default=[n for n in st.session_state["watch_relationship_names"] if n in names]
    )
    st.caption("Thresholds come from each preset. Custom rules can be created in Saved Views.")

@st.fragment(run_every="60s")
def watch():
    selected=st.session_state["watch_relationship_names"]
    if not selected:
        st.info("No relationships selected.")
        return

    results=[]
    for name in selected:
        p=next((x for x in allp if x["name"]==name),None)
        if not p:
            continue
        r=evaluate_relationship(p)
        if not r.get("ok"):
            results.append({
                "Relationship":name,"Status":"DATA GAP","Observed":"—",
                "Threshold":"—","Crown State":"UNAVAILABLE","Interpretation":r.get("error","")
            })
            continue
        observed=r.get("alert_value_observed")
        threshold=f"{p.get('alert_operator','>=')} {p.get('alert_value',1.5)}"
        results.append({
            "Relationship":name,
            "Status":"TRIGGERED" if r["triggered"] else "NORMAL",
            "Observed":round(float(observed),2) if isinstance(observed,(int,float)) else None,
            "Threshold":threshold,
            "Crown State":r["interpretation"]["state"],
            "Interpretation":r["interpretation"]["meaning"],
        })

    df=pd.DataFrame(results)
    trig=df[df["Status"]=="TRIGGERED"] if len(df) else pd.DataFrame()

    a,b,c=st.columns(3)
    a.metric("Watched",len(df))
    b.metric("Triggered",len(trig))
    c.metric("Data gaps",int((df["Status"]=="DATA GAP").sum()) if len(df) else 0)

    if len(trig):
        st.error(f"{len(trig)} Crown relationship alert(s) triggered.")
        for _,r in trig.iterrows():
            with st.container(border=True):
                st.markdown(f"### 🔴 {r['Relationship']}")
                st.write(f"**{r['Crown State']}** · observed {r['Observed']} · threshold {r['Threshold']}")
                st.write(r["Interpretation"])
    else:
        st.success("No selected Crown relationship is outside its configured threshold.")

    st.subheader("All watched relationships")
    st.dataframe(df,hide_index=True,width="stretch",height=500)

watch()

st.caption("Live Watch refreshes while this page is open. It is not a background notification service.")
