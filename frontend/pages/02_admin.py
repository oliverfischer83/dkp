import streamlit as st
from src.dkp.dkp_app import get_admin_view
from src.dkp.config_mapper import Config


if st.button("Reload config"):
    config = Config()
    config.reload_config()


report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")

if report_id:
    view = get_admin_view(report_id)

    if view.validations:
        for validation in view.validations:
            st.error(validation)

    st.code(f"""
    - date: {view.date}
      report: {view.report}
      player: {view.player}""", language='yaml')
    st.markdown('Copy and paste this entry into the raid section of the config.yml file.')

