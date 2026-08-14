
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

def _fmt_number(x):
    if x is None or pd.isna(x):
        return "N/A"
    x=float(x)
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.2f}"

@st.cache_data(ttl=60, show_spinner=False)
def load_yahoo_market():
    rows=[]
    for name,ticker in MARKET_TICKERS.items():
        try:
            # Latest intraday price
            intraday = yf.download(
                ticker, period="2d", interval="1m",
                progress=False, auto_adjust=False, threads=False
            )
            if intraday is None or intraday.empty:
                raise ValueError("No intraday data")
            if isinstance(intraday.columns, pd.MultiIndex):
                intraday.columns=[c[0] for c in intraday.columns]
            last_series=pd.to_numeric(intraday["Close"],errors="coerce").dropna()
            if last_series.empty:
                raise ValueError("No live close")
            last=float(last_series.iloc[-1])

            # Official daily close history for previous-close comparison.
            daily = yf.download(
                ticker, period="10d", interval="1d",
                progress=False, auto_adjust=False, threads=False
            )
            if daily is None or daily.empty:
                raise ValueError("No daily history")
            if isinstance(daily.columns,pd.MultiIndex):
                daily.columns=[c[0] for c in daily.columns]
            dclose=pd.to_numeric(daily["Close"],errors="coerce").dropna()
            if len(dclose) < 2:
                raise ValueError("Insufficient daily closes")

            # If today's daily bar already exists, previous official close is penultimate;
            # otherwise use last available daily close.
            today_utc = pd.Timestamp.now(tz="UTC").date()
            idx_dates = [pd.Timestamp(i).date() for i in dclose.index]
            if idx_dates[-1] == today_utc and len(dclose) >= 2:
                prev_close=float(dclose.iloc[-2])
            else:
                prev_close=float(dclose.iloc[-1])

            delta_pct=(last/prev_close-1.0)*100 if prev_close else float("nan")
            rows.append({
                "name":name,"ticker":ticker,"value_raw":last,"value":_fmt_number(last),
                "delta_raw":delta_pct,
                "delta":f"{delta_pct:+.2f}%" if math.isfinite(delta_pct) else "N/A",
                "source":"Yahoo/yfinance",
                "frequency":"LIVE/INTRADAY",
                "reference":"vs previous official close",
                "ok":True
            })
        except Exception as e:
            rows.append({
                "name":name,"ticker":ticker,"value_raw":None,"value":"N/A",
                "delta_raw":None,"delta":"N/A","source":"Yahoo/yfinance",
                "frequency":"LIVE/INTRADAY","reference":"vs previous official close","freshness":"UNAVAILABLE",
                "ok":False,"error":str(e)[:160]
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def load_fred_rates():
    key=st.secrets.get("FRED_API_KEY","")
    if not key:
        return pd.DataFrame([{
            "name":name,"series":series,"value_raw":None,"value":"N/A",
            "delta_raw":None,"delta":"FRED key missing","source":"FRED",
            "frequency":"DAILY","reference":"vs previous FRED observation","ok":False
        } for name,series in FRED_SERIES.items()])

    rows=[]
    url="https://api.stlouisfed.org/fred/series/observations"
    for name,series in FRED_SERIES.items():
        try:
            params={
                "series_id":series,"api_key":key,"file_type":"json",
                "sort_order":"desc","limit":10
            }
            r=requests.get(url,params=params,timeout=15)
            r.raise_for_status()
            obs=r.json()["observations"]
            vals=[]
            for o in obs:
                try:
                    vals.append((o["date"],float(o["value"])))
                except Exception:
                    pass
            if not vals:
                raise ValueError("No usable observations")
            latest_date,latest=vals[0]
            previous=vals[1][1] if len(vals)>1 else latest
            delta_bp=(latest-previous)*100
            obs_date=pd.Timestamp(latest_date).date()
            today=pd.Timestamp.now(tz="UTC").date()
            age_days=(today-obs_date).days
            freshness="FRESH" if age_days<=1 else "STALE"
            rows.append({
                "name":name,"series":series,"value_raw":latest,
                "value":f"{latest:.2f}%","delta_raw":delta_bp,
                "delta":f"{delta_bp:+.1f} bp","source":f"FRED · {latest_date}",
                "frequency":"DAILY","reference":"vs previous FRED observation","freshness":freshness,"age_days":age_days,"ok":True
            })
        except Exception as e:
            rows.append({
                "name":name,"series":series,"value_raw":None,"value":"N/A",
                "delta_raw":None,"delta":"N/A","source":"FRED",
                "frequency":"DAILY","reference":"vs previous FRED observation","freshness":"UNAVAILABLE","age_days":None,
                "ok":False,"error":str(e)[:160]
            })
    return pd.DataFrame(rows)

def _lookup(df,name,field="value_raw"):
    x=df[df["name"]==name]
    if x.empty:
        return None
    v=x.iloc[0].get(field)
    return None if pd.isna(v) else v

def derive_live_states(market,rates):
    states=[]
    y30=_lookup(rates,"US 30Y")
    y2d=_lookup(rates,"US 2Y","delta_raw")
    y10d=_lookup(rates,"US 10Y","delta_raw")
    y30d=_lookup(rates,"US 30Y","delta_raw")
    gold_d=_lookup(market,"Gold","delta_raw")
    dxy_d=_lookup(market,"DXY","delta_raw")
    gdx_d=_lookup(market,"Gold Miners","delta_raw")

    if y30 is not None and y30>=5.0:
        states.append({
            "State":"LONG_END_STRESS","Status":"ACTIVE","Confidence":85,
            "Evidence":f"US 30Y is {y30:.2f}% (latest daily FRED observation), above the 5% Crown stress threshold.",
            "Portfolio_Implication":"Raise the hurdle for duration-sensitive tactical exposure."
        })

    if None not in (y2d,y10d,y30d) and y2d<0 and (y10d>=0 or y30d>=0):
        states.append({
            "State":"FRONT_END_LONG_END_DECOUPLING","Status":"ACTIVE","Confidence":78,
            "Evidence":f"Latest daily FRED changes: 2Y {y2d:+.1f} bp, 10Y {y10d:+.1f} bp, 30Y {y30d:+.1f} bp.",
            "Portfolio_Implication":"Do not equate easier front-end pricing with a long-duration buy signal."
        })

    if y30 is not None and y30>=5.0:
        states.append({
            "State":"MARKET_IMPOSED_TIGHTENING","Status":"WATCH","Confidence":72,
            "Evidence":"Long-end yields remain restrictive even without a policy-rate change.",
            "Portfolio_Implication":"Favor strong cash-flow/low-refinancing-dependency equities."
        })

    if gold_d is not None and dxy_d is not None and gold_d<0 and dxy_d<=0:
        states.append({
            "State":"PRECIOUS_METALS_CONFIRMATION","Status":"NOT_CONFIRMED","Confidence":70,
            "Evidence":f"Gold {gold_d:+.2f}% vs previous close while DXY {dxy_d:+.2f}%; favorable USD transmission is not producing bullion strength.",
            "Portfolio_Implication":"Do not add higher-beta gold-miner exposure yet."
        })

    if gdx_d is not None and gold_d is not None and gdx_d<gold_d:
        states.append({
            "State":"GOLD_HEDGE_FAILURE","Status":"WATCH","Confidence":65,
            "Evidence":f"GDX {gdx_d:+.2f}% vs gold {gold_d:+.2f}% today.",
            "Portfolio_Implication":"Miner beta remains tactically fragile."
        })
    return pd.DataFrame(states)

def live_snapshot():
    market=load_yahoo_market()
    rates=load_fred_rates()
    states=derive_live_states(market,rates)
    metrics=[]
    for name in ["US 2Y","US 10Y","US 30Y"]:
        x=rates[rates["name"]==name]
        if len(x):
            metrics.append(x.iloc[0][["name","value","delta","source","frequency","reference","freshness","ok"]].to_dict())
    for name in ["DXY","USDJPY","S&P 500","Nasdaq 100","VIX","Gold","Gold Miners","Brent","WTI"]:
        x=market[market["name"]==name]
        if len(x):
            metrics.append(x.iloc[0][["name","value","delta","source","frequency","reference","freshness","ok"]].to_dict())
    return {
        "last_update":datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "market_df":market,"rates_df":rates,"states_df":states,"metrics":metrics
    }
