"""
Used to map the config file to a class
"""

import yaml


class Config:
    def __init__(self, auth, season, player_list, raid_list):
        self.auth = auth
        self.season = season
        self.player_list = player_list
        self.raid_list = raid_list


class Auth:
    def __init__(self, wcl_client):
        self.wcl_client = wcl_client


class WclClient:
    def __init__(self, client_id, client_secret, token_url, api_endpoint):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.api_endpoint = api_endpoint


class Season:
    def __init__(self, name, key):
        self.name = name
        self.key = key


class Player:
    def __init__(self, name, chars):
        self.name = name
        self.chars = chars


class Raid:
    def __init__(self, date, report, player_list):
        self.date = date
        self.report = report
        self.player_list = player_list


def get_config():
    with open('data/config.yml', 'r') as config_file:
        config_yml = yaml.safe_load(config_file)

    wcl_config = config_yml['auth']['wcl']
    wcl_client = WclClient(wcl_config['client-id'], wcl_config['client-secret'], wcl_config['token-url'], wcl_config['api-endpoint'])
    auth = Auth(wcl_client)

    season = Season(config_yml['season']['name'], config_yml['season']['key'])
    player_list = []
    for player in config_yml['player']:
        player_list.append(Player(player['name'], player['chars']))

    raid_list = []
    for raid in config_yml['raid']:
        raid_list.append(Raid(raid['date'], raid['report'], raid['player']))
    return Config(auth, season, player_list, raid_list)

