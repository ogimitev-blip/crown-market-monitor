
from __future__ import annotations
from datetime import datetime, timezone
import math
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

MARKET_TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "USDJPY": "JPY=X",
    "Gold": "GC=F",
    "Gold Miners": "GDX",
    "Brent": "BZ=F",
    "WTI": "CL=F",
    "SPY": "SPY",
    "RSP": "RSP",
}

FRED_SERIES = {
    "US 2Y": "DGS2",
    "US 10Y": "DGS10",
    "US 30Y": "DGS30",
    "US 10Y Real": "DFII10",
}

def _fmt_number(x, pct=False):
    if x is None or pd.isna(x):
        return "N/A"
    if pct:
        return f"{float(x):.2f}%"
    if abs(float(x)) >= 1000:
        return f"{float(x):,.0f}"
    return f"{float(x):.2f}"

@st.cache_data(ttl=60, show_spinner=False)
def load_yahoo_market():
    rows = []
    for name, ticker in MARKET_TICKERS.items():
        try:
            hist = yf.download(
                ticker,
                period="5d",
                interval="1m" if name not in {"SPY","RSP"} else "5m",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            if hist is None or hist.empty:
                raise ValueError("No price data")
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = [c[0] for c in hist.columns]
            close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
            if close.empty:
                raise ValueError("No close values")
            last = float(close.iloc[-1])

            # Previous-session reference: use first valid point at least ~1 day back if possible,
            # otherwise first available point. This is intentionally an MVP approximation.
            prev = float(close.iloc[0])
            if len(close) > 5:
                prev = float(close.iloc[max(0, len(close)-min(len(close), 390))])
            delta_pct = (last / prev - 1.0) * 100 if prev else float("nan")
            rows.append({
                "name": name,
                "ticker": ticker,
                "value_raw": last,
                "value": _fmt_number(last),
                "delta_raw": delta_pct,
                "delta": f"{delta_pct:+.2f}%" if math.isfinite(delta_pct) else "N/A",
                "source": "Yahoo/yfinance",
                "ok": True,
            })
        except Exception as e:
            rows.append({
                "name": name, "ticker": ticker, "value_raw": None,
                "value": "N/A", "delta_raw": None, "delta": "N/A",
                "source": "Yahoo/yfinance", "ok": False, "error": str(e)[:120]
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def load_fred_rates():
    key = st.secrets.get("FRED_API_KEY", "")
    if not key:
        return pd.DataFrame([{
            "name": name, "series": series, "value_raw": None, "value": "N/A",
            "delta_raw": None, "delta": "FRED key missing", "source": "FRED",
            "ok": False
        } for name, series in FRED_SERIES.items()])

    rows = []
    url = "https://api.stlouisfed.org/fred/series/observations"
    for name, series in FRED_SERIES.items():
        try:
            params = {
                "series_id": series,
                "api_key": key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 10,
            }
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            obs = r.json()["observations"]
            vals = []
            for o in obs:
                try:
                    vals.append((o["date"], float(o["value"])))
                except Exception:
                    pass
            if not vals:
                raise ValueError("No usable observations")
            latest_date, latest = vals[0]
            previous = vals[1][1] if len(vals) > 1 else latest
            delta_bp = (latest - previous) * 100
            rows.append({
                "name": name,
                "series": series,
                "value_raw": latest,
                "value": f"{latest:.2f}%",
                "delta_raw": delta_bp,
                "delta": f"{delta_bp:+.1f} bp",
                "source": f"FRED ({latest_date})",
                "ok": True,
            })
        except Exception as e:
            rows.append({
                "name": name, "series": series, "value_raw": None,
                "value": "N/A", "delta_raw": None, "delta": "N/A",
                "source": "FRED", "ok": False, "error": str(e)[:120]
            })
    return pd.DataFrame(rows)

def _lookup(df, name, field="value_raw"):
    x = df[df["name"] == name]
    if x.empty:
        return None
    v = x.iloc[0].get(field)
    return None if pd.isna(v) else v

def derive_live_states(market, rates):
    states = []

    y10 = _lookup(rates, "US 10Y")
    y30 = _lookup(rates, "US 30Y")
    y2d = _lookup(rates, "US 2Y", "delta_raw")
    y10d = _lookup(rates, "US 10Y", "delta_raw")
    y30d = _lookup(rates, "US 30Y", "delta_raw")
    gold_d = _lookup(market, "Gold", "delta_raw")
    dxy_d = _lookup(market, "DXY", "delta_raw")
    gdx_d = _lookup(market, "Gold Miners", "delta_raw")

    if y30 is not None and y30 >= 5.0:
        states.append({
            "State":"LONG_END_STRESS","Status":"ACTIVE","Confidence":85,
            "Evidence":f"US 30Y is {y30:.2f}%, above the 5% Crown stress threshold.",
            "Portfolio_Implication":"Raise the hurdle for duration-sensitive tactical exposure."
        })

    if y2d is not None and y10d is not None and y30d is not None and y2d < 0 and (y10d >= 0 or y30d >= 0):
        states.append({
            "State":"FRONT_END_LONG_END_DECOUPLING","Status":"ACTIVE","Confidence":78,
            "Evidence":f"2Y moved {y2d:+.1f} bp while 10Y/30Y moved {y10d:+.1f}/{y30d:+.1f} bp.",
            "Portfolio_Implication":"Do not equate easier Fed pricing with a long-duration buy signal."
        })

    if y30 is not None and y30 >= 5.0:
        states.append({
            "State":"MARKET_IMPOSED_TIGHTENING","Status":"WATCH","Confidence":72,
            "Evidence":"Long-end yields remain restrictive even without a policy-rate change.",
            "Portfolio_Implication":"Favor strong cash-flow/low-refinancing-dependency equities."
        })

    if gold_d is not None and dxy_d is not None and gold_d < 0 and dxy_d <= 0:
        states.append({
            "State":"PRECIOUS_METALS_CONFIRMATION","Status":"NOT_CONFIRMED","Confidence":70,
            "Evidence":f"Gold is {gold_d:+.2f}% while DXY is {dxy_d:+.2f}%; favorable USD transmission is not producing bullion strength.",
            "Portfolio_Implication":"Do not add higher-beta gold-miner exposure yet."
        })

    if gdx_d is not None and gold_d is not None and gdx_d < gold_d:
        states.append({
            "State":"GOLD_HEDGE_FAILURE","Status":"WATCH","Confidence":65,
            "Evidence":f"Gold miners ({gdx_d:+.2f}%) are underperforming gold ({gold_d:+.2f}%).",
            "Portfolio_Implication":"Miner beta remains tactically fragile."
        })

    return pd.DataFrame(states)

def live_snapshot():
    market = load_yahoo_market()
    rates = load_fred_rates()
    states = derive_live_states(market, rates)

    metrics = []
    for name in ["US 2Y","US 10Y","US 30Y"]:
        x = rates[rates["name"] == name]
        if len(x):
            metrics.append(x.iloc[0][["name","value","delta","source","ok"]].to_dict())
    for name in ["DXY","USDJPY","S&P 500","Nasdaq 100","VIX","Gold","Gold Miners","Brent","WTI"]:
        x = market[market["name"] == name]
        if len(x):
            metrics.append(x.iloc[0][["name","value","delta","source","ok"]].to_dict())

    return {
        "last_update": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "market_df": market,
        "rates_df": rates,
        "states_df": states,
        "metrics": metrics,
    }
