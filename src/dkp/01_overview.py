# pylint: disable=missing-module-docstring
import logging

import pandas as pd
import streamlit as st

from app import get_balance_view

log = logging.getLogger(__name__)

log.debug("rendering page")
view = get_balance_view()

log.debug("validation")
if view.validations:
    for validation in view.validations:
        st.error(validation)

# Balance
log.debug("show balance")
st.markdown("# " + view.season_name)
st.markdown("Letzte Aktualisierung: " + view.last_update)
st.markdown("### DKP Liste")
st.dataframe(
    pd.DataFrame(view.balance, columns=["name", "value", "income", "cost", "characters"]).sort_values(
        by=["name"], ascending=True, ignore_index=False
    ),
    column_config={
        "name": "Spieler",
        "value": "Guthaben",
        "income": "verdient",
        "cost": "ausgegeben",
        "characters": "Charaktere",
    },
    # hide_index=True,
)

# Loot history
log.debug("show loot history")
st.markdown("### Loot Liste")
st.dataframe(
    pd.DataFrame(view.loot_history, columns=["timestamp", "player", "note", "item_name", "item_link", "boss", "difficulty", "instance", "character"]).sort_values(
        by=["timestamp"], ascending=False, ignore_index=False
    ),
    column_config={
        "timestamp": st.column_config.DateColumn(
            "Datum",
            format="DD.MM.YYYY",
        ),
        "player": "Spieler",
        "note": "Gebot",
        "item_name": "Item",
        "item_link": st.column_config.LinkColumn(
            "Item Link",
            display_text="wowhead.com"
        ),
        "boss": "Boss",
        "difficulty": "Stufe",
        "instance": "Raid",
        "character": "Charakter",
    },
    # hide_index=True,
)
