# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import time

import app
import pandas as pd
import streamlit as st
from core import Fix, FixEntry, to_date, to_raw_loot_list


def main():

    # Password protection
    with st.container():
        password = st.text_input("Enter password:", type="password")
        if password != app.get_admin_password():
            st.error("Incorrect password. Access denied.")
            st.stop()


    # Generate config snippet
    with st.container():
        st.header("Raid snippet")
        report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")
        if st.button("Submit WCL report id"):
            view = app.get_admin_view(report_id)
            st.code(
                f"""
            - date: {view.date}
                report: {view.report_url}
                player: {view.player_list}""",
                language="yaml",
            )
            st.markdown("Copy and paste this entry into the raid section of the config.yml file.")


    # Loot upload
    with st.container():
        st.header("Loot upload")
        json_string = st.text_area("Add Loot Log (RCLootCouncil export as JSON):", placeholder='e.g. [{"player":"Moppi-Anub\'Arak", "date":"31/1/24", ...')
        if st.button("Try submit ..."):
            uploaded_log = to_raw_loot_list(json_string)
            raid_day = to_date(uploaded_log[0].date)
            existing_log = app.get_loot_log_raw_for_current_season(raid_day)
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


    # Loot editor
    with st.container():
        st.header("Loot editor")
        raid_day = st.selectbox("Select raid:", sorted([raid.date for raid in app.get_raid_list()], reverse=True))
        loot_log_original = app.get_loot_log_for_current_season(raid_day)  # type: ignore

        data=[loot.model_dump() for loot in loot_log_original]
        columns=[ "id", "character", "note", "response", "item_name", "boss", "difficulty", "instance", "timestamp"]
        dataframe = pd.DataFrame(data, columns=columns).sort_values(by=["id"], ascending=True).set_index("id")

        editor = st.data_editor(dataframe, disabled=["id", "item_name", "boss", "difficulty", "instance", "timestamp"])
        diff = editor.compare(dataframe, keep_shape=False, keep_equal=False, result_names=("fix", "original"))
        if not diff.empty:
            st.write("Changed Loot:")
            st.write(diff)
            reason = st.text_input("Reason for fix:", key="reason", placeholder="e.g. clean up, player traded item, fixed response, ...")

            if st.button("Submit changed Loot"):
                if not reason:
                    st.error("Please provide a reason for the fix.")
                    st.stop()

                app.apply_loot_log_fix(transform_loot_diff(diff), raid_day, reason)  # type: ignore
                st.success("Fix applied." )
                time.sleep(2)  # wait for the message to be displayed
                st.rerun()  # clear streamlit widges responsible for the fix


    # Player editor
    with st.container():
        st.header("New player")

        new_player = st.text_input("Enter new player name:", placeholder="e.g. Jürgen")
        if st.button("Add player"):
            if not new_player:
                st.error("Please enter a name for the new player.")
                st.stop()
            app.add_player(new_player)
            st.success("Player added.")
            time.sleep(2)  # wait for the message to be displayed
            st.rerun()  # realoads the assign button

        new_char = st.text_input("Enter new character name:", placeholder="e.g. Lümmel-Anub'arak")
        selected_player = st.selectbox("Select player:", sorted([player.name for player in app.get_player_list()]))
        if st.button("Add character"):
            if not new_char:
                st.error("Please enter a character name.")
                st.stop()
            if not selected_player:
                st.error("Please select a player.")
                st.stop()
            app.add_player_character(selected_player, new_char)
            st.success("Character assignment saved.")


def transform_loot_diff(diff: pd.DataFrame) -> list[Fix]:
    # drop original values
    if ("character", "original") in diff.columns:
        diff = diff.drop(columns=[("character", "original")])
    if ("note", "original") in diff.columns:
        diff = diff.drop(columns=[("note", "original")])
    if ("response", "original") in diff.columns:
        diff = diff.drop(columns=[("response", "original")])
    # drop the second index used for original and fixed values
    diff = diff.droplevel(1, axis=1)
    # swap columns and rows
    diff = diff.transpose()
    # remove NaN values
    clean_diff = {id: {attr: value for attr, value in fix.items() if pd.notna(value)} for id, fix in diff.to_dict().items()}
    # into data objects
    result = []
    for id, fix_entry in clean_diff.items():
        entries = []
        for name, value in fix_entry.items():
            entry = FixEntry(name=name, value=value)
            entries.append(entry)
        result.append(Fix(id=id, entries=entries)) # type: ignore
    return result


# entry point
main()