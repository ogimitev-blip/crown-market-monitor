
from __future__ import annotations
import json
from pathlib import Path
import math
import pandas as pd
import streamlit as st

from crown_monitor.official_data import (
    SERIES_CATALOG, load_catalog_series, align_pair, transform_pair, secret_status
)

ROOT=Path(__file__).resolve().parents[1]
PRESET_FILE=ROOT/"data/crown_relationship_presets.json"

@st.cache_data(ttl=3600,show_spinner=False)
def built_in_presets():
    return json.loads(PRESET_FILE.read_text(encoding="utf-8"))

def get_preset(name):
    for p in built_in_presets():
        if p["name"]==name:
            return p.copy()
    return None

def eval_condition(value,operator,threshold):
    if value is None or pd.isna(value):
        return False
    if operator==">=":
        return float(value)>=float(threshold)
    if operator=="<=":
        return float(value)<=float(threshold)
    if operator==">":
        return float(value)>float(threshold)
    if operator=="<":
        return float(value)<float(threshold)
    return False

def evaluate_relationship(config):
    a_key=config["a"]; b_key=config["b"]
    ma=SERIES_CATALOG[a_key]; mb=SERIES_CATALOG[b_key]
    status=secret_status()
    for meta in (ma,mb):
        src=meta["source"]
        if src in ("FRED","BLS","EIA") and not status.get(src,False):
            return {"ok":False,"error":f"{src}_API_KEY missing"}

    try:
        a=load_catalog_series(a_key,int(config.get("history",5)))
        b=load_catalog_series(b_key,int(config.get("history",5)))
    except Exception as e:
        return {"ok":False,"error":str(e)}

    pair=align_pair(a,b,config.get("alignment","Auto"))
    if pair.empty:
        return {"ok":False,"error":"No alignable observations"}

    transformed,stats=transform_pair(pair,config.get("operation","Indexed comparison"))
    if transformed.empty:
        return {"ok":False,"error":"No transformed observations"}

    metric=config.get("alert_metric","z60")
    value=stats.get(metric)
    if metric=="latest":
        value=stats.get("latest")
    triggered=eval_condition(value,config.get("alert_operator",">="),config.get("alert_value",1.5))
    interp=interpret_relationship(config,stats,pair,transformed)
    return {
        "ok":True,
        "pair":pair,
        "transformed":transformed,
        "stats":stats,
        "triggered":triggered,
        "alert_value_observed":value,
        "interpretation":interp,
        "meta_a":ma,
        "meta_b":mb,
    }

def _direction(series,lookback=20):
    s=series.dropna()
    if len(s)<=lookback:
        return "FLAT / INSUFFICIENT"
    ch=float(s.iloc[-1]-s.iloc[-1-lookback])
    if ch>0: return "RISING"
    if ch<0: return "FALLING"
    return "FLAT"

