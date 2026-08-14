import streamlit as st
from crown_monitor.data import load_cross_asset
st.title("Cross-Asset")
st.caption("Expected response vs observed response")
df=load_cross_asset(); st.dataframe(df,width="stretch",hide_index=True)
div=df[df["Verdict"].str.contains("Divergence",case=False,na=False)]
if len(div):
    st.warning(f"{len(div)} important divergence(s) detected.")
    for _,r in div.iterrows(): st.write(f"**{r['Asset']}** — expected {r['Expected']}, observed {r['Observed']}")
