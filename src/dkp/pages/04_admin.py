# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import time

import app
import pandas as pd
import streamlit as st
from core import CHANGE, ORIGINAL, Fix, FixEntry, to_date, to_raw_loot_list


def main():

    st.set_page_config(
        page_title='DKP - admin',
        page_icon='🟠',  # see https://twemoji-cheatsheet.vercel.app/
        initial_sidebar_state="expanded")

    st.sidebar.write('###### Version: 0.1.0')

    build_password_protection()
    build_loot_upload()
    build_loot_editor()
    build_player_editor()
    build_raid_editor()
    build_season_editor()


def build_password_protection():
    with st.container():
        password = st.text_input("Enter password:", type="password")
        if password != app.get_admin_password():
            st.error("Incorrect password. Access denied.")
            st.stop()


def build_loot_upload():
    with st.container():
        with st.expander('🟢 Loot upload'):
            json_string = st.text_area("Add Loot Log (RCLootCouncil export as JSON):", placeholder='e.g. [{"player":"Moppi-Anub\'Arak", "date":"31/1/24", ...')
            if st.button("Try submit ..."):
                uploaded_log = to_raw_loot_list(json_string)
                raid_day = to_date(uploaded_log[0].date)
                existing_log = app.get_raid_loot_raw(raid_day)
                new_log = app.filter_logs(existing_log, uploaded_log)
                try:
                    # only validate the new loot, the existing loot in the json export could be invalid and was cleaned up before
                    # only the new loot is stored into the database
                    app.validate_import(new_log)

                    # upload clean logs
                    clean_logs = app.merging_logs(existing_log, new_log)
                    app.upload_loot_log(clean_logs)
                    st.success("Loot log uploaded.")
                except ValueError as e:
                    st.error(f"Validation failed! {str(e)}")


def build_loot_editor():
    with st.container():
        with st.expander('🟡 Loot editor'):
            col1, col2, _, _ = st.columns(4)
            with col1:
                season_list = app.get_season_list_starting_with_current()
                selected_season = st.selectbox("Select season:", [season.name for season in season_list])
                season = next((season for season in app.get_season_list() if season.name == selected_season))
            with col2:
                raid_list = app.get_raid_list(season)
                raid_day = st.selectbox("Select raid:", sorted([raid.date for raid in raid_list], reverse=True))

            if season and raid_day:
                loot_log_original = app.get_raid_loot(raid_day)

                data=[loot.model_dump() for loot in loot_log_original]
                columns=[ "id", "character", "note", "response", "item_name", "boss", "difficulty", "instance", "timestamp"]
                dataframe = pd.DataFrame(data, columns=columns).sort_values(by=["id"], ascending=True).set_index("id")

                editor = st.data_editor(dataframe, disabled=["id", "item_name", "boss", "difficulty", "instance", "timestamp"])
                diff = editor.compare(dataframe, keep_shape=False, keep_equal=False, result_names=(CHANGE, ORIGINAL))
                if not diff.empty:
                    st.write("Changed loot:")
                    st.write(diff)
                    reason = st.text_input("Reason for fix:", key="reason", placeholder="e.g. clean up, player traded item, fixed response, ...")

                    if st.button("Submit changed Loot"):
                        if not reason:
                            st.error("Please provide a reason for the fix.")
                        else:
                            app.apply_fix_to_loot_log(transform(diff), raid_day, reason)
                            st.success("Fix applied." )
                            time.sleep(2)
                            st.rerun()


def build_player_editor():
    with st.container():
        with st.expander('🟠 Player editor'):
            left, right = st.columns(2)
            with left:
                new_player = st.text_input("Enter new player name:", placeholder="e.g. Alfons")
                if st.button("Add player"):
                    if not new_player:
                        st.error("Please enter a name for the new player.")
                    else:
                        app.add_player(new_player)
                        st.success(f"Player added: {new_player}")
                        time.sleep(2)
                        st.rerun()

            with right:
                player_name = st.selectbox("Select player:", sorted([player.name for player in app.get_player_list()]))
                if st.button("Delete player"):
                    if not player_name:
                        st.error("Please select player to remove.")
                    else:
                        app.delete_player(player_name)
                        st.success(f"Player removed: {player_name}")
                        time.sleep(2)
                        st.rerun()

            data=[{"id": player.id, "name": player.name, "chars": ", ".join(player.chars)} for player in app.get_player_list()]
            columns=[ "id", "name", "chars"]
            dataframe = pd.DataFrame(data, columns=columns).sort_values(by=["name"], ascending=True).set_index("id")

            editor = st.data_editor(dataframe, disabled=["id"])
            diff = editor.compare(dataframe, keep_shape=False, keep_equal=False, result_names=(CHANGE, ORIGINAL))
            if not diff.empty:
                st.write("Changed player:")
                st.write(diff)

                if st.button("Submit changed player"):
                    app.update_player(transform(diff))
                    st.success("Player updated." )
                    time.sleep(2)
                    st.rerun()


def build_raid_editor():
    with st.container():
        with st.expander('🔵 Raid editor'):
            report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")
            if st.button("Submit WCL report id"):
                date, report_url, player_list = app.get_raid_entry_for_manual_storage(report_id)
                st.code(
                    f"""
                - date: {date}
                    report: {report_url}
                    player: {player_list}""",
                    language="yaml",
                )
                st.markdown("Copy and paste this entry into the raid section of the config.yml file.")


def build_season_editor():
    with st.container():
        with st.expander('🟣 Season editor'):
            left, right = st.columns(2)
            with left:
                with st.form('season_form'):
                    st.subheader('New season')
                    season_name = st.text_input("Name:", placeholder="e.g. dfs3")
                    season_desc = st.text_input("Description:", placeholder="e.g. Dragonflight - Season 3")
                    season_start = str(st.date_input("Start date:", format="YYYY-MM-DD"))
                    season_add_submitted = st.form_submit_button('Add season')

                if season_add_submitted:
                    if not season_name or not season_desc or not season_start:
                        st.error("Please fill out all fields.")
                    else:
                        app.add_season(season_name, season_desc, season_start)
                        st.success(f"Season added: {season_name} - {season_desc}")
                        time.sleep(2)
                        st.rerun()

            with right:
                selected_season = st.selectbox("Select empty season:", [season.descr for season in app.get_empty_season_list()], index=None)
                if selected_season:
                    season = next((season for season in app.get_season_list() if season.descr == selected_season))

                if st.button('Delete season'):
                    app.delete_season(season)
                    st.success(f"Season deleted: {season.descr}")
                    time.sleep(2)
                    st.rerun()





def transform(diff: pd.DataFrame) -> list[Fix]:
    # drop original values
    for col in diff.columns:
        if col[1] == ORIGINAL:
            diff = diff.drop(columns=[col])
    # drop the second index used for original and fixed values
    diff = diff.droplevel(1, axis=1)
    # swap columns and rows
    diff = diff.transpose()
    # remove NaN values
    # BUG: when deleting cells value also is None and gets removed, effectivly ignoring the change
    clean_diff = {id: {name: value for name, value in entry.items() if pd.notna(value)} for id, entry in diff.to_dict().items()}
    # into data objects
    result = []
    for id, fix_entry in clean_diff.items():
        entries = []
        for name, value in fix_entry.items():
            entry = FixEntry(name=name, value=value)
            entries.append(entry)
        result.append(Fix(id=str(id), entries=entries))
    return result


# entry point
main()