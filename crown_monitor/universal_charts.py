
from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def comparison_chart(transformed,title,operation):
    if transformed is None or transformed.empty:
        return go.Figure()
    has_composite="Composite" in transformed.columns
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.76,0.24],vertical_spacing=0.04)

    if has_composite:
        fig.add_trace(go.Scatter(x=transformed.index,y=transformed["Composite"],mode="lines",name="Composite"),row=1,col=1)
        if "SMA20" in transformed:
            fig.add_trace(go.Scatter(x=transformed.index,y=transformed["SMA20"],mode="lines",name="SMA20"),row=1,col=1)
        if "SMA50" in transformed:
            fig.add_trace(go.Scatter(x=transformed.index,y=transformed["SMA50"],mode="lines",name="SMA50"),row=1,col=1)
        if "Z60" in transformed:
            fig.add_trace(go.Scatter(x=transformed.index,y=transformed["Z60"],mode="lines",name="Z60"),row=2,col=1)
            fig.add_hline(y=0,row=2,col=1,line_dash="dot")
            fig.add_hline(y=2,row=2,col=1,line_dash="dot")
            fig.add_hline(y=-2,row=2,col=1,line_dash="dot")
    else:
        fig.add_trace(go.Scatter(x=transformed.index,y=transformed["A_indexed"],mode="lines",name="A"),row=1,col=1)
        fig.add_trace(go.Scatter(x=transformed.index,y=transformed["B_indexed"],mode="lines",name="B"),row=1,col=1)
        fig.add_trace(go.Scatter(x=transformed.index,y=transformed["Corr20"],mode="lines",name="Corr20"),row=2,col=1)
        fig.add_hline(y=0,row=2,col=1,line_dash="dot")

    fig.update_layout(title=title,height=670,margin=dict(l=10,r=10,t=50,b=10),legend_orientation="h",legend_y=1.02)
    return fig

def raw_pair_chart(df,label_a,label_b):
    fig=go.Figure()
    if df is None or df.empty:
        return fig
    a=df["A"]/df["A"].iloc[0]*100
    b=df["B"]/df["B"].iloc[0]*100
    fig.add_trace(go.Scatter(x=df.index,y=a,mode="lines",name=label_a))
    fig.add_trace(go.Scatter(x=df.index,y=b,mode="lines",name=label_b))
    fig.add_hline(y=100,line_dash="dot")
    fig.update_layout(height=420,margin=dict(l=10,r=10,t=35,b=10),yaxis_title="Indexed = 100",legend_orientation="h",legend_y=1.02)
    return fig

def single_series_chart(series,title):
    fig=go.Figure()
    if series is not None and not series.empty:
        fig.add_trace(go.Scatter(x=series.index,y=series.values,mode="lines",name=title))
    fig.update_layout(height=460,margin=dict(l=10,r=10,t=45,b=10),title=title)
    return fig
