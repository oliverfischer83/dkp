"""
Used to map and hold the config file in a singleton class
"""

import datetime
import threading

import yaml
from pydantic import BaseModel


class WclClient(BaseModel):
    client_id: str
    client_secret: str
    token_url: str
    api_endpoint: str


class Auth(BaseModel):
    wcl_client: WclClient


class Season(BaseModel):
    name: str
    key: str


class Player(BaseModel):
    name: str
    chars: list[str]


class Raid(BaseModel):
    date: datetime.date
    report: str
    player: list[str]


class ConfigRoot(BaseModel):
    auth: Auth
    season: Season
    player: list[Player]
    raid: list[Raid]


class Config:
    # singleton instance
    _instance = None
    # used to prevent multiple threads (e.g. multiple browser tabs) from start working with a not yet
    # fully loaded config, which will lead to errors
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
        self.player_list: list[Player] = root.player
        self.raid_list: list[Raid] = root.raid

    def reload_config(self):
        with self._lock:
            self._load_config()


def load_config():
    with open("config.yml", "r") as config_file:
        config_yml = yaml.safe_load(config_file)
    return ConfigRoot(**config_yml)