def interpret_relationship(config,stats,pair,transformed):
    fam=config.get("family","GENERIC")
    z=stats.get("z60")
    corr=stats.get("corr20")
    comp=transformed["Composite"].dropna() if "Composite" in transformed else pd.Series(dtype=float)
    direction=_direction(comp,20) if len(comp) else "COMPARISON"

    ztxt="normal"
    if isinstance(z,(int,float)) and math.isfinite(z):
        if z>=2: ztxt="extremely high"
        elif z>=1: ztxt="high"
        elif z<=-2: ztxt="extremely low"
        elif z<=-1: ztxt="low"

    if fam=="BREADTH":
        state="BREADTH_BROADENING" if direction=="RISING" else "BREADTH_NARROWING"
        meaning="Equal-weight participation is improving relative to cap-weighted SPY." if direction=="RISING" else "The cap-weighted index is outperforming equal-weight participation; concentration risk is rising."
    elif fam=="CONCENTRATION":
        state="CONCENTRATION_FRAGILITY" if direction=="RISING" else "BREADTH_BROADENING"
        meaning="Mega-cap/growth concentration is strengthening." if direction=="RISING" else "Concentration is easing as equal-weight participation catches up."
    elif fam in ("MINER_TRANSMISSION","GOLD_RELATIVE"):
        state="MINERS_CONFIRM" if direction=="RISING" else "MINER_LAG_OR_FAILURE"
        meaning="Higher-beta precious-metals exposure is confirming bullion/relative strength." if direction=="RISING" else "Miners are lagging the reference asset; do not infer bullish miner transmission from bullion strength alone."
    elif fam=="GOLD_MACRO":
        state="GOLD_MACRO_DIVERGENCE"
        meaning="Real-yield and gold behavior are diverging unusually; check USD, bullion price response and whether the divergence is temporary or structural."
    elif fam=="LONG_END_STRESS":
        state="LONG_END_STRESS_CONFIRMATION" if direction=="RISING" else "LONG_END_STRESS_EASING"
        meaning="Financials are outperforming housing, consistent with elevated long-end pressure." if direction=="RISING" else "Housing is repairing relative to financials, weakening the long-end-stress expression."
    elif fam=="CREDIT":
        state="CREDIT_STRESS_WARNING" if config.get("operation")=="Z-score divergence" and direction=="RISING" else ("CREDIT_RISK_APPETITE_IMPROVING" if direction=="RISING" else "CREDIT_RISK_APPETITE_WEAKENING")
        meaning="Credit and equities are diverging; widening OAS relative to SPY is a warning." if config.get("operation")=="Z-score divergence" else ("High-yield risk appetite is improving relative to investment grade." if direction=="RISING" else "High-yield risk appetite is weakening relative to investment grade.")
    elif fam=="CURVE":
        state="FRONT_END_LONG_END_DECOUPLING" if direction=="RISING" else "CURVE_PRESSURE_EASING"
        meaning="The long end is steepening relative to the front/intermediate curve, consistent with term-premium or supply pressure." if direction=="RISING" else "The long-end spread is compressing, reducing the immediate decoupling signal."
    elif fam=="INFLATION_TRANSMISSION":
        state="COMMODITY_INFLATION_TRANSMISSION_WATCH"
        meaning="Energy and inflation pricing are diverging; persistence determines whether oil is transmitting into inflation expectations."
    elif fam=="INFLATION_PIPELINE":
        state="INFLATION_PIPELINE_DIVERGENCE"
        meaning="Consumer and producer inflation momentum differ; inspect services/goods composition and revisions before inferring persistence."
    elif fam=="LIQUIDITY":
        state="LIQUIDITY_DIVERGENCE_WATCH"
        meaning="The liquidity proxy and equities are unusually divergent. Treat this as context, not a standalone tactical signal."
    elif fam=="LABOUR":
        state="LABOUR_DEMAND_DIVERGENCE"
        meaning="Job openings and payroll employment are diverging; this can distinguish a hiring-buffer slowdown from a confirmed labour break."
    elif fam=="OIL_PHYSICAL":
        state="OIL_PHYSICAL_CONFIRMATION_WATCH"
        meaning="Inventories and crude price are diverging; falling stocks with strong Brent supports physical tightness, while rising stocks weaken it."
    elif fam=="AI_LEADERSHIP":
        state="AI_LEADERSHIP_CONFIRMING" if direction=="RISING" else "AI_LEADERSHIP_WEAKENING"
        meaning="Semiconductor leadership is strengthening versus the broad market." if direction=="RISING" else "Semiconductor relative leadership is weakening; avoid interpreting index strength as uniform AI health."
    elif fam=="RISK_APPETITE":
        state="CYCLICAL_RISK_ON" if direction=="RISING" else "DEFENSIVE_ROTATION"
        meaning="Cyclicals are outperforming defensives." if direction=="RISING" else "Defensive consumer exposure is outperforming cyclicals."
    else:
        state="RELATIVE_VALUE_MONITOR"
        meaning=f"The composite is {direction.lower()} and its 60-period z-score is {ztxt}."

    confidence="MODERATE"
    if isinstance(z,(int,float)) and abs(z)>=2:
        confidence="HIGH_EXTREME"
    elif isinstance(z,(int,float)) and abs(z)<0.5:
        confidence="LOW / NORMAL_RANGE"

    return {
        "state":state,
        "meaning":meaning,
        "direction":direction,
        "z_state":ztxt.upper(),
        "confidence":confidence,
        "caveat":"Heuristic Crown interpretation from the selected relationship; it does not override the uploaded Crown Framework decision layer."
    }

def default_watch_names():
    return [
        "Breadth — RSP / SPY",
        "Concentration — QQQ / RSP",
        "Miners vs bullion — GDX / GLD",
        "IS0E vs bullion — IS0E / GLD",
        "30Y - 2Y curve",
        "Real yield vs gold",
        "Credit appetite — HYG / LQD",
        "High Yield OAS vs SPY",
        "Breakeven inflation vs Brent",
        "Crude stocks vs Brent",
    ]
