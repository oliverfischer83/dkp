"""
Used to map the config file to a class
"""

import yaml
from dataclasses import dataclass


@dataclass
class WclClient:
    client_id: str
    client_secret: str
    token_url: str
    api_endpoint: str


@dataclass
class Auth:
    wcl_client: WclClient


@dataclass
class Season:
    name: str
    key: str


@dataclass
class Player:
    name: str
    chars: list[str]


@dataclass
class Raid:
    date: str
    report: str
    player_list: list[str]


@dataclass
class Config:
    auth: Auth
    season: Season
    player_list: list[Player]
    raid_list: list[Raid]


def get_config():
    with open('data/config.yml', 'r') as config_file:
        config_yml = yaml.safe_load(config_file)

    wcl_config = config_yml['auth']['wcl']
    wcl_client = WclClient(wcl_config['client-id'], wcl_config['client-secret'], wcl_config['token-url'],
                           wcl_config['api-endpoint'])
    auth = Auth(wcl_client)

    season = Season(config_yml['season']['name'], config_yml['season']['key'])
    player_list = []
    for player in config_yml['player']:
        player_list.append(Player(player['name'], player['chars']))

    raid_list = []
    for raid in config_yml['raid']:
        raid_list.append(Raid(raid['date'], raid['report'], raid['player']))
    return Config(auth, season, player_list, raid_list)
