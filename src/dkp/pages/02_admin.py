# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import logging
import os

import streamlit as st
from app import get_admin_view
import app

log = logging.getLogger(__name__)
EXPECTED_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


def _main():
    log.debug("_main")

    # Password protection
    password = st.text_input("Enter password:", type="password")
    if password != EXPECTED_PASSWORD:
        st.error("Incorrect password. Access denied.")
        st.stop()

    # Reload config
    if st.button("Reload config"):
        log.debug("reloading config")
        app.reload_config()

    # Generate config snippet
    report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")
    if st.button("Submit WCL report id:"):
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

    json_string = st.text_area(export_ta_label, value=session_state.textarea_value, key=export_ta_key, placeholder='e.g. [{"player":"Moppi-Anub\'Arak", "date":"31/1/24", ...')
    if st.button("Submit LootCouncil export"):
        try:
            app.upload_loot_log(json_string)
            st.success("Loot log uploaded.")
            session_state.textarea_value = "" # clear text area
        except Exception as e:
            st.error(f"Loot log uploaded failed: {str(e)}")

# entry point
_main()
