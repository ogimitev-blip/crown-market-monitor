
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "instrument_registry.csv"

@st.cache_data(ttl=3600, show_spinner=False)
def instrument_registry():
    return pd.read_csv(REGISTRY)

def yahoo_symbol(ticker: str) -> str:
    reg = instrument_registry()
    t = str(ticker).strip().upper()
    hit = reg[reg["Ticker"].astype(str).str.upper() == t]
    if len(hit):
        return str(hit.iloc[0]["Yahoo_Symbol"])
    if "." in t or "=" in t or t.startswith("^"):
        return t
    return f"{t}.DE"

def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [c[0] for c in df.columns]
    return df

@st.cache_data(ttl=60, show_spinner=False)
def load_history(symbol: str, interval: str = "1d", period: str = "1y") -> pd.DataFrame:
    df = yf.download(
        symbol, interval=interval, period=period,
        auto_adjust=False, progress=False, threads=False
    )
    if df is None or df.empty:
        return pd.DataFrame()
    df = _flatten(df).copy()
    for c in ["Open","High","Low","Close","Volume"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Close"])
    return df

def interval_period(interval: str):
    return {
        "15m": ("60d", "15m"),
        "1h": ("730d", "60m"),
        "1D": ("2y", "1d"),
    }.get(interval, ("2y","1d"))

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    x = df.copy()
    close=x["Close"]; high=x["High"]; low=x["Low"]

    for n in [20,50,100,200]:
        x[f"SMA{n}"] = close.rolling(n).mean()

    # RSI 14
    d=close.diff()
    gain=d.clip(lower=0).rolling(14).mean()
    loss=(-d.clip(upper=0)).rolling(14).mean()
    rs=gain/loss.replace(0,np.nan)
    x["RSI14"]=100-(100/(1+rs))

    # ATR 14
    prev=close.shift(1)
    tr=pd.concat([(high-low).abs(),(high-prev).abs(),(low-prev).abs()],axis=1).max(axis=1)
    x["ATR14"]=tr.rolling(14).mean()

    # Rolling VWAP, works for both intraday/daily proxy
    if "Volume" in x and x["Volume"].fillna(0).sum() > 0:
        typical=(high+low+close)/3
        v=x["Volume"].fillna(0)
        x["VWAP20"]=(typical*v).rolling(20).sum()/v.rolling(20).sum().replace(0,np.nan)
    else:
        x["VWAP20"]=np.nan

    # Ichimoku
    x["Tenkan"]=(high.rolling(9).max()+low.rolling(9).min())/2
    x["Kijun"]=(high.rolling(26).max()+low.rolling(26).min())/2
    x["SpanA"]=((x["Tenkan"]+x["Kijun"])/2).shift(26)
    x["SpanB"]=((high.rolling(52).max()+low.rolling(52).min())/2).shift(26)

    # SuperTrend 10,3
    atr10=tr.rolling(10).mean()
    hl2=(high+low)/2
    upper=hl2+3*atr10
    lower=hl2-3*atr10
    final_upper=upper.copy()
    final_lower=lower.copy()
    st=pd.Series(index=x.index,dtype=float)
    direction=pd.Series(index=x.index,dtype=float)
    for i in range(1,len(x)):
        if pd.isna(atr10.iloc[i]):
            continue
        pi=i-1
        final_upper.iloc[i] = upper.iloc[i] if (
            upper.iloc[i] < final_upper.iloc[pi] or close.iloc[pi] > final_upper.iloc[pi]
        ) else final_upper.iloc[pi]
        final_lower.iloc[i] = lower.iloc[i] if (
            lower.iloc[i] > final_lower.iloc[pi] or close.iloc[pi] < final_lower.iloc[pi]
        ) else final_lower.iloc[pi]
        prev_st=st.iloc[pi] if not pd.isna(st.iloc[pi]) else final_upper.iloc[pi]
        if prev_st == final_upper.iloc[pi]:
            st.iloc[i] = final_upper.iloc[i] if close.iloc[i] <= final_upper.iloc[i] else final_lower.iloc[i]
        else:
            st.iloc[i] = final_lower.iloc[i] if close.iloc[i] >= final_lower.iloc[i] else final_upper.iloc[i]
        direction.iloc[i]=1 if close.iloc[i] > st.iloc[i] else -1
    x["SuperTrend"]=st
    x["SuperTrendDir"]=direction

    # Support/resistance: recent range + ATR zone
    x["Support20"]=low.rolling(20).min()
    x["Resistance20"]=high.rolling(20).max()
    return x

def technical_snapshot(df: pd.DataFrame):
    if df is None or df.empty:
        return {}
    x=add_indicators(df)
    r=x.iloc[-1]
    close=float(r["Close"])
    sma20=r.get("SMA20"); sma50=r.get("SMA50"); sma200=r.get("SMA200")
    atr=r.get("ATR14")
    trend="MIXED"
    if pd.notna(sma20) and pd.notna(sma50):
        trend="BULLISH" if close>sma20>sma50 else ("BEARISH" if close<sma20<sma50 else "MIXED")
    entry="UNKNOWN"
    if pd.notna(atr) and atr>0 and pd.notna(sma20):
        ext=(close-sma20)/atr
        if ext>2.0: entry="EXTENDED / NO CHASE"
        elif ext>0.75: entry="WAIT / PULLBACK"
        elif ext>-0.5: entry="ACCEPTABLE"
        else: entry="RETEST / VERIFY"
    return {
        "price":close,
        "trend":trend,
        "entry":entry,
        "rsi":float(r["RSI14"]) if pd.notna(r.get("RSI14")) else None,
        "support":float(r["Support20"]) if pd.notna(r.get("Support20")) else None,
        "resistance":float(r["Resistance20"]) if pd.notna(r.get("Resistance20")) else None,
        "sma20":float(sma20) if pd.notna(sma20) else None,
        "sma50":float(sma50) if pd.notna(sma50) else None,
        "sma200":float(sma200) if pd.notna(sma200) else None,
        "atr":float(atr) if pd.notna(atr) else None,
        "supertrend":"BULLISH" if r.get("SuperTrendDir")==1 else ("BEARISH" if r.get("SuperTrendDir")==-1 else "UNKNOWN"),
    }

@st.cache_data(ttl=90, show_spinner=False)
def normalized_cross_asset(symbols: tuple, period="6mo"):
    data={}
    for s in symbols:
        try:
            df=load_history(s,"1d",period)
            if not df.empty:
                data[s]=df["Close"]
        except Exception:
            pass
    if not data:
        return pd.DataFrame()
    px=pd.concat(data,axis=1).dropna(how="all").ffill().dropna()
    if px.empty:
        return px
    return px/px.iloc[0]*100

def rolling_corr(px: pd.DataFrame, anchor: str, window=20):
    if px.empty or anchor not in px.columns:
        return pd.DataFrame()
    rets=px.pct_change().dropna()
    out={}
    for c in rets.columns:
        if c==anchor: continue
        out[c]=rets[anchor].rolling(window).corr(rets[c])
    return pd.DataFrame(out)
