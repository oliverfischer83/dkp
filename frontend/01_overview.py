import numpy as np
import pandas as pd
import streamlit as st

st.write("Hello World")

df = pd.read_json("data/example-export.json")

st.write(df)

