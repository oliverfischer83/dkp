"""
Business logic for the DKP webapp.
"""
import os
import pandas
import yaml

INITIAL_BALANCE = 100


class Config:
    def __init__(self, season, player_list, raid_list=None):
        self.season = season
        self.player_list = player_list
        self.raid_list = raid_list


class Season:
    def __init__(self, name, key):
        self.name = name
        self.key = key


class Player:
    def __init__(self, name, chars):
        self.name = name
        self.chars = chars


class Raid:
    def __init__(self, date, report, member_list):
        self.date = date
        self.report = report
        self.member_list = member_list


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


class View:
    def __init__(self, season_name, balance, loot_history, validations):
        self.season_name = season_name
        self.balance = balance
        self.loot_history = loot_history
        self.validations = validations


def get_config():
    with open('data/config.yml', 'r') as config_file:
        config_yml = yaml.safe_load(config_file)
    season = Season(config_yml['season']['name'], config_yml['season']['key'])
    player_list = []
    for player in config_yml['player']:
        player_list.append(Player(player['name'], player['chars']))
    return Config(season, player_list)


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


def get_balance(player_list, loot):
    balance_list = list()
    for player in player_list:
        balance_list.append(Balance(player, INITIAL_BALANCE))

    for index, row in loot.iterrows():
        char = row['player']
        cost = row['cost']
        for balance in balance_list:
            if char in balance.player.chars:
                balance.value = balance.value - int(cost)

    balance_list_as_df = [[balance.player.name, balance.value] for balance in balance_list]
    return (pandas.DataFrame(balance_list_as_df, columns=['name', 'points'])
            .sort_values(by=['name'], ascending=True, ignore_index=True))


def get_loot_from_local_files(season_key):
    raw_data = get_raw_data_from_files(os.path.join('data', 'season', season_key))
    return cleanup_data(raw_data)


def validate_players_exists(player_list, looting_char_list):
    known_char_list = list()
    for player in player_list:
        for char in player.chars:
            known_char_list.append(char)

    result = []
    for player in looting_char_list:
        if player not in known_char_list:
            result.append("Unknown player: " + player)
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


def get_view():
    config = get_config()
    loot = get_loot_from_local_files(config.season.key)
    season_name = config.season.name
    player_list = config.player_list

    validations = []
    validations.extend(validate_players_exists(player_list, loot['player'].unique()))
    validations.extend(validate_costs_parsable(loot[["timestamp", "cost"]]))

    if validations:
        return View(season_name, None, None, validations)

    balance = get_balance(player_list, loot[["player", "cost"]])

    return View(season_name, balance, loot, validations)


def get_raid(report_id):
    report_link = f"https://www.warcraftlogs.com/reports/{report_id}"
    # TODO call api and get members

    date = "1990-01-01"
    member_list = []

    result = Raid(date, report_link, member_list)
    return result

