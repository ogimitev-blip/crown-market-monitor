
import streamlit as st
from crown_monitor.ratio_tools import (
    ASSET_UNIVERSE, PRESETS, build_ratio, key_for_symbol, label_for_symbol
)
from crown_monitor.ratio_charts import (
    ratio_chart, underlying_normalized_chart, correlation_chart
)

st.title("➗ Ratio Lab")
st.caption("Build relative-strength charts from any two assets. Rising ratio = numerator outperforming denominator.")

preset = st.selectbox("Preset", list(PRESETS.keys()), index=1)

labels = list(ASSET_UNIVERSE.keys())

if "ratio_num_label" not in st.session_state:
    st.session_state["ratio_num_label"] = "RSP — S&P 500 Equal Weight"
if "ratio_den_label" not in st.session_state:
    st.session_state["ratio_den_label"] = "SPY — S&P 500"

if preset != "Custom":
    num_sym, den_sym = PRESETS[preset]
    st.session_state["ratio_num_label"] = key_for_symbol(num_sym)
    st.session_state["ratio_den_label"] = key_for_symbol(den_sym)

c1, c2, c3 = st.columns([2,2,1])
num_label = c1.selectbox(
    "Numerator",
    labels,
    index=labels.index(st.session_state["ratio_num_label"])
    if st.session_state["ratio_num_label"] in labels else 0
)
den_label = c2.selectbox(
    "Denominator",
    labels,
    index=labels.index(st.session_state["ratio_den_label"])
    if st.session_state["ratio_den_label"] in labels else 0
)
period = c3.selectbox("Horizon", ["3mo","6mo","1y","2y","5y"], index=2)

st.session_state["ratio_num_label"] = num_label
st.session_state["ratio_den_label"] = den_label

num = ASSET_UNIVERSE[num_label]
den = ASSET_UNIVERSE[den_label]

if num == den:
    st.warning("Choose two different assets.")
    st.stop()

with st.spinner(f"Loading {num} / {den}…"):
    df, stats = build_ratio(num, den, period)

if df.empty:
    st.error("Price data are unavailable for one or both selected assets.")
    st.stop()

a,b,c,d,e = st.columns(5)
a.metric("Ratio", f"{stats['ratio']:.4f}")
b.metric("5D", f"{stats['change_5d']:+.2f}%" if stats["change_5d"] is not None else "N/A")
c.metric("20D", f"{stats['change_20d']:+.2f}%" if stats["change_20d"] is not None else "N/A")
d.metric("60D Z-score", f"{stats['z60']:+.2f}" if stats["z60"] is not None else "N/A")
e.metric("Trend", stats["trend"])

with st.expander("Chart settings", expanded=False):
    s1,s2,s3 = st.columns(3)
    sma20 = s1.checkbox("SMA 20", value=True)
    sma50 = s2.checkbox("SMA 50", value=True)
    sma200 = s3.checkbox("SMA 200", value=False)

title = f"{num_label.split(' — ')[0]} / {den_label.split(' — ')[0]}"
st.plotly_chart(
    ratio_chart(df, title, sma20, sma50, sma200),
    width="stretch",
    config={"displaylogo":False}
)

st.subheader("What drives the ratio?")
left,right = st.columns(2)
with left:
    st.caption("Underlying performance")
    st.plotly_chart(
        underlying_normalized_chart(
            df,
            num_label.split(" — ")[0],
            den_label.split(" — ")[0]
        ),
        width="stretch",
        config={"displaylogo":False}
    )
with right:
    st.caption("20-session return correlation")
    st.plotly_chart(
        correlation_chart(df),
        width="stretch",
        config={"displaylogo":False}
    )

corr = stats.get("corr20")
if corr is not None:
    if abs(corr) < 0.25:
        corr_text = "low recent correlation"
    elif corr > 0.65:
        corr_text = "high positive correlation"
    elif corr < -0.65:
        corr_text = "high negative correlation"
    else:
        corr_text = "moderate correlation"
else:
    corr_text = "correlation unavailable"

z = stats.get("z60")
if z is None:
    z_text = "z-score unavailable"
elif z >= 2:
    z_text = "ratio is >2σ above its 60-day mean"
elif z <= -2:
    z_text = "ratio is >2σ below its 60-day mean"
elif z >= 1:
    z_text = "ratio is elevated versus its 60-day mean"
elif z <= -1:
    z_text = "ratio is depressed versus its 60-day mean"
else:
    z_text = "ratio is near its 60-day mean"

st.info(
    f"**Crown read:** {stats['trend']}. "
    f"20D ratio change {stats['change_20d']:+.2f}% "
    f"and {z_text}; the two underlying assets currently have {corr_text}."
)

st.caption(
    "A ratio is a relative-strength diagnostic, not a standalone trade signal. "
    "Use it with macro cause, breadth, rates, volatility, fundamentals and entry quality."
)
