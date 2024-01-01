"""
Business logic for the DKP webapp.
"""
import datetime
import os
import pandas
from typing import Optional
from pydantic import BaseModel
from .warcraftlogs_client import WclClient
from dataclasses import dataclass
from .config_mapper import Player, Config


INITIAL_BALANCE = 100
ATTENDANCE_BONUS = 50


@dataclass
class AdminView:
    date: str
    report: str
    player_list: list[str]
    validations: list[str]


@dataclass
class Balance:
    player: Player
    value: int = INITIAL_BALANCE
    income: int = INITIAL_BALANCE
    cost: int = 0


class LootHistory(BaseModel):
    timestamp: datetime.datetime
    player: str
    cost: str
    item: str
    instance: str
    difficulty: str
    boss: str
    character: str


class BalanceView(BaseModel):
    season_name: str
    balance: pandas.DataFrame
    loot_history: pandas.DataFrame
    validations: list[str]


def get_raw_data_from_files(export_dir):
    result = pandas.DataFrame()
    for file in os.listdir(export_dir):
        dataframe = pandas.read_json(os.path.join(export_dir, file), orient='records', dtype='str', convert_dates=False)
        result = pandas.concat([result, dataframe])
    return result


def make_clickable(val):
    return '<a href="{}">{}</a>'.format(val, val)


def modify_data(dataframe, player_list):
    result = dataframe.copy()
    # remove irrelevant data, need bids only
    result = result[result['response'] == 'Gebot']
    # creating timestamp column
    result['timestamp'] = result['date'] + ' ' + result['time']
    result['timestamp'] = pandas.to_datetime(result['timestamp'], format='%d/%m/%y %H:%M:%S', dayfirst=True)
    result.set_index('timestamp')
    # creating item link column
    result['itemLink'] = 'https://www.wowhead.com/item=' + result['itemID']
    result.style.format({'itemLink': make_clickable})
    # renaming columns
    result = result.rename(columns={'player': 'character'})
    result = result.rename(columns={'itemName': 'item'})
    result = result.rename(columns={'note': 'cost'})
    # create and fill column 'player' using mapping table like {'Moppi': 'Olli', 'Zelma': 'Olli', ...}
    result['player'] = result['character'].map(
        lambda x: next((player.name for player in player_list if x in player.chars), None))
    # create difficulty column
    result['difficulty'] = result['instance'].str.split('-').str[1]
    # substring of instance name
    result['instance'] = result['instance'].str.split(',').str[0]
    # select and sort columns
    result = result[["timestamp", "player", "cost", "item", "itemLink", "instance", "difficulty", "boss", "character"]]
    result = result.sort_values(by=['timestamp'], ascending=False, ignore_index=True)
    return result.to_dict()


def get_loot_from_local_files(season_key, player_list):
    raw_data = get_raw_data_from_files(os.path.join('data', 'season', season_key))
    return modify_data(raw_data, player_list)


def get_balance(player_list, raid_list, loot):
    # init balance list
    balance_list = list()
    for player in player_list:
        balance_list.append(Balance(player))

    # add income
    for raid in raid_list:
        for player in raid.player:
            for balance in balance_list:
                if player == balance.player.name:
                    balance.value = balance.value + ATTENDANCE_BONUS
                    balance.income = balance.income + ATTENDANCE_BONUS

    # subtract costs
    for index, row in loot.iterrows():
        char = row['character']
        cost = row['cost']
        for balance in balance_list:
            if char in balance.player.chars:
                balance.value = balance.value - int(cost)
                balance.cost = balance.cost - int(cost)

    balance_list_as_df = [[balance.player.name, balance.value, balance.income, balance.cost] for balance in
                          balance_list]
    return (pandas.DataFrame(balance_list_as_df, columns=['name', 'balance', "income", "cost"])
            .sort_values(by=['name'], ascending=True, ignore_index=True))


def validate_characters_known(known_player, looting_characters):
    known_characters = list()
    for player in known_player:
        for char in player.chars:
            known_characters.append(char)

    result = []
    for char in looting_characters:
        if char not in known_characters:
            result.append("Unknown character: " + char)
    return result


def validate_costs(cost_list):
    result = []
    for cost in cost_list:
        try:
            int(cost)
        except ValueError:
            result.append("Cost must be an integer, but was: " + cost)
            continue
        if int(cost) < 10:
            result.append("Cost minimum is 10, but was: " + cost)
            continue
        if int(cost) % 10 != 0:
            result.append("Cost must be within steps of 10, but was: " + cost)
            continue
    return result


def get_balance_view():
    config = Config()

    season_name = config.season.name
    player_list = config.player_list
    loot = get_loot_from_local_files(config.season.key, player_list)
    looting_characters = list(set([value for value in loot['character'].values()]))

    validations = []
    validations.extend(validate_characters_known(player_list, looting_characters))
    validations.extend(validate_costs(loot['cost'].values()))

    if validations:
        return BalanceView(season_name, None, None, validations)

    balance = get_balance(player_list, config.raid_list, loot[["character", "cost"]])

    return BalanceView(season_name, balance, loot, None)


def get_admin_view(report_id):
    config = Config()

    wcl_client = WclClient(config.auth.wcl_client)
    date, report_link, raiding_char_list = wcl_client.get_raid_details(report_id)

    player_list = []
    for player in config.player_list:
        for char in raiding_char_list:
            if char in player.chars:
                player_list.append(player.name)
                break

    validations = []
    validations.extend(validate_characters_known(config.player_list, raiding_char_list))

    if validations:
        return AdminView(date, report_link, None, validations)

    return AdminView(date, report_link, player_list, None)
