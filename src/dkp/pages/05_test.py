import app
import streamlit as st

if st.button("Get zones"):
    app.get_example_zones()


if st.button("Get rate limits"):
    app.get_example_rate_limits()


if st.button("Get report"):
    code = "vF2C8crAdja1QKhD"
    app.get_example_report(code)


if st.button("Get player_details"):
    code = "vF2C8crAdja1QKhD"
    app.get_example_player_details(code)


if st.button("Get debugging report"):
    code = "vF2C8crAdja1QKhD"
    app.get_example_report_debug(code)

