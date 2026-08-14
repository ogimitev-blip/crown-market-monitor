
import streamlit as st
import pandas as pd

from crown_monitor.official_data import (
    SERIES_CATALOG,catalog_dataframe,secret_status,load_catalog_series,
    align_pair,auto_operation,transform_pair,
    bea_nipa_table_names,load_bea_nipa_table,bea_line_series,
    load_bls_series,load_eia_series
)
from crown_monitor.universal_charts import comparison_chart,raw_pair_chart,single_series_chart
from crown_monitor.event_tools import all_events
from crown_monitor.preset_store import ensure_store, save_user_preset

ensure_store()
st.title("🌐 Universal Macro & Cross-Asset Lab")
st.caption("Market prices + FRED + BLS + BEA + EIA in one Crown research cockpit.")

tab1,tab2,tab3,tab4=st.tabs([
    "Universal Comparison","Official API Explorer","BEA NIPA Explorer","API Health"
])

with tab1:
    cat=catalog_dataframe()
    sources=sorted(cat["source"].unique().tolist())
    cats=sorted(cat["category"].unique().tolist())

    f1,f2=st.columns(2)
    source_filter=f1.multiselect("Sources",sources,default=sources)
    category_filter=f2.multiselect("Categories",cats,default=cats)

    view=cat[cat["source"].isin(source_filter) & cat["category"].isin(category_filter)].copy()
    available_keys=view["key"].tolist()

    if not available_keys:
        st.warning("No series match the selected filters.")
    else:
        def nice(k):
            m=SERIES_CATALOG[k]
            return f"[{m['source']}] {m['label']}"

        defaults_a="FRED:DGS30" if "FRED:DGS30" in available_keys else available_keys[0]
        defaults_b="FRED:DGS2" if "FRED:DGS2" in available_keys else available_keys[min(1,len(available_keys)-1)]

        c1,c2,c3=st.columns([2,2,1])
        key_a=c1.selectbox("Series A / Numerator",available_keys,index=available_keys.index(defaults_a),format_func=nice)
        key_b=c2.selectbox("Series B / Denominator",available_keys,index=available_keys.index(defaults_b),format_func=nice)
        years=c3.selectbox("History",[1,2,5,10,15],index=2)

        ma=SERIES_CATALOG[key_a]; mb=SERIES_CATALOG[key_b]
        auto=auto_operation(ma,mb)
        operations=[
            "AUTO","Ratio A / B","Spread A - B","Spread in basis points",
            "Indexed comparison","Indexed relative strength","Z-score divergence","YoY change spread"
        ]

        d1,d2=st.columns(2)
        op_sel=d1.selectbox("Transformation",operations,index=0)
        alignment=d2.selectbox("Alignment",["Auto","Native overlap","Daily forward-fill","Weekly","Monthly","Quarterly"],index=0)
        operation=auto if op_sel=="AUTO" else op_sel

        status=secret_status()
        missing=[]
        for m in (ma,mb):
            if m["source"] in ("FRED","BLS","EIA") and not status.get(m["source"],False):
                missing.append(m["source"])

        if missing:
            st.error("Missing Streamlit Secret(s): " + ", ".join(sorted(set(x+"_API_KEY" for x in missing))))
        else:
            with st.spinner("Loading official and market data…"):
                try:
                    a=load_catalog_series(key_a,years)
                    b=load_catalog_series(key_b,years)
                except Exception as e:
                    st.error(str(e))
                    a=pd.Series(dtype=float); b=pd.Series(dtype=float)

            if not a.empty and not b.empty:
                pair=align_pair(a,b,alignment)
                if pair.empty:
                    st.error("The two series do not have enough alignable observations.")
                else:
                    transformed,stats=transform_pair(pair,operation)

                    st.caption(
                        f"A: **{ma['label']}** · {ma['source']} · {ma['freq']} · {ma['unit_type']}  |  "
                        f"B: **{mb['label']}** · {mb['source']} · {mb['freq']} · {mb['unit_type']}  |  "
                        f"Operation: **{operation}**"
                    )

                    a1,a2,a3,a4=st.columns(4)
                    latest=stats.get("latest")
                    a1.metric("Composite",f"{latest:.4f}" if isinstance(latest,(int,float)) else "Indexed pair")
                    z=stats.get("z60")
                    a2.metric("60-period Z",f"{z:+.2f}" if isinstance(z,(int,float)) else "N/A")
                    corr=stats.get("corr20")
                    a3.metric("20-period correlation",f"{corr:+.2f}" if isinstance(corr,(int,float)) else "N/A")
                    a4.metric("Aligned observations",len(pair))

                    fig=comparison_chart(transformed,f"{ma['label']} vs {mb['label']} — {operation}",operation)

                    show_events=st.checkbox("Overlay Crown/manual events",value=True)
                    if show_events:
                        bundle=st.session_state.get("crown_bundle",{})
                        evs=all_events(bundle,st.session_state.get("manual_events",[]))
                        if len(transformed):
                            xmin=transformed.index.min(); xmax=transformed.index.max()
                            for ev in evs:
                                dt=ev["date"]
                                try:
                                    if dt.tzinfo is not None:
                                        dt=dt.tz_localize(None)
                                except Exception:
                                    pass
                                if xmin <= dt <= xmax:
                                    fig.add_vline(x=dt,line_dash="dot",opacity=0.45)
                                    fig.add_annotation(
                                        x=dt,y=1.0,yref="paper",text=str(ev["label"])[:28],
                                        showarrow=False,textangle=-90,yanchor="top",font=dict(size=9)
                                    )

                    st.plotly_chart(fig,width="stretch",config={"displaylogo":False})

                    with st.expander("Save this relationship / alert",expanded=False):
                        save_name=st.text_input("Saved view name",value=f"{ma['label']} vs {mb['label']}",key="universal_save_name")
                        sc1,sc2,sc3=st.columns(3)
                        alert_metric=sc1.selectbox("Alert metric",["z60","latest"],key="universal_alert_metric")
                        alert_operator=sc2.selectbox("Trigger when",["<=",">=","<",">"],key="universal_alert_operator")
                        alert_value=sc3.number_input("Threshold",value=1.5,step=0.25,key="universal_alert_value")
                        if st.button("Save current relationship",key="universal_save_button"):
                            save_user_preset({
                                "name":save_name,"a":key_a,"b":key_b,"operation":operation,
                                "alignment":alignment,"history":years,"family":"GENERIC",
                                "alert_metric":alert_metric,"alert_operator":alert_operator,
                                "alert_value":alert_value,
                                "why":"Saved from Universal Macro Lab."
                            })
                            st.success("Saved. Export from Saved Views for durable backup.")

                    with st.expander("Underlying series — indexed comparison",expanded=False):
                        st.plotly_chart(raw_pair_chart(pair,ma["label"],mb["label"]),width="stretch",config={"displaylogo":False})

                    if ma["freq"]!=mb["freq"]:
                        st.warning(
                            "Mixed-frequency comparison. Lower-frequency observations are aligned by the selected rule. "
                            "Use this as a research diagnostic, not an execution-grade trading ratio."
                        )

                    st.info(
                        "Crown rule: relative relationships are evidence, not standalone trades. "
                        "For rates use spreads/basis points; for prices use ratios/indexed relative strength; "
                        "for mixed units prefer indexed or z-score comparisons."
                    )

