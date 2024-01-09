import logging

import streamlit as st

from config_mapper import Config
from dkp_app import get_admin_view

log = logging.getLogger(__name__)

log.debug("rendering page")

if st.button("Reload config"):
    log.debug("reloading config")
    config = Config()
    config.reload_config()

report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")

if report_id:
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
