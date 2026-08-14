import streamlit as st
from crown_monitor.data import load_state_dictionary,load_active_states
st.title("State Explorer")
d=load_state_dictionary(); a=load_active_states()
q=st.text_input("Search states",placeholder="e.g. technical, gold, term premium")
view=d[d.astype(str).apply(lambda c:c.str.contains(q,case=False,na=False)).any(axis=1)] if q else d
st.caption(f"{len(view)} state(s)")
for _,r in view.iterrows():
    cur=a[a["State"]==r["State"]]; status=cur.iloc[0]["Status"] if len(cur) else "INACTIVE / NOT EVALUATED"
    with st.expander(f"{r['State']} — {status}"):
        st.write(r.get("Plain_English_Definition",""))
        st.markdown(f"**Typical trigger:** {r.get('Typical_Trigger','')}")
        st.markdown(f"**Interpretation:** {r.get('How_To_Interpret','')}")
        st.markdown(f"**Portfolio implication:** {r.get('Portfolio_Implication','')}")
        st.markdown(f"**Do not infer:** {r.get('What_Not_To_Infer','')}")
        st.markdown(f"**Key data:** {r.get('Key_Data','')}")
