# pylint: disable=missing-module-docstring
from datetime import date

import app
import pandas as pd
import streamlit as st
from core import Season


def main():

    st.set_page_config(
        page_title='DKP - Punkte',
        page_icon='🟢',  # see https://twemoji-cheatsheet.vercel.app/
        layout="wide",
        initial_sidebar_state="expanded")

    season = build_season_selector()
    build_sidebar(season)
    build_balance(season)
    build_loot_history(season)



def build_season_selector() -> Season:
    col_1, _, _ = st.columns(3)
    with col_1:
        season_list = app.get_season_list_starting_with_current()
        selected_season = st.selectbox("WoW season:", [season.descr for season in season_list], label_visibility="collapsed")
        season = next((season for season in season_list if season.descr == selected_season))
    return season


def build_sidebar(season: Season):
    timestamp, boss, difficulty = app.get_info_last_update(season)
    timestamp = pd.to_datetime(timestamp)
    if timestamp.date() == date.today():
        timestamp = f"Heute, {timestamp.strftime("%H:%M")} Uhr"
    else:
        timestamp = f"{timestamp.strftime("%d.%m.%Y, %H:%M")} Uhr"
    st.sidebar.markdown(f'#### Letzte Änderung:\n- {timestamp}\n- {boss} ({difficulty})')


def build_balance(season: Season):
    st.markdown("### DKP Liste")
    st.dataframe(
        pd.DataFrame(app.get_balance(season), columns=["name", "value", "income", "cost", "characters"]).sort_values(
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

def build_loot_history(season: Season):
    st.markdown("### Loot Liste")
    st.dataframe(
        pd.DataFrame([loot.model_dump() for loot in app.get_loot_history(season)], columns=["timestamp", "player", "note", "item_name", "item_link", "boss", "difficulty", "instance", "character"]).sort_values(
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


# entry point
main()