with tab2:
    st.subheader("Direct official-series explorer")
    source=st.selectbox("Official source",["BLS","EIA"],index=0)

    if source=="BLS":
        st.caption("Enter any BLS Public Data API series ID.")
        sid=st.text_input("BLS Series ID",value="JTS000000000000000JOL")
        yrs=st.slider("Years",1,19,10)
        if st.button("Load BLS series"):
            if not st.secrets.get("BLS_API_KEY",""):
                st.error("Add BLS_API_KEY to Streamlit Secrets.")
            else:
                try:
                    s=load_bls_series(sid,yrs)
                    if s.empty:
                        st.warning("No usable observations returned.")
                    else:
                        st.plotly_chart(single_series_chart(s,f"BLS {sid}"),width="stretch")
                        st.dataframe(s.tail(36).rename("Value").to_frame(),width="stretch")
                except Exception as e:
                    st.error(str(e))
    else:
        st.caption("Enter any legacy EIA Series ID; the app uses EIA API v2's SeriesID translation route.")
        sid=st.text_input("EIA Series ID",value="PET.WCESTUS1.W")
        yrs=st.slider("Years",1,20,10,key="eia_years")
        if st.button("Load EIA series"):
            if not st.secrets.get("EIA_API_KEY",""):
                st.error("Add EIA_API_KEY to Streamlit Secrets.")
            else:
                try:
                    s=load_eia_series(sid,yrs)
                    if s.empty:
                        st.warning("No usable observations returned.")
                    else:
                        st.plotly_chart(single_series_chart(s,f"EIA {sid}"),width="stretch")
                        st.dataframe(s.tail(52).rename("Value").to_frame(),width="stretch")
                except Exception as e:
                    st.error(str(e))

