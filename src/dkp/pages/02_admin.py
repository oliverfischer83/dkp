# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import logging
import time

import pandas as pd
import streamlit as st
from app import get_admin_view
import app

log = logging.getLogger(__name__)


# Password protection
password = st.text_input("Enter password:", type="password")
if password != app.get_admin_password():
    st.error("Incorrect password. Access denied.")
    st.stop()


# Generate config snippet
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

# Loot Log upload
export_ta_label = "Add Loot Log for current active raid (RCLootCouncil export as JSON):"
export_ta_key = "rclc_export"

session_state = st.session_state
if 'textarea_value' not in session_state:
    session_state.textarea_value = ""

# TODO use session_state or remove it
json_string = st.text_area(export_ta_label, value=session_state.textarea_value, key=export_ta_key, placeholder='e.g. [{"player":"Moppi-Anub\'Arak", "date":"31/1/24", ...')
if st.button("Submit LootCouncil export"):
    try:
        app.update_or_create_loot_log(json_string)
        st.success("Loot log uploaded.")
        session_state.textarea_value = "" # clear text area
    except Exception as e:
        st.error(f"Loot log uploaded failed: {str(e)}")

# Loot log changes
raid_day = st.date_input("Show Loot Log of Raid day:", value=datetime.date.today(), format="YYYY-MM-DD").strftime("%Y-%m-%d")  # type: ignore
loot_log_original = app.get_loot_log(raid_day)

# TODO unify the dataframes
log.debug("show loot log of raid day")
## TODO: disable not editable columns
loot_log_modified_df = st.data_editor(
    pd.DataFrame([loot.model_dump() for loot in loot_log_original], columns=[ "id", "character", "note", "response", "item_name", "boss", "difficulty", "instance", "timestamp"])
    .sort_values(by=["id"], ascending=True)
    .set_index("id"),
)

changed_lines = loot_log_modified_df.compare(
    pd.DataFrame([loot.model_dump() for loot in loot_log_original], columns=[ "id", "character", "note", "response", "item_name", "boss", "difficulty", "instance", "timestamp"])
    .sort_values(by=["id"], ascending=True)
    .set_index("id"),
    keep_shape=False,
    keep_equal=False,
    result_names=("fix", "original")
)

if not changed_lines.empty:
    st.write("Changes:")
    st.write(changed_lines)

    reason = st.text_input("Reason for fix:", key="reason")

    if st.button("Submit Changes"):

        if not reason:
            st.error("Please provide a reason for the fix.")
            st.stop()

        fix_df = changed_lines
        if ("character", "original") in fix_df.columns:
            fix_df = fix_df.drop(columns=[("character", "original")])
        if ("note", "original") in fix_df.columns:
            fix_df = fix_df.drop(columns=[("note", "original")])
        if ("response", "original") in fix_df.columns:
            fix_df = fix_df.drop(columns=[("response", "original")]) # drop original values
        fix_df = fix_df.droplevel(1, axis=1) # drop the second index used for original and fixed values
        fix_df_transposed = fix_df.transpose() # swap columns and rows
        result = fix_df_transposed.to_dict()
        result = {id: {attr: value for attr, value in fix.items() if pd.notna(value)} for id, fix in result.items()} # remove NaN values
        app.apply_loot_log_fix(result, raid_day, reason)  # type: ignore  # TODO add reason
        st.success("Fix applied." )
        time.sleep(2)  # wait for the message to be displayed
        st.rerun()  # clear streamlit widges responsible for the fix

