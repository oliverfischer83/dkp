import streamlit as st
import pandas as pd
from src.dkp.dkp_app import get_balance_view

view = get_balance_view()

if view.validations:
    for validation in view.validations:
        st.error(validation)

st.write("DKP - " + view.season_name)
st.dataframe(pd.DataFrame(view.balance, columns=['name', 'balance', "income", "cost"])
             .sort_values(by=['name'], ascending=True, ignore_index=True))

st.write("Loot History")
st.dataframe(pd.DataFrame(view.loot_history), column_config={
    "itemLink": st.column_config.LinkColumn(
        "item link",
        # display_text="Show item"  # TODO feature coming with streamlit 1.30 (Jan 2024)
    ),
    "timestamp": st.column_config.DateColumn(
        "date",
        format="DD.MM.YYYY",
    ),
})
