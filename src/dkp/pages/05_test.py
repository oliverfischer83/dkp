import streamlit as st

import app



if st.button('Get zones'):
    app.get_zones()


if st.button('Get rate limits'):
    app.get_rate_limits()


if st.button('Get report'):
    code = "vF2C8crAdja1QKhD"
    app.get_report(code)


if st.button('Get player_details'):
    code = "vF2C8crAdja1QKhD"
    app.get_player_details(code)
