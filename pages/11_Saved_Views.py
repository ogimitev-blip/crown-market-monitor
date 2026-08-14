
import streamlit as st
import pandas as pd

from crown_monitor.official_data import SERIES_CATALOG
from crown_monitor.relationship_engine import evaluate_relationship
from crown_monitor.preset_store import (
    ensure_store, all_presets, save_user_preset, delete_user_preset,
    export_state_json, import_state_json
)
from crown_monitor.universal_charts import comparison_chart

st.title("⭐ Saved Views & Alert Rules")
st.caption("Create reusable Crown relationships, attach thresholds, and export/import your workspace.")

ensure_store()

tabs=st.tabs(["Create / edit","Saved dashboard","Import / export"])

with tabs[0]:
    keys=list(SERIES_CATALOG.keys())
    def label(k):
        m=SERIES_CATALOG[k]
        return f"[{m['source']}] {m['label']}"

    name=st.text_input("Preset name",value="My Crown relationship")
    c1,c2=st.columns(2)
    a=c1.selectbox("Series A",keys,index=keys.index("MKT:IS0E") if "MKT:IS0E" in keys else 0,format_func=label)
    b=c2.selectbox("Series B",keys,index=keys.index("MKT:GLD") if "MKT:GLD" in keys else 1,format_func=label)

    c3,c4,c5=st.columns(3)
    operation=c3.selectbox("Operation",[
        "Ratio A / B","Spread A - B","Spread in basis points",
        "Indexed comparison","Indexed relative strength","Z-score divergence","YoY change spread"
    ])
    alignment=c4.selectbox("Alignment",["Auto","Native overlap","Daily forward-fill","Weekly","Monthly","Quarterly"])
    history=c5.selectbox("History",[1,2,5,10,15],index=2)

    c6,c7,c8=st.columns(3)
    metric=c6.selectbox("Alert metric",["z60","latest"])
    operator=c7.selectbox("Trigger when",["<=",">=","<",">"],index=0)
    threshold=c8.number_input("Threshold",value=-1.5,step=0.25)

    why=st.text_input("Why this relationship matters",value="Custom Crown relative-value / macro diagnostic.")
    family=st.text_input("Interpretation family",value="GENERIC")

    config={
        "name":name,"a":a,"b":b,"operation":operation,"alignment":alignment,
        "history":history,"family":family,"alert_metric":metric,
        "alert_operator":operator,"alert_value":threshold,"why":why
    }

    if st.button("Save preset"):
        save_user_preset(config)
        st.success("Preset saved for this Streamlit session. Export the workspace for durable backup.")

with tabs[1]:
    presets=all_presets()
    user_names=[p["name"] for p in st.session_state["user_relationship_presets"]]
    chosen=st.multiselect("Views to display",[p["name"] for p in presets],default=user_names[:4])

    for name in chosen[:8]:
        p=next(x for x in presets if x["name"]==name)
        r=evaluate_relationship(p)
        with st.container(border=True):
            st.markdown(f"### {name}")
            st.caption(p.get("why",""))
            if not r.get("ok"):
                st.warning(r.get("error","Data unavailable"))
            else:
                interp=r["interpretation"]
                c1,c2,c3=st.columns(3)
                obs=r.get("alert_value_observed")
                c1.metric("Alert metric",f"{obs:+.2f}" if isinstance(obs,(int,float)) else "N/A")
                c2.metric("Status","TRIGGERED" if r["triggered"] else "NORMAL")
                c3.metric("Crown State",interp["state"])
                st.plotly_chart(
                    comparison_chart(r["transformed"],name,p["operation"]),
                    width="stretch",config={"displaylogo":False}
                )
                st.write(interp["meaning"])

    if user_names:
        to_delete=st.selectbox("Delete a custom preset",["—"]+user_names)
        if to_delete!="—" and st.button("Delete selected custom preset"):
            delete_user_preset(to_delete)
            st.success("Deleted.")

with tabs[2]:
    blob=export_state_json()
    st.download_button(
        "Download Crown workspace JSON",
        data=blob,
        file_name="crown_streamlit_workspace.json",
        mime="application/json"
    )
    upl=st.file_uploader("Import Crown workspace JSON",type=["json"])
    if upl is not None and st.button("Import workspace"):
        try:
            import_state_json(upl.getvalue().decode("utf-8"))
            st.success("Workspace imported.")
        except Exception as e:
            st.error(str(e))

st.warning("Streamlit Community Cloud local/session storage is not a durable database. Export the workspace JSON to preserve custom views and alert rules across app resets.")
