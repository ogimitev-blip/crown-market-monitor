
from __future__ import annotations

from datetime import datetime
from urllib.parse import quote
import re
import requests
import numpy as np
import pandas as pd
import streamlit as st

from crown_monitor.market_tools import load_history

SERIES_CATALOG = {
    # Market / equity
    "MKT:SPY":{"label":"SPY — S&P 500","source":"YAHOO","locator":"SPY","freq":"daily","unit_type":"price","category":"Equity"},
    "MKT:RSP":{"label":"RSP — S&P 500 Equal Weight","source":"YAHOO","locator":"RSP","freq":"daily","unit_type":"price","category":"Breadth"},
    "MKT:QQQ":{"label":"QQQ — Nasdaq 100","source":"YAHOO","locator":"QQQ","freq":"daily","unit_type":"price","category":"Equity"},
    "MKT:IWM":{"label":"IWM — Russell 2000","source":"YAHOO","locator":"IWM","freq":"daily","unit_type":"price","category":"Equity"},
    "MKT:DIA":{"label":"DIA — Dow Jones","source":"YAHOO","locator":"DIA","freq":"daily","unit_type":"price","category":"Equity"},
    "MKT:SOXX":{"label":"SOXX — Semiconductors","source":"YAHOO","locator":"SOXX","freq":"daily","unit_type":"price","category":"AI/Semis"},
    "MKT:XLF":{"label":"XLF — Financials","source":"YAHOO","locator":"XLF","freq":"daily","unit_type":"price","category":"Sector"},
    "MKT:ITB":{"label":"ITB — Homebuilders","source":"YAHOO","locator":"ITB","freq":"daily","unit_type":"price","category":"Housing"},
    "MKT:XLV":{"label":"XLV — Healthcare","source":"YAHOO","locator":"XLV","freq":"daily","unit_type":"price","category":"Sector"},
    "MKT:XLP":{"label":"XLP — Consumer Staples","source":"YAHOO","locator":"XLP","freq":"daily","unit_type":"price","category":"Sector"},
    "MKT:XLY":{"label":"XLY — Consumer Discretionary","source":"YAHOO","locator":"XLY","freq":"daily","unit_type":"price","category":"Sector"},
    "MKT:XLE":{"label":"XLE — Energy","source":"YAHOO","locator":"XLE","freq":"daily","unit_type":"price","category":"Energy"},
    "MKT:XLU":{"label":"XLU — Utilities","source":"YAHOO","locator":"XLU","freq":"daily","unit_type":"price","category":"Sector"},
    "MKT:XLI":{"label":"XLI — Industrials","source":"YAHOO","locator":"XLI","freq":"daily","unit_type":"price","category":"Sector"},
    "MKT:XLK":{"label":"XLK — Technology","source":"YAHOO","locator":"XLK","freq":"daily","unit_type":"price","category":"Sector"},
    "MKT:HYG":{"label":"HYG — High Yield Credit","source":"YAHOO","locator":"HYG","freq":"daily","unit_type":"price","category":"Credit"},
    "MKT:LQD":{"label":"LQD — Investment Grade Credit","source":"YAHOO","locator":"LQD","freq":"daily","unit_type":"price","category":"Credit"},
    "MKT:TLT":{"label":"TLT — Long Treasuries","source":"YAHOO","locator":"TLT","freq":"daily","unit_type":"price","category":"Rates"},
    "MKT:IEF":{"label":"IEF — 7–10Y Treasuries","source":"YAHOO","locator":"IEF","freq":"daily","unit_type":"price","category":"Rates"},
    "MKT:SHY":{"label":"SHY — 1–3Y Treasuries","source":"YAHOO","locator":"SHY","freq":"daily","unit_type":"price","category":"Rates"},
    "MKT:GLD":{"label":"GLD — Gold","source":"YAHOO","locator":"GLD","freq":"daily","unit_type":"price","category":"Metals"},
    "MKT:GDX":{"label":"GDX — Gold Miners","source":"YAHOO","locator":"GDX","freq":"daily","unit_type":"price","category":"Metals"},
    "MKT:SLV":{"label":"SLV — Silver","source":"YAHOO","locator":"SLV","freq":"daily","unit_type":"price","category":"Metals"},
    "MKT:GOLD":{"label":"Gold Futures","source":"YAHOO","locator":"GC=F","freq":"daily","unit_type":"price","category":"Metals"},
    "MKT:SILVER":{"label":"Silver Futures","source":"YAHOO","locator":"SI=F","freq":"daily","unit_type":"price","category":"Metals"},
    "MKT:BRENT":{"label":"Brent Futures","source":"YAHOO","locator":"BZ=F","freq":"daily","unit_type":"price","category":"Energy"},
    "MKT:WTI":{"label":"WTI Futures","source":"YAHOO","locator":"CL=F","freq":"daily","unit_type":"price","category":"Energy"},
    "MKT:DBC":{"label":"DBC — Broad Commodities","source":"YAHOO","locator":"DBC","freq":"daily","unit_type":"price","category":"Commodities"},
    "MKT:DXY":{"label":"DXY — US Dollar Index","source":"YAHOO","locator":"DX-Y.NYB","freq":"daily","unit_type":"index","category":"FX"},
    "MKT:USDJPY":{"label":"USDJPY","source":"YAHOO","locator":"JPY=X","freq":"daily","unit_type":"price","category":"FX"},
    "MKT:EURUSD":{"label":"EURUSD","source":"YAHOO","locator":"EURUSD=X","freq":"daily","unit_type":"price","category":"FX"},
    "MKT:VIX":{"label":"VIX","source":"YAHOO","locator":"^VIX","freq":"daily","unit_type":"index","category":"Volatility"},

    # Crown UCITS
    "MKT:IS0E":{"label":"IS0E — Gold Producers","source":"YAHOO","locator":"IS0E.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:SEC0":{"label":"SEC0 — Global Semiconductors","source":"YAHOO","locator":"SEC0.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:VWCE":{"label":"VWCE — FTSE All-World","source":"YAHOO","locator":"VWCE.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:VWCG":{"label":"VWCG — Developed Europe","source":"YAHOO","locator":"VWCG.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:QDVE":{"label":"QDVE — US Information Technology","source":"YAHOO","locator":"QDVE.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:XDWH":{"label":"XDWH — World Healthcare","source":"YAHOO","locator":"XDWH.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:CBUX":{"label":"CBUX — Global Infrastructure","source":"YAHOO","locator":"CBUX.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:VFEA":{"label":"VFEA — Emerging Markets","source":"YAHOO","locator":"VFEA.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:IS3Q":{"label":"IS3Q — World Quality","source":"YAHOO","locator":"IS3Q.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:SXR0":{"label":"SXR0 — World Min Vol","source":"YAHOO","locator":"SXR0.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:XAAG":{"label":"XAAG — Broad Commodities","source":"YAHOO","locator":"XAAG.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},
    "MKT:XMK9":{"label":"XMK9 — World Momentum","source":"YAHOO","locator":"XMK9.DE","freq":"daily","unit_type":"price","category":"Crown UCITS"},

    # FRED nominal curve
    "FRED:DGS1MO":{"label":"US Treasury 1M","source":"FRED","locator":"DGS1MO","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS3MO":{"label":"US Treasury 3M","source":"FRED","locator":"DGS3MO","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS6MO":{"label":"US Treasury 6M","source":"FRED","locator":"DGS6MO","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS1":{"label":"US Treasury 1Y","source":"FRED","locator":"DGS1","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS2":{"label":"US Treasury 2Y","source":"FRED","locator":"DGS2","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS5":{"label":"US Treasury 5Y","source":"FRED","locator":"DGS5","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS7":{"label":"US Treasury 7Y","source":"FRED","locator":"DGS7","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS10":{"label":"US Treasury 10Y","source":"FRED","locator":"DGS10","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS20":{"label":"US Treasury 20Y","source":"FRED","locator":"DGS20","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:DGS30":{"label":"US Treasury 30Y","source":"FRED","locator":"DGS30","freq":"daily","unit_type":"rate_pct","category":"Rates"},
    "FRED:T10Y2Y":{"label":"10Y–2Y Treasury Spread","source":"FRED","locator":"T10Y2Y","freq":"daily","unit_type":"rate_pct","category":"Curve"},
    "FRED:T10Y3M":{"label":"10Y–3M Treasury Spread","source":"FRED","locator":"T10Y3M","freq":"daily","unit_type":"rate_pct","category":"Curve"},

    # Real yields / inflation pricing
    "FRED:DFII5":{"label":"5Y TIPS Real Yield","source":"FRED","locator":"DFII5","freq":"daily","unit_type":"rate_pct","category":"Real Yields"},
    "FRED:DFII7":{"label":"7Y TIPS Real Yield","source":"FRED","locator":"DFII7","freq":"daily","unit_type":"rate_pct","category":"Real Yields"},
    "FRED:DFII10":{"label":"10Y TIPS Real Yield","source":"FRED","locator":"DFII10","freq":"daily","unit_type":"rate_pct","category":"Real Yields"},
    "FRED:DFII20":{"label":"20Y TIPS Real Yield","source":"FRED","locator":"DFII20","freq":"daily","unit_type":"rate_pct","category":"Real Yields"},
    "FRED:DFII30":{"label":"30Y TIPS Real Yield","source":"FRED","locator":"DFII30","freq":"daily","unit_type":"rate_pct","category":"Real Yields"},
    "FRED:T5YIE":{"label":"5Y Breakeven Inflation","source":"FRED","locator":"T5YIE","freq":"daily","unit_type":"rate_pct","category":"Inflation Pricing"},
    "FRED:T10YIE":{"label":"10Y Breakeven Inflation","source":"FRED","locator":"T10YIE","freq":"daily","unit_type":"rate_pct","category":"Inflation Pricing"},
    "FRED:T5YIFR":{"label":"5Y5Y Forward Inflation Expectation","source":"FRED","locator":"T5YIFR","freq":"daily","unit_type":"rate_pct","category":"Inflation Pricing"},

    # Fed / funding / liquidity
    "FRED:DFF":{"label":"Effective Federal Funds Rate","source":"FRED","locator":"DFF","freq":"daily","unit_type":"rate_pct","category":"Fed/Liquidity"},
    "FRED:SOFR":{"label":"SOFR","source":"FRED","locator":"SOFR","freq":"daily","unit_type":"rate_pct","category":"Fed/Liquidity"},
    "FRED:IORB":{"label":"Interest on Reserve Balances","source":"FRED","locator":"IORB","freq":"daily","unit_type":"rate_pct","category":"Fed/Liquidity"},
    "FRED:WALCL":{"label":"Fed Total Assets","source":"FRED","locator":"WALCL","freq":"weekly","unit_type":"quantity","category":"Liquidity"},
    "FRED:WRESBAL":{"label":"Reserve Balances with Fed Banks","source":"FRED","locator":"WRESBAL","freq":"weekly","unit_type":"quantity","category":"Liquidity"},
    "FRED:RRPONTSYD":{"label":"ON RRP Usage","source":"FRED","locator":"RRPONTSYD","freq":"daily","unit_type":"quantity","category":"Liquidity"},
    "FRED:WTREGEN":{"label":"US Treasury General Account","source":"FRED","locator":"WTREGEN","freq":"weekly","unit_type":"quantity","category":"Liquidity"},
    "FRED:M2SL":{"label":"M2 Money Stock","source":"FRED","locator":"M2SL","freq":"monthly","unit_type":"quantity","category":"Liquidity"},

    # Credit / financial conditions
    "FRED:BAMLH0A0HYM2":{"label":"US High Yield OAS","source":"FRED","locator":"BAMLH0A0HYM2","freq":"daily","unit_type":"rate_pct","category":"Credit"},
    "FRED:BAMLC0A0CM":{"label":"US Corporate OAS","source":"FRED","locator":"BAMLC0A0CM","freq":"daily","unit_type":"rate_pct","category":"Credit"},
    "FRED:NFCI":{"label":"National Financial Conditions Index","source":"FRED","locator":"NFCI","freq":"weekly","unit_type":"index","category":"Financial Conditions"},
    "FRED:ANFCI":{"label":"Adjusted National Financial Conditions Index","source":"FRED","locator":"ANFCI","freq":"weekly","unit_type":"index","category":"Financial Conditions"},

    # Growth / consumption / housing mirrors
    "FRED:GDPC1":{"label":"Real GDP — BEA via FRED","source":"FRED","locator":"GDPC1","freq":"quarterly","unit_type":"quantity","category":"Growth"},
    "FRED:GDP":{"label":"Nominal GDP — BEA via FRED","source":"FRED","locator":"GDP","freq":"quarterly","unit_type":"quantity","category":"Growth"},
    "FRED:PCE":{"label":"Personal Consumption Expenditures — BEA via FRED","source":"FRED","locator":"PCE","freq":"monthly","unit_type":"quantity","category":"Consumption"},
    "FRED:PCEPI":{"label":"PCE Price Index — BEA via FRED","source":"FRED","locator":"PCEPI","freq":"monthly","unit_type":"index","category":"Inflation"},
    "FRED:PCEPILFE":{"label":"Core PCE Price Index — BEA via FRED","source":"FRED","locator":"PCEPILFE","freq":"monthly","unit_type":"index","category":"Inflation"},
    "FRED:INDPRO":{"label":"Industrial Production","source":"FRED","locator":"INDPRO","freq":"monthly","unit_type":"index","category":"Growth"},
    "FRED:RSAFS":{"label":"Retail Sales","source":"FRED","locator":"RSAFS","freq":"monthly","unit_type":"quantity","category":"Consumption"},
    "FRED:DGORDER":{"label":"Durable Goods New Orders","source":"FRED","locator":"DGORDER","freq":"monthly","unit_type":"quantity","category":"Growth"},
    "FRED:HOUST":{"label":"Housing Starts","source":"FRED","locator":"HOUST","freq":"monthly","unit_type":"quantity","category":"Housing"},
    "FRED:PERMIT":{"label":"Building Permits","source":"FRED","locator":"PERMIT","freq":"monthly","unit_type":"quantity","category":"Housing"},

    # BLS direct
    "BLS:CUSR0000SA0":{"label":"CPI-U All Items, SA — BLS","source":"BLS","locator":"CUSR0000SA0","freq":"monthly","unit_type":"index","category":"Inflation"},
    "BLS:CUSR0000SA0L1E":{"label":"Core CPI, SA — BLS","source":"BLS","locator":"CUSR0000SA0L1E","freq":"monthly","unit_type":"index","category":"Inflation"},
    "BLS:LNS14000000":{"label":"Unemployment Rate — BLS","source":"BLS","locator":"LNS14000000","freq":"monthly","unit_type":"pct","category":"Labour"},
    "BLS:LNS11300000":{"label":"Labour Force Participation Rate — BLS","source":"BLS","locator":"LNS11300000","freq":"monthly","unit_type":"pct","category":"Labour"},
    "BLS:CES0000000001":{"label":"Nonfarm Payroll Employment — BLS","source":"BLS","locator":"CES0000000001","freq":"monthly","unit_type":"quantity","category":"Labour"},
    "BLS:CES0500000003":{"label":"Average Hourly Earnings, Total Private — BLS","source":"BLS","locator":"CES0500000003","freq":"monthly","unit_type":"quantity","category":"Labour"},
    "BLS:JTS000000000000000JOL":{"label":"JOLTS Job Openings — BLS","source":"BLS","locator":"JTS000000000000000JOL","freq":"monthly","unit_type":"quantity","category":"Labour"},
    "BLS:JTS000000000000000HIR":{"label":"JOLTS Hires Rate — BLS","source":"BLS","locator":"JTS000000000000000HIR","freq":"monthly","unit_type":"pct","category":"Labour"},
    "BLS:WPSFD4":{"label":"PPI Final Demand — BLS","source":"BLS","locator":"WPSFD4","freq":"monthly","unit_type":"index","category":"Inflation"},
    "BLS:WPSFD41":{"label":"PPI Final Demand Goods — BLS","source":"BLS","locator":"WPSFD41","freq":"monthly","unit_type":"index","category":"Inflation"},
    "BLS:WPSFD42":{"label":"PPI Final Demand Services — BLS","source":"BLS","locator":"WPSFD42","freq":"monthly","unit_type":"index","category":"Inflation"},
    "BLS:WPSFD49116":{"label":"PPI Final Demand ex Food/Energy/Trade — BLS","source":"BLS","locator":"WPSFD49116","freq":"monthly","unit_type":"index","category":"Inflation"},

    # EIA direct
    "EIA:PET.RWTC.D":{"label":"WTI Spot Price — EIA","source":"EIA","locator":"PET.RWTC.D","freq":"daily","unit_type":"price","category":"Energy"},
    "EIA:PET.RBRTE.D":{"label":"Brent Spot Price — EIA","source":"EIA","locator":"PET.RBRTE.D","freq":"daily","unit_type":"price","category":"Energy"},
    "EIA:PET.WCESTUS1.W":{"label":"US Crude Stocks ex SPR — EIA","source":"EIA","locator":"PET.WCESTUS1.W","freq":"weekly","unit_type":"quantity","category":"Energy"},
    "EIA:PET.WGTSTUS1.W":{"label":"US Total Gasoline Stocks — EIA","source":"EIA","locator":"PET.WGTSTUS1.W","freq":"weekly","unit_type":"quantity","category":"Energy"},
    "EIA:PET.WDISTUS1.W":{"label":"US Distillate Stocks — EIA","source":"EIA","locator":"PET.WDISTUS1.W","freq":"weekly","unit_type":"quantity","category":"Energy"},
}

def catalog_dataframe():
    return pd.DataFrame([{"key":k, **v} for k,v in SERIES_CATALOG.items()])

def secret_status():
    return {
        "FRED": bool(st.secrets.get("FRED_API_KEY","")),
        "BLS": bool(st.secrets.get("BLS_API_KEY","")),
        "BEA": bool(st.secrets.get("BEA_API_KEY","")),
        "EIA": bool(st.secrets.get("EIA_API_KEY","")),
    }

@st.cache_data(ttl=900, show_spinner=False)
def load_fred_series(series_id: str, years: int = 10):
    key=st.secrets.get("FRED_API_KEY","")
    if not key:
        raise RuntimeError("FRED_API_KEY is missing from Streamlit Secrets.")
    start=(pd.Timestamp.now(tz="UTC")-pd.DateOffset(years=years)).date().isoformat()
    r=requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id":series_id,"api_key":key,"file_type":"json","observation_start":start},
        timeout=20
    )
    r.raise_for_status()
    rows=[]
    for o in r.json().get("observations",[]):
        try:
            rows.append((pd.Timestamp(o["date"]),float(o["value"])))
        except Exception:
            pass
    return pd.Series({d:v for d,v in rows},name=series_id).sort_index() if rows else pd.Series(dtype=float,name=series_id)

@st.cache_data(ttl=1800, show_spinner=False)
def load_bls_series(series_id: str, years: int = 10):
    key=st.secrets.get("BLS_API_KEY","")
    if not key:
        raise RuntimeError("BLS_API_KEY is missing from Streamlit Secrets.")
    end=pd.Timestamp.now().year
    start=max(end-min(int(years),19),2000)
    payload={"seriesid":[series_id],"startyear":str(start),"endyear":str(end),"registrationkey":key}
    r=requests.post("https://api.bls.gov/publicAPI/v2/timeseries/data/",json=payload,timeout=25)
    r.raise_for_status()
    js=r.json()
    if js.get("status") not in (None,"REQUEST_SUCCEEDED"):
        raise RuntimeError("; ".join(js.get("message",[])) or "BLS request failed")
    series=js.get("Results",{}).get("series",[]) or []
    if not series:
        return pd.Series(dtype=float,name=series_id)
    rows=[]
    for item in series[0].get("data",[]):
        period=str(item.get("period",""))
        if not re.match(r"M(0[1-9]|1[0-2])$",period):
            continue
        try:
            dt=pd.Timestamp(year=int(item["year"]),month=int(period[1:]),day=1)
            rows.append((dt,float(str(item["value"]).replace(",",""))))
        except Exception:
            pass
    return pd.Series({d:v for d,v in rows},name=series_id).sort_index() if rows else pd.Series(dtype=float,name=series_id)

def _find_period_value_rows(obj):
    found=[]
    if isinstance(obj,list):
        if obj and isinstance(obj[0],dict) and "period" in obj[0]:
            for row in obj:
                if "period" not in row:
                    continue
                val=None
                for c in ("value","Value","series-value","data"):
                    if c in row:
                        val=row[c]
                        break
                if val is None:
                    for k,v in row.items():
                        if k.lower() in ("period","units","unit","name","series-description","series"):
                            continue
                        try:
                            float(str(v).replace(",",""))
                            val=v
                            break
                        except Exception:
                            pass
                if val is not None:
                    found.append((row.get("period"),val))
        else:
            for x in obj:
                found.extend(_find_period_value_rows(x))
    elif isinstance(obj,dict):
        for v in obj.values():
            found.extend(_find_period_value_rows(v))
    return found

def _parse_period(x):
    s=str(x)
    for fmt in ("%Y-%m-%d","%Y-%m","%Y"):
        try:
            return pd.Timestamp(datetime.strptime(s,fmt))
        except Exception:
            pass
    try:
        return pd.Timestamp(s)
    except Exception:
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def load_eia_series(series_id: str, years: int = 10):
    key=st.secrets.get("EIA_API_KEY","")
    if not key:
        raise RuntimeError("EIA_API_KEY is missing from Streamlit Secrets.")
    sid=quote(series_id,safe=".")
    urls=[
        f"https://api.eia.gov/v2/seriesid/{sid}?api_key={key}",
        f"https://api.eia.gov/v2/seriesid/{sid}/data/?api_key={key}",
    ]
    err=None
    for url in urls:
        try:
            r=requests.get(url,timeout=25)
            r.raise_for_status()
            rows=_find_period_value_rows(r.json())
            vals=[]
            for p,v in rows:
                dt=_parse_period(p)
                if dt is None:
                    continue
                try:
                    vals.append((dt,float(str(v).replace(",",""))))
                except Exception:
                    pass
            if vals:
                s=pd.Series({d:v for d,v in vals},name=series_id).sort_index()
                cutoff=pd.Timestamp.now().tz_localize(None)-pd.DateOffset(years=years)
                return s[s.index>=cutoff]
        except Exception as e:
            err=e
    if err:
        raise RuntimeError(f"EIA series unavailable: {err}")
    return pd.Series(dtype=float,name=series_id)

BEA_URL="https://apps.bea.gov/api/data/"

def _bea_key():
    k=st.secrets.get("BEA_API_KEY","")
    if not k:
        raise RuntimeError("BEA_API_KEY is missing from Streamlit Secrets.")
    return k

@st.cache_data(ttl=3600, show_spinner=False)
def bea_nipa_table_names():
    params={
        "UserID":_bea_key(),
        "method":"GetParameterValuesFiltered",
        "datasetname":"NIPA",
        "TargetParameter":"TableName",
        "ResultFormat":"JSON",
    }
    r=requests.get(BEA_URL,params=params,timeout=25)
    r.raise_for_status()
    vals=r.json().get("BEAAPI",{}).get("Results",{}).get("ParamValue",[])
    rows=[]
    for v in vals:
        table=v.get("TableName") or v.get("Key") or v.get("ParamValue")
        desc=v.get("Description") or v.get("Desc") or ""
        if table:
            rows.append((str(table),str(desc)))
    return rows

@st.cache_data(ttl=1800, show_spinner=False)
def load_bea_nipa_table(table_name: str, frequency: str="Q", year: str="ALL"):
    params={
        "UserID":_bea_key(),"method":"GetData","datasetname":"NIPA",
        "TableName":table_name,"Frequency":frequency,"Year":year,"ResultFormat":"JSON"
    }
    r=requests.get(BEA_URL,params=params,timeout=30)
    r.raise_for_status()
    data=r.json().get("BEAAPI",{}).get("Results",{}).get("Data",[])
    return pd.DataFrame(data) if data else pd.DataFrame()

def bea_line_series(df,line_number):
    if df is None or df.empty or "LineNumber" not in df:
        return pd.Series(dtype=float)
    x=df[df["LineNumber"].astype(str)==str(line_number)].copy()
    rows=[]
    for _,r in x.iterrows():
        tp=str(r.get("TimePeriod",""))
        try:
            v=float(str(r.get("DataValue")).replace(",",""))
        except Exception:
            continue
        if re.match(r"^\d{4}Q[1-4]$",tp):
            y=int(tp[:4]); q=int(tp[-1]); m=3*q
            dt=pd.Timestamp(year=y,month=m,day=1)+pd.offsets.MonthEnd(0)
        elif re.match(r"^\d{4}M\d{2}$",tp):
            dt=pd.Timestamp(year=int(tp[:4]),month=int(tp[-2:]),day=1)
        elif re.match(r"^\d{4}$",tp):
            dt=pd.Timestamp(year=int(tp),month=12,day=31)
        else:
            try:
                dt=pd.Timestamp(tp)
            except Exception:
                continue
        rows.append((dt,v))
    return pd.Series({d:v for d,v in rows}).sort_index() if rows else pd.Series(dtype=float)

@st.cache_data(ttl=90, show_spinner=False)
def load_catalog_series(key: str, years: int=10):
    meta=SERIES_CATALOG[key]
    source=meta["source"]
    loc=meta["locator"]
    if source=="YAHOO":
        period="10y" if years>=10 else ("5y" if years>=5 else ("2y" if years>=2 else "1y"))
        df=load_history(loc,"1d",period)
        return df["Close"].rename(key) if not df.empty else pd.Series(dtype=float,name=key)
    if source=="FRED":
        return load_fred_series(loc,years).rename(key)
    if source=="BLS":
        return load_bls_series(loc,years).rename(key)
    if source=="EIA":
        return load_eia_series(loc,years).rename(key)
    raise RuntimeError(f"Unsupported source {source}")

def _zscore(s,window=60):
    minp=max(5,min(window//3,20))
    mean=s.rolling(window,min_periods=minp).mean()
    sd=s.rolling(window,min_periods=minp).std()
    return (s-mean)/sd.replace(0,np.nan)

def align_pair(a,b,alignment="Auto"):
    if a.empty or b.empty:
        return pd.DataFrame()
    df=pd.concat([a.rename("A"),b.rename("B")],axis=1).sort_index()
    if alignment=="Auto":
        alignment="Native overlap" if len(df.dropna())>=40 else "Monthly"
    if alignment=="Native overlap":
        return df.dropna()
    if alignment=="Daily forward-fill":
        idx=pd.date_range(df.index.min(),df.index.max(),freq="D")
        return df.reindex(idx).ffill().dropna()
    if alignment=="Weekly":
        return df.resample("W-FRI").last().ffill().dropna()
    if alignment=="Monthly":
        return df.resample("ME").last().ffill().dropna()
    if alignment=="Quarterly":
        return df.resample("QE").last().ffill().dropna()
    return df.dropna()

def auto_operation(meta_a,meta_b):
    ua=meta_a.get("unit_type"); ub=meta_b.get("unit_type")
    if ua=="rate_pct" and ub=="rate_pct":
        return "Spread A - B"
    if ua=="pct" and ub=="pct":
        return "Spread A - B"
    if ua in ("price","index") and ub in ("price","index"):
        return "Ratio A / B"
    return "Indexed comparison"

def transform_pair(df,operation):
    if df.empty:
        return pd.DataFrame(),{}
    x=df.copy()
    out=pd.DataFrame(index=x.index)
    stats={}
    if operation=="Ratio A / B":
        out["Composite"]=x["A"]/x["B"].replace(0,np.nan)
        label="A / B"
    elif operation=="Spread A - B":
        out["Composite"]=x["A"]-x["B"]
        label="A - B"
    elif operation=="Spread in basis points":
        out["Composite"]=(x["A"]-x["B"])*100
        label="(A - B) bp"
    elif operation=="Indexed relative strength":
        ia=x["A"]/x["A"].iloc[0]*100
        ib=x["B"]/x["B"].iloc[0]*100
        out["Composite"]=ia/ib*100
        label="Indexed A / B"
    elif operation=="Z-score divergence":
        out["Composite"]=_zscore(x["A"],60)-_zscore(x["B"],60)
        label="Z(A) - Z(B)"
    elif operation=="YoY change spread":
        med=x.index.to_series().diff().dt.days.median() if len(x)>2 else 30
        lag=4 if med and med>60 else (12 if med and med>20 else 252)
        ga=x["A"].pct_change(lag)*100
        gb=x["B"].pct_change(lag)*100
        out["Composite"]=ga-gb
        label="YoY % A - YoY % B"
    else:
        out["A_indexed"]=x["A"]/x["A"].iloc[0]*100
        out["B_indexed"]=x["B"]/x["B"].iloc[0]*100
        label="Indexed 100"

    returns=x.pct_change(fill_method=None)
    out["Corr20"]=returns["A"].rolling(20,min_periods=8).corr(returns["B"])
    if "Composite" in out:
        out["SMA20"]=out["Composite"].rolling(20,min_periods=5).mean()
        out["SMA50"]=out["Composite"].rolling(50,min_periods=10).mean()
        out["Z60"]=_zscore(out["Composite"],60)
        comp=out["Composite"].dropna()
        if len(comp):
            stats["latest"]=float(comp.iloc[-1])
            z=out.loc[comp.index[-1],"Z60"]
            stats["z60"]=None if pd.isna(z) else float(z)
    c=out["Corr20"].dropna()
    stats["corr20"]=float(c.iloc[-1]) if len(c) else None
    stats["label"]=label
    return out,stats
