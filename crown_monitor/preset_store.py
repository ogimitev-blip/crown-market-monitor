
from __future__ import annotations
import json
import streamlit as st
from crown_monitor.relationship_engine import built_in_presets

def ensure_store():
    st.session_state.setdefault("user_relationship_presets",[])
    st.session_state.setdefault("watch_relationship_names",[])
    st.session_state.setdefault("manual_events",[])

def all_presets():
    ensure_store()
    return built_in_presets()+list(st.session_state["user_relationship_presets"])

def save_user_preset(config):
    ensure_store()
    name=config.get("name","Custom relationship").strip()
    items=[p for p in st.session_state["user_relationship_presets"] if p.get("name")!=name]
    items.append(config)
    st.session_state["user_relationship_presets"]=items

def delete_user_preset(name):
    ensure_store()
    st.session_state["user_relationship_presets"]=[
        p for p in st.session_state["user_relationship_presets"] if p.get("name")!=name
    ]

def export_state_json():
    ensure_store()
    payload={
        "version":"1.0",
        "user_relationship_presets":st.session_state["user_relationship_presets"],
        "watch_relationship_names":st.session_state["watch_relationship_names"],
        "manual_events":st.session_state["manual_events"],
    }
    return json.dumps(payload,indent=2)

def import_state_json(raw):
    ensure_store()
    obj=json.loads(raw)
    for k in ("user_relationship_presets","watch_relationship_names","manual_events"):
        if k in obj and isinstance(obj[k],list):
            st.session_state[k]=obj[k]
