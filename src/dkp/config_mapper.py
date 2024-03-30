"""
Used to map and hold the config file in a singleton class
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import logging
import threading

import yaml
from pydantic import BaseModel

log = logging.getLogger(__name__)


class GithubClient(BaseModel):
    token: str

class WclClient(BaseModel):
    client_id: str
    client_secret: str
    token_url: str
    api_endpoint: str


class Auth(BaseModel):
    wcl_client: WclClient
    github_client: GithubClient


class ConfigRoot(BaseModel):
    auth: Auth


class Config:
    # singleton instance
    _instance = None
    # used to prevent multiple threads (e.g. multiple browser tabs) from start working with a not yet
    # fully loaded config, which will lead to errors
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.auth: Auth

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Config, cls).__new__(cls)
                cls._instance._load_config()
            return cls._instance

    def _load_config(self):
        root = load_config()
        self.auth: Auth = root.auth


def load_config():
    log.debug("load_config")
    with open("config.yml", "r", encoding="utf-8") as config_file:
        config_yml = yaml.safe_load(config_file)
    return ConfigRoot(**config_yml)
