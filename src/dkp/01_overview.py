# pylint: disable=missing-module-docstring
import pandas as pd
import streamlit as st
import app


# Season
season_list = sorted(app.get_season_list(), key=lambda season: season.id, reverse=True)
selected_season = st.selectbox("WoW season:", [season.descr for season in season_list], label_visibility="collapsed")
season = next((season for season in season_list if season.descr == selected_season), None)

st.markdown("Letzte Aktualisierung: " + app.get_last_update(season))  # type: ignore

# DKP list
st.markdown("### DKP Übersicht")
st.dataframe(
    pd.DataFrame(app.get_balance(season), columns=["name", "value", "income", "cost", "characters"]).sort_values(   # type: ignore
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
    pd.DataFrame([loot.model_dump() for loot in app.get_loot_history(season)], columns=["timestamp", "player", "note", "item_name", "item_link", "boss", "difficulty", "instance", "character"]).sort_values(  # type: ignore
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
