# pylint: disable=missing-module-docstring
import pandas as pd
import streamlit as st
import app


view = app.get_balance_view()

# Season
seasons = [season.descr for season in sorted(app.get_season_list(), key=lambda season: season.id, reverse=True)]
season = st.selectbox("WoW Season:", seasons)

st.markdown("# " + view.season_descr)
st.markdown("Letzte Aktualisierung: " + view.last_update)

# DKP list
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
    hide_index=True,
)

# Loot history
st.markdown("### Loot Liste")
st.dataframe(
    pd.DataFrame([loot.model_dump() for loot in view.loot_history], columns=["timestamp", "player", "note", "item_name", "item_link", "boss", "difficulty", "instance", "character"]).sort_values(
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
    hide_index=True,
)
