
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from crown_monitor.market_tools import load_history

ASSET_UNIVERSE = {
    # Broad / style
    "SPY — S&P 500": "SPY",
    "RSP — S&P 500 Equal Weight": "RSP",
    "QQQ — Nasdaq 100": "QQQ",
    "IWM — Russell 2000": "IWM",
    "DIA — Dow Jones": "DIA",

    # Sectors / themes
    "SOXX — Semiconductors": "SOXX",
    "XLF — Financials": "XLF",
    "ITB — Homebuilders": "ITB",
    "XLV — Healthcare": "XLV",
    "XLP — Consumer Staples": "XLP",
    "XLY — Consumer Discretionary": "XLY",
    "XLE — Energy": "XLE",
    "XLU — Utilities": "XLU",
    "XLI — Industrials": "XLI",
    "XLK — Technology": "XLK",

    # Credit / duration
    "HYG — High Yield Credit": "HYG",
    "LQD — Investment Grade Credit": "LQD",
    "TLT — Long Treasuries": "TLT",
    "IEF — 7–10Y Treasuries": "IEF",
    "SHY — 1–3Y Treasuries": "SHY",

    # Metals / commodities
    "GLD — Gold": "GLD",
    "GDX — Gold Miners": "GDX",
    "SLV — Silver": "SLV",
    "GC=F — Gold Futures": "GC=F",
    "SI=F — Silver Futures": "SI=F",
    "BZ=F — Brent": "BZ=F",
    "CL=F — WTI": "CL=F",
    "DBC — Broad Commodities": "DBC",

    # FX
    "DXY — US Dollar Index": "DX-Y.NYB",
    "USDJPY": "JPY=X",
    "EURUSD": "EURUSD=X",

    # Crown UCITS
    "IS0E — Gold Producers": "IS0E.DE",
    "SEC0 — Global Semiconductors": "SEC0.DE",
    "VWCE — FTSE All-World": "VWCE.DE",
    "VWCG — Developed Europe": "VWCG.DE",
    "QDVE — US Information Technology": "QDVE.DE",
    "XDWH — World Healthcare": "XDWH.DE",
    "CBUX — Global Infrastructure": "CBUX.DE",
    "VFEA — Emerging Markets": "VFEA.DE",
    "IS3Q — World Quality": "IS3Q.DE",
    "SXR0 — World Min Vol": "SXR0.DE",
    "XAAG — Broad Commodities": "XAAG.DE",
    "XMK9 — World Momentum": "XMK9.DE",
}

PRESETS = {
    "Custom": None,
    "RSP / SPY — Breadth": ("RSP", "SPY"),
    "GLD / SPY — Gold vs equities": ("GLD", "SPY"),
    "GDX / GLD — Miners vs bullion": ("GDX", "GLD"),
    "IS0E / GLD — IS0E vs bullion": ("IS0E.DE", "GLD"),
    "IS0E / GDX — IS0E vs US miners": ("IS0E.DE", "GDX"),
    "SOXX / SPY — Semiconductor leadership": ("SOXX", "SPY"),
    "QQQ / RSP — Concentration": ("QQQ", "RSP"),
    "XLF / ITB — Financials vs housing": ("XLF", "ITB"),
    "XLY / XLP — Cyclicals vs defensives": ("XLY", "XLP"),
    "XLE / SPY — Energy leadership": ("XLE", "SPY"),
    "HYG / LQD — Credit risk appetite": ("HYG", "LQD"),
    "GLD / TLT — Gold vs duration": ("GLD", "TLT"),
    "SLV / GLD — Precious-metals breadth": ("SLV", "GLD"),
    "VWCG / VWCE — Europe vs global": ("VWCG.DE", "VWCE.DE"),
    "SEC0 / VWCE — Semis vs global": ("SEC0.DE", "VWCE.DE"),
}

def label_for_symbol(symbol: str) -> str:
    for label, sym in ASSET_UNIVERSE.items():
        if sym == symbol:
            return label
    return symbol

def key_for_symbol(symbol: str) -> str:
    for label, sym in ASSET_UNIVERSE.items():
        if sym == symbol:
            return label
    return next(iter(ASSET_UNIVERSE))

@st.cache_data(ttl=90, show_spinner=False)
def build_ratio(numerator: str, denominator: str, period: str = "1y"):
    a = load_history(numerator, "1d", period)
    b = load_history(denominator, "1d", period)
    if a.empty or b.empty:
        return pd.DataFrame(), {}

    px = pd.concat(
        [a["Close"].rename("Numerator"), b["Close"].rename("Denominator")],
        axis=1
    ).dropna()

    if px.empty:
        return pd.DataFrame(), {}

    px["Ratio"] = px["Numerator"] / px["Denominator"]
    px["SMA20"] = px["Ratio"].rolling(20).mean()
    px["SMA50"] = px["Ratio"].rolling(50).mean()
    px["SMA200"] = px["Ratio"].rolling(200).mean()

    mean60 = px["Ratio"].rolling(60).mean()
    std60 = px["Ratio"].rolling(60).std()
    px["Z60"] = (px["Ratio"] - mean60) / std60.replace(0, np.nan)

    ra = px["Numerator"].pct_change()
    rb = px["Denominator"].pct_change()
    px["Corr20"] = ra.rolling(20).corr(rb)

    def change(n):
        if len(px) <= n:
            return None
        return (float(px["Ratio"].iloc[-1]) / float(px["Ratio"].iloc[-1-n]) - 1) * 100

    r = px.iloc[-1]
    ratio = float(r["Ratio"])
    sma20 = float(r["SMA20"]) if pd.notna(r["SMA20"]) else None
    sma50 = float(r["SMA50"]) if pd.notna(r["SMA50"]) else None
    z60 = float(r["Z60"]) if pd.notna(r["Z60"]) else None
    corr20 = float(r["Corr20"]) if pd.notna(r["Corr20"]) else None

    trend = "MIXED"
    if sma20 is not None and sma50 is not None:
        if ratio > sma20 > sma50:
            trend = "NUMERATOR LEADING"
        elif ratio < sma20 < sma50:
            trend = "DENOMINATOR LEADING"

    stats = {
        "ratio": ratio,
        "change_5d": change(5),
        "change_20d": change(20),
        "z60": z60,
        "corr20": corr20,
        "trend": trend,
    }
    return px, stats
