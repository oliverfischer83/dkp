import streamlit as st
from src.dkp.dkp_app import get_raid_view

report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")

if report_id:
    view = get_raid_view(report_id)

    if view.validations:
        for validation in view.validations:
            st.error(validation)

    st.code(f"""
    - date: {view.date}
      report: {view.report}
      member: {view.player_list}""", language='yaml')
    st.markdown('Copy and paste this entry into the raid section of the config.yml file.')

