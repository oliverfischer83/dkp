import streamlit as st

from src.dkp.dkp_app import get_raid

report_id = st.text_input("Enter warcraftlogs report id:", placeholder="e.g. JrYPGF9D1yLqtZhd")

if report_id:
    raid = get_raid(report_id)
    st.code(f"""
    - date: {raid.date}
      report: {raid.report}
      member: {raid.member_list}""", language='yaml')
    st.markdown('Copy and paste this entry into the raid section of the config.yml file.')

