import logging

import pandas as pd
import streamlit as st

from dkp_app import get_balance_view

log = logging.getLogger(__name__)

log.debug("rendering page")
view = get_balance_view()

log.debug("validation")
if view.validations:
    for validation in view.validations:
        st.error(validation)

log.debug("show balance")
st.write("DKP - " + view.season_name)
st.dataframe(
    pd.DataFrame(view.balance, columns=["name", "value", "income", "cost"]).sort_values(by=["name"], ascending=True, ignore_index=True)
)

log.debug("show loot history")
st.write("Loot History")
st.dataframe(
    pd.DataFrame(view.loot_history),
    column_config={
        "itemLink": st.column_config.LinkColumn(
            "item link",
            # display_text="Show item"  # TODO feature coming with streamlit 1.30 (Jan 2024)
        ),
        "timestamp": st.column_config.DateColumn(
            "date",
            format="DD.MM.YYYY",
        ),
    },
)