with tab3:
    st.subheader("BEA NIPA Explorer")
    if not st.secrets.get("BEA_API_KEY",""):
        st.error("Add BEA_API_KEY to Streamlit Secrets.")
    else:
        st.caption(
            "Direct BEA NIPA access. Table metadata is requested from BEA, then the selected table is loaded "
            "and you can chart any returned line."
        )
        try:
            tables=bea_nipa_table_names()
        except Exception as e:
            tables=[]
            st.warning(f"Could not load BEA table metadata: {e}")

        if tables:
            options=[f"{t} — {d}" if d else t for t,d in tables]
            choice=st.selectbox("NIPA table",options,index=0)
            table_name=choice.split(" — ")[0]
        else:
            table_name=st.text_input("NIPA TableName",value="T10101")

        frequency=st.selectbox("Frequency",["Q","M","A"],index=0)
        year=st.text_input("Year parameter",value="ALL")

        if st.button("Load BEA NIPA table"):
            try:
                df=load_bea_nipa_table(table_name,frequency,year)
                st.session_state["bea_nipa_df"]=df
                st.session_state["bea_nipa_table"]=table_name
            except Exception as e:
                st.error(str(e))

        df=st.session_state.get("bea_nipa_df")
        if isinstance(df,pd.DataFrame) and not df.empty:
            st.success(f"Loaded {len(df):,} BEA rows from {st.session_state.get('bea_nipa_table','')}.")
            if "LineNumber" in df:
                choices=[]
                seen=set()
                for _,r in df.iterrows():
                    ln=str(r.get("LineNumber",""))
                    if ln in seen:
                        continue
                    seen.add(ln)
                    desc=str(r.get("LineDescription","")) if "LineDescription" in df else ""
                    choices.append((ln,desc))
                labels=[f"{ln} — {desc}" if desc else ln for ln,desc in choices]
                sel=st.selectbox("Line",labels)
                ln=sel.split(" — ")[0]
                s=bea_line_series(df,ln)
                if not s.empty:
                    st.plotly_chart(single_series_chart(s,sel),width="stretch")
                    st.dataframe(s.tail(40).rename("Value").to_frame(),width="stretch")
            with st.expander("Raw BEA rows"):
                st.dataframe(df.head(500),width="stretch",height=400)

st.subheader("Manual chart events")
with st.expander("Add an event marker",expanded=False):
    ec1,ec2=st.columns(2)
    event_date=ec1.date_input("Event date")
    event_label=ec2.text_input("Event label",value="Macro event")
    if st.button("Add manual event"):
        st.session_state["manual_events"].append({"date":str(event_date),"label":event_label})
        st.success("Event added for this session.")

with tab4:
    st.subheader("API Health")
    status=secret_status()
    cols=st.columns(4)
    for col,(name,ok) in zip(cols,status.items()):
        col.metric(name,"KEY PRESENT" if ok else "MISSING")

    st.code(
        'FRED_API_KEY = "..."\nBLS_API_KEY = "..."\nBEA_API_KEY = "..."\nEIA_API_KEY = "..."',
        language="toml"
    )
    st.caption("Add these in Streamlit Community Cloud → App settings → Secrets. Do not commit API keys to GitHub.")

    cat=catalog_dataframe()
    st.write(f"**Universal catalogue:** {len(cat)} curated series")
    st.dataframe(
        cat[["source","category","label","locator","freq","unit_type"]].sort_values(["source","category","label"]),
        hide_index=True,width="stretch",height=520
    )
