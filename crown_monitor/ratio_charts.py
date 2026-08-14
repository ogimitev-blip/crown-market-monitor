
from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def ratio_chart(df, title, show_sma20=True, show_sma50=True, show_sma200=False):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.76, 0.24], vertical_spacing=0.04
    )

    fig.add_trace(
        go.Scatter(x=df.index, y=df["Ratio"], mode="lines", name="Ratio"),
        row=1, col=1
    )

    if show_sma20:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA20"], mode="lines", name="SMA 20"),
            row=1, col=1
        )
    if show_sma50:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA50"], mode="lines", name="SMA 50"),
            row=1, col=1
        )
    if show_sma200:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["SMA200"], mode="lines", name="SMA 200"),
            row=1, col=1
        )

    fig.add_trace(
        go.Scatter(x=df.index, y=df["Z60"], mode="lines", name="60D z-score"),
        row=2, col=1
    )
    fig.add_hline(y=0, row=2, col=1, line_dash="dot")
    fig.add_hline(y=2, row=2, col=1, line_dash="dot")
    fig.add_hline(y=-2, row=2, col=1, line_dash="dot")

    fig.update_layout(
        title=title,
        height=670,
        margin=dict(l=10, r=10, t=50, b=10),
        legend_orientation="h",
        legend_y=1.02
    )
    fig.update_yaxes(title_text="Ratio", row=1, col=1)
    fig.update_yaxes(title_text="Z60", row=2, col=1)
    return fig

def underlying_normalized_chart(df, numerator_label, denominator_label):
    norm = df[["Numerator","Denominator"]].copy()
    norm = norm / norm.iloc[0] * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=norm.index, y=norm["Numerator"],
        mode="lines", name=numerator_label
    ))
    fig.add_trace(go.Scatter(
        x=norm.index, y=norm["Denominator"],
        mode="lines", name=denominator_label
    ))
    fig.add_hline(y=100, line_dash="dot")
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=35, b=10),
        yaxis_title="Normalized = 100",
        legend_orientation="h",
        legend_y=1.02
    )
    return fig

def correlation_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Corr20"],
        mode="lines", name="20D return correlation"
    ))
    fig.add_hline(y=0, line_dash="dot")
    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=35, b=10),
        yaxis_title="Correlation",
        yaxis_range=[-1,1]
    )
    return fig
