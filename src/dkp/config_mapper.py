"""
Used to map and hold the config file in a singleton class
"""

import yaml
import threading
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
class ConfigRoot:
    auth: Auth
    season: Season
    player_list: list[Player]
    raid_list: list[Raid]


class Config:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Config, cls).__new__(cls)
                cls._instance._load_config()
            return cls._instance

    def _load_config(self):
        root = load_config()
        self.auth: Auth = root.auth
        self.season: Season = root.season
        self.player_list: list[Player] = root.player_list
        self.raid_list: list[Raid] = root.raid_list

    def reload_config(self):
        with self._lock:
            self._load_config()


def load_config():
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
    return ConfigRoot(auth, season, player_list, raid_list)
