import os

import pandas as pd
import streamlit as st
import yaml

with open('data/config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

all_player = config['player']
all_loot = pd.DataFrame()
export_dir = os.path.join('data', 'season', config['season']['key'], 'lootcouncil-export')
for file in os.listdir(export_dir):
    dataframe = pd.read_json(os.path.join(export_dir, file), orient='records', dtype='str')
    dataframe['timestamp'] = dataframe['date'] + ' ' + dataframe['time']
    dataframe = dataframe[["timestamp", "player", "itemName", "note", "instance", "boss"]]
    dataframe.set_index('timestamp')
    all_loot = pd.concat([all_loot, dataframe])

all_loot.rename(columns={'itemName': 'item'}, inplace=True)
all_loot.rename(columns={'note': 'cost'}, inplace=True)
all_loot = all_loot.sort_values(by=['timestamp'], ascending=False, ignore_index=True)

# TODO show error message if player unknown


def init_balance():
    balance = {}
    for player in all_player:
        balance[player] = 100
    return balance


st.write("DKP - " + config['season']['name'])
balance = pd.DataFrame(list(init_balance().items()), columns=['name', 'points']).set_index('name')
st.write(balance)

st.write("Loot History")
st.write(all_loot)


