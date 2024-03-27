# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import logging
import time

import pandas as pd
import streamlit as st
from app import get_admin_view
import app

log = logging.getLogger(__name__)


def main():

    # Password protection
    with st.container():
        password = st.text_input("Enter password:", type="password")
        if password != app.get_admin_password():
            st.error("Incorrect password. Access denied.")
            st.stop()


    # Generate config snippet
    with st.container():
        report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")
        if st.button("Submit WCL report id"):
            log.debug("generate config snippet")
            view = get_admin_view(report_id)
            log.debug("validate")
            if view.validations:
                for validation in view.validations:
                    st.error(validation)
            log.debug("show config snippet")
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
        json_string = st.text_area("Add Loot Log for current active raid (RCLootCouncil export as JSON):",
                                placeholder='e.g. [{"player":"Moppi-Anub\'Arak", "date":"31/1/24", ...')

        if st.button("Try submit ..."):
            try:
                app.update_or_create_loot_log(json_string)
                st.success("Loot log uploaded.")
            except Exception as e:
                st.error(f"Loot log uploaded failed: {str(e)}")


    # Loot explorer
    with st.container():
        raid_day = st.date_input("Show Loot Log of Raid day:", value=datetime.date.today(), format="YYYY-MM-DD").strftime("%Y-%m-%d")  # type: ignore
        loot_log_original = app.get_loot_log(raid_day)

        data=[loot.model_dump() for loot in loot_log_original]
        columns=[ "id", "character", "note", "response", "item_name", "boss", "difficulty", "instance", "timestamp"]
        dataframe = pd.DataFrame(data, columns=columns).sort_values(by=["id"], ascending=True).set_index("id")

        editor = st.data_editor(dataframe, disabled=["id", "item_name", "boss", "difficulty", "instance", "timestamp"])
        diff = editor.compare(dataframe, keep_shape=False, keep_equal=False, result_names=("fix", "original"))
        if not diff.empty:
            st.write("Changes:")
            st.write(diff)
            reason = st.text_input("Reason for fix:", key="reason")

            if st.button("Submit Changes"):
                if not reason:
                    st.error("Please provide a reason for the fix.")
                    st.stop()

                result = transform(diff)
                app.apply_loot_log_fix(result, raid_day, reason)  # type: ignore
                st.success("Fix applied." )
                time.sleep(2)  # wait for the message to be displayed
                st.rerun()  # clear streamlit widges responsible for the fix




def transform(diff: pd.DataFrame) -> dict[str, dict[str, str]]:
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
    result = {id: {attr: value for attr, value in fix.items() if pd.notna(value)} for id, fix in diff.to_dict().items()}
    return result  # type: ignore


# entry point
main()