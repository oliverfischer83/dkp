import streamlit as st
from src.dkp.dkp_app import get_view

view = get_view()

if view.validations:
    for validation in view.validations:
        st.error(validation)

st.write("DKP - " + view.season_name)
st.write(view.balance)

st.write("Loot History")
st.write(view.loot_history)
