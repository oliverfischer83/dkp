# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import time

import app
import pandas as pd
import streamlit as st
from core import CHANGE, ORIGINAL, Fix, FixEntry, to_date, to_raw_loot_list


def main():

    st.set_page_config(
        page_title="DKP - admin", page_icon="🧑‍💻", initial_sidebar_state="expanded"  # see https://twemoji-cheatsheet.vercel.app/
    )


    build_password_protection()
    build_sidebar()
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


def build_sidebar():

    with st.sidebar:

        # raid start/stop
        col1, col2 = st.columns(2)
        with col1:
            st.button("Start Raid")
        with col2:
            st.button("Stop Raid")

        # checklist
        if True: # TODO app.is_raid_started():
            checklist = app.get_raid_checklist()
            symbol = "🟢" if checklist.is_fullfilled() else "🔴"
            st.markdown(f"#### Status: {symbol}")
            st.checkbox("Aufnahme läuft", on_change=update_raid_checklist, key='video', args=('video',), value=checklist.video_recording)
            st.checkbox("Warcraft Logs aktiviert", on_change=update_raid_checklist, key='logs', args=('logs',), value=checklist.logs_recording)
            st.checkbox("RCLootCouncil installiert", on_change=update_raid_checklist, key='addon', args=('addon',), value=checklist.rclc_installed)
            st.checkbox("Kessel, Pots, Vantus Runen", on_change=update_raid_checklist, key='consum', args=('consum',), value=checklist.consumables)

        # version
        st.write("")
        st.write("")
        st.write("")
        st.write("###### Version: 0.1.0")


def build_loot_upload():
    with st.container():
        with st.expander("🇺pload"):
            json_string = st.text_area(
                "Add Loot Log (RCLootCouncil export as JSON):", placeholder='e.g. [{"player":"Moppi-Anub\'Arak", "date":"31/1/24", ...'
            )
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
        with st.expander("🇱oot editor"):
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

                data = [loot.model_dump() for loot in loot_log_original]
                columns = ["id", "character", "note", "response", "item_name", "boss", "difficulty", "instance", "timestamp"]
                dataframe = pd.DataFrame(data, columns=columns).sort_values(by=["id"], ascending=True).set_index("id")

                editor = st.data_editor(dataframe, disabled=["id", "item_name", "boss", "difficulty", "instance", "timestamp"])
                diff = editor.compare(dataframe, keep_shape=False, keep_equal=False, result_names=(CHANGE, ORIGINAL))
                if not diff.empty:
                    st.write("Changed loot:")
                    st.write(diff)
                    reason = st.text_input(
                        "Reason for fix:", key="reason", placeholder="e.g. clean up, player traded item, fixed response, ..."
                    )

                    if st.button("Submit changed Loot"):
                        if not reason:
                            st.error("Please provide a reason for the fix.")
                        else:
                            app.apply_fix_to_loot_log(transform(diff), raid_day, reason)
                            st.success("Fix applied.")
                            time.sleep(2)
                            st.rerun()


def build_player_editor():
    with st.container():
        with st.expander("🇵layer editor"):
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
                player_name = st.selectbox("Select absent player:", sorted([player.name for player in app.get_absent_player_list()]))
                if st.button("Delete player"):
                    if not player_name:
                        st.error("Please select player to remove.")
                    else:
                        app.delete_player(player_name)
                        st.success(f"Player removed: {player_name}")
                        time.sleep(2)
                        st.rerun()

            data = [{"id": player.id, "name": player.name, "chars": ", ".join(player.chars)} for player in app.get_player_list()]
            columns = ["id", "name", "chars"]
            dataframe = pd.DataFrame(data, columns=columns).sort_values(by=["name"], ascending=True).set_index("id")

            editor = st.data_editor(dataframe, disabled=["id"])
            diff = editor.compare(dataframe, keep_shape=False, keep_equal=False, result_names=(CHANGE, ORIGINAL))
            if not diff.empty:
                st.write("Changed player:")
                st.write(diff)

                if st.button("Submit changed player"):
                    app.update_player(transform(diff))
                    st.success("Player updated.")
                    time.sleep(2)
                    st.rerun()


def build_raid_editor():
    with st.container():
        with st.expander("🇷aid editor"):
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
        with st.expander("🇸eason editor"):
            left, right = st.columns(2)
            with left:
                season_name = st.text_input("Name:", placeholder="e.g. dfs3")
                if st.button("Add season"):
                    if not season_name:
                        st.error("Please enter new season name.")
                    else:
                        app.add_season(season_name)
                        st.success(f"Season added: {season_name}")
                        time.sleep(2)
                        st.rerun()

            with right:
                selected_season = st.selectbox("Select empty season:", [season.desc for season in app.get_empty_season_list()], index=None)
                if selected_season:
                    season = next((season for season in app.get_season_list() if season.desc == selected_season))

                if st.button("Delete season"):
                    app.delete_season(season)
                    st.success(f"Season deleted: {season.desc}")
                    time.sleep(2)
                    st.rerun()

            data = [
                {
                    "id": season.id,
                    "name": season.name,
                    "desc": season.desc,
                    "start_date": season.start_date
                }
                for season in app.get_season_list()
            ]
            columns = ["id", "name", "desc", "start_date"]
            dataframe = pd.DataFrame(data, columns=columns).sort_values(by=["start_date"], ascending=True).set_index("id")

            editor = st.data_editor(dataframe, disabled=["id"])
            diff = editor.compare(dataframe, keep_shape=False, keep_equal=False, result_names=(CHANGE, ORIGINAL))
            if not diff.empty:
                st.write("Changed season:")
                st.write(diff)

                if st.button("Submit changed season"):
                    app.update_season(transform(diff))
                    st.success("Player updated.")
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
    for fix_id, fix_entry in clean_diff.items():
        entries = []
        for name, value in fix_entry.items():
            entry = FixEntry(name=name, value=value)
            entries.append(entry)
        result.append(Fix(id=str(fix_id), entries=entries))
    return result


def update_raid_checklist(key_name: str):
    value = st.session_state.get(key_name, False)
    checklist = app.get_raid_checklist()
    if key_name == 'video':
        checklist.video_recording = value
    elif key_name == 'logs':
        checklist.logs_recording = value
    elif key_name == 'addon':
        checklist.rclc_installed = value
    elif key_name == 'consum':
        checklist.consumables = value
    app.update_raid_checklist(checklist)


# entry point
main()
