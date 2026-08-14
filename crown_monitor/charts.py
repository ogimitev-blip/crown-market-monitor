
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from crown_monitor.market_tools import add_indicators

def instrument_chart(df, ticker, overlays, levels=None):
    x=add_indicators(df)
    fig=make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.77,0.23], vertical_spacing=0.04
    )
    fig.add_trace(go.Candlestick(
        x=x.index,open=x["Open"],high=x["High"],low=x["Low"],close=x["Close"],
        name=ticker
    ),row=1,col=1)

    for n in [20,50,100,200]:
        k=f"SMA{n}"
        if f"SMA {n}" in overlays and k in x:
            fig.add_trace(go.Scatter(x=x.index,y=x[k],mode="lines",name=f"SMA {n}"),row=1,col=1)

    if "VWAP 20" in overlays and "VWAP20" in x:
        fig.add_trace(go.Scatter(x=x.index,y=x["VWAP20"],mode="lines",name="VWAP20"),row=1,col=1)
    if "SuperTrend" in overlays and "SuperTrend" in x:
        fig.add_trace(go.Scatter(x=x.index,y=x["SuperTrend"],mode="lines",name="SuperTrend"),row=1,col=1)
    if "Ichimoku" in overlays:
        fig.add_trace(go.Scatter(x=x.index,y=x["Tenkan"],mode="lines",name="Tenkan"),row=1,col=1)
        fig.add_trace(go.Scatter(x=x.index,y=x["Kijun"],mode="lines",name="Kijun"),row=1,col=1)

    fig.add_trace(go.Scatter(x=x.index,y=x["RSI14"],mode="lines",name="RSI14"),row=2,col=1)
    fig.add_hline(y=70,row=2,col=1,line_dash="dot")
    fig.add_hline(y=30,row=2,col=1,line_dash="dot")

    if levels:
        for label,val in levels.items():
            try:
                val=float(val)
            except Exception:
                continue
            fig.add_hline(y=val,row=1,col=1,line_dash="dash",annotation_text=label)

    fig.update_layout(
        height=680,margin=dict(l=10,r=10,t=40,b=10),
        xaxis_rangeslider_visible=False,
        legend_orientation="h",legend_y=1.02
    )
    fig.update_yaxes(title_text="Price",row=1,col=1)
    fig.update_yaxes(title_text="RSI",range=[0,100],row=2,col=1)
    return fig

def normalized_chart(px, display_names=None):
    fig=go.Figure()
    if px is None or px.empty:
        return fig
    for c in px.columns:
        name=display_names.get(c,c) if display_names else c
        fig.add_trace(go.Scatter(x=px.index,y=px[c],mode="lines",name=name))
    fig.add_hline(y=100,line_dash="dot")
    fig.update_layout(
        height=500,margin=dict(l=10,r=10,t=35,b=10),
        yaxis_title="Normalized = 100",legend_orientation="h",legend_y=1.02
    )
    return fig

def corr_chart(corr, display_names=None):
    fig=go.Figure()
    if corr is None or corr.empty:
        return fig
    for c in corr.columns:
        name=display_names.get(c,c) if display_names else c
        fig.add_trace(go.Scatter(x=corr.index,y=corr[c],mode="lines",name=name))
    fig.add_hline(y=0,line_dash="dot")
    fig.update_layout(
        height=420,margin=dict(l=10,r=10,t=35,b=10),
        yaxis_title="Rolling correlation",yaxis_range=[-1,1],
        legend_orientation="h",legend_y=1.02
    )
    return fig
