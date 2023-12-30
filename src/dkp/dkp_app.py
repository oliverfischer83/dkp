"""
Business logic for the DKP webapp.
"""
import os
import pandas
from . import config_mapper
from .warcraftlogs_client import WclClient

INITIAL_BALANCE = 100
ATTENDANCE_BONUS = 50

config = config_mapper.get_config()


class AdminView:
    def __init__(self, date, report, player_list, validations):
        self.date = date
        self.report = report
        self.player_list = player_list
        self.validations = validations


class Loot:
    def __init__(self, timestamp, player, item, cost, instance, boss):
        self.timestamp = timestamp
        self.player = player
        self.item = item
        self.cost = cost
        self.instance = instance
        self.boss = boss


class Balance:
    def __init__(self, player, value):
        self.player = player
        self.value = value


class BalanceView:
    def __init__(self, season_name, balance, loot_history, validations):
        self.season_name = season_name
        self.balance = balance
        self.loot_history = loot_history
        self.validations = validations


def get_raw_data_from_files(export_dir):
    result = pandas.DataFrame()
    for file in os.listdir(export_dir):
        dataframe = pandas.read_json(os.path.join(export_dir, file), orient='records', dtype='str')
        result = pandas.concat([result, dataframe])
    return result


def cleanup_data(raw_data):
    result = raw_data.copy()
    result['timestamp'] = result['date'] + ' ' + result['time']
    result = result[["timestamp", "player", "itemName", "note", "instance", "boss"]]
    result = result.rename(columns={'itemName': 'item'})
    result = result.rename(columns={'note': 'cost'})
    result.set_index('timestamp')
    return result.sort_values(by=['timestamp'], ascending=False, ignore_index=True)


def get_balance(player_list, raid_list, loot):
    # init balance list
    balance_list = list()
    for player in player_list:
        balance_list.append(Balance(player, INITIAL_BALANCE))

    # add attendance fee
    for raid in raid_list:
        for player in raid.player_list:
            for balance in balance_list:
                if player == balance.player.name:
                    balance.value = balance.value + ATTENDANCE_BONUS

    # subtract costs
    for index, row in loot.iterrows():
        char = row['player']
        cost = row['cost']
        for balance in balance_list:
            if char in balance.player.chars:
                balance.value = balance.value - int(cost)

    balance_list_as_df = [[balance.player.name, balance.value] for balance in balance_list]
    return (pandas.DataFrame(balance_list_as_df, columns=['name', 'points'])
            .sort_values(by=['name'], ascending=True, ignore_index=True))


def filter_data(raw_data):
    result = raw_data.copy()
    result = result[result['response'] == 'Gebot']
    return result


def get_loot_from_local_files(season_key):
    raw_data = get_raw_data_from_files(os.path.join('data', 'season', season_key))
    filtered_data = filter_data(raw_data)
    return cleanup_data(filtered_data)


def validate_characters_known(player_list, looting_char_list):
    known_char_list = list()
    for player in player_list:
        for char in player.chars:
            known_char_list.append(char)

    result = []
    for char in looting_char_list:
        if char not in known_char_list:
            result.append("Unknown character: " + char)
    return result


def validate_costs_parsable(cost_list):
    result = []
    for index, row in cost_list.iterrows():
        timestamp = row['timestamp']
        cost = row['cost']
        try:
            int(cost)
        except ValueError:
            result.append("Invalid cost: " + cost + " (at timestamp: " + timestamp + ")")
    return result


def get_balance_view():
    loot = get_loot_from_local_files(config.season.key)
    season_name = config.season.name
    player_list = config.player_list

    validations = []
    validations.extend(validate_characters_known(player_list, loot['player'].unique()))
    validations.extend(validate_costs_parsable(loot[["timestamp", "cost"]]))

    if validations:
        return BalanceView(season_name, None, None, validations)

    balance = get_balance(player_list, config.raid_list, loot[["player", "cost"]])

    return BalanceView(season_name, balance, loot, None)


def get_admin_view(report_id):
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
