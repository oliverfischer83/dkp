import os

import numpy as np
import pandas as pd
import streamlit as st
import yaml

with open('data/config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

st.write("DKP - " + config['season']['name'])

export_dir = os.path.join('data', 'season', config['season']['key'], 'lootcouncil-export')
for file in os.listdir(export_dir):
    json = pd.read_json(os.path.join(export_dir, file))
    filteredColumns = json[["player", "date", "time", "instance", "boss", "itemName", "note"]]
    st.write(filteredColumns)








