"""
Client for interaction with github.com API
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import json
import logging
import os

from core import Loot, Player, Raid, RawLoot, to_player_json, to_raw_loot_json, to_raw_loot_list
from github import Auth, Github, UnknownObjectException
from github.ContentFile import ContentFile

log = logging.getLogger(__name__)

USER_NAME = "oliverfischer83"
REPO_NAME = "dkp"


class GithubClient:

    def __init__(self, token):
        github_api = Github(auth=Auth.Token(token))
        self.repo_api = github_api.get_user(USER_NAME).get_repo(REPO_NAME)
        self.player_list = self._load_players()
        self.raid_list = self._load_raids()


    def _get_data_file(self, file_path: str) -> ContentFile:
        result = self.repo_api.get_contents(file_path)
        if result is list:
            raise ValueError(f"Multiple files found for {file_path}")
        return result # type: ignore


    def _load_raids(self) -> list[Raid]:
        content = self._get_data_file(_get_raid_file()).decoded_content.decode("utf-8")
        return [Raid(**entry) for entry in json.loads(content)]

    def get_raids(self) -> list[Raid]:
        return self.raid_list


    def _load_players(self) -> list[Player]:
        content = self._get_data_file(_get_player_file()).decoded_content.decode("utf-8")
        player_list = [Player(**entry) for entry in json.loads(content)]
        return sorted(player_list, key=lambda player: player.name)


    def get_players(self) -> list[Player]:
        self.player_list = sorted(self.player_list, key=lambda player: player.name)
        return self.player_list


    def add_player(self, player_name: str):
        self.player_list.append(Player(name=player_name, chars=[]))
        self._update_player_list()


    def add_character(self, player_name: str, character_name: str):
        for player in self.player_list:
            if player.name == player_name:
                player.chars.append(character_name)
                break
        self._update_player_list()


    def _update_player_list(self):
        file_path = _get_player_file()
        file_hash = self._get_data_file(file_path).sha
        self.repo_api.update_file(file_path, "Update", to_player_json(self.player_list), file_hash)


    def get_loot_log_raw(self, season: str, raid_day: str) -> list[RawLoot]:
        """"Get loot log for a specific raid day from REMOTE repository at github.com."""
        file_path = _get_loot_log_file_path(season, raid_day)
        try:
            content = self._get_data_file(file_path).decoded_content.decode("utf-8")
            return to_raw_loot_list(content)
        except UnknownObjectException:
            return []


    def get_loot_log(self, season: str, raid_day: str) -> list[Loot]:
        """"Get loot log for a specific raid day from REMOTE repository at github.com."""
        file_path = _get_loot_log_file_path(season, raid_day)
        try:
            content = self._get_data_file(file_path).decoded_content.decode("utf-8")
            raw_loot_list = to_raw_loot_list(content)
            return _cleanup_data(raw_loot_list, self.player_list)
        except UnknownObjectException:
            return []


    def get_loot_logs_from_local_files(self, season: str) -> list[Loot]:
        """"Get all loot logs for a season from LOCAL git repository."""
        dir_path = _get_loot_log_dir_path(season)
        result = []
        for file in os.listdir(dir_path):
            with open(os.path.join(dir_path, file), 'r') as file:
                content = file.read()
                raw_loot_list = to_raw_loot_list(content)
                result += _cleanup_data(raw_loot_list, self.player_list)
        return result


    def create_loot_log(self, content: list[RawLoot], season: str, raid_day: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        self.repo_api.create_file(file_path, "Create", to_raw_loot_json(content))


    def update_loot_log(self, content: list[RawLoot], season: str, raid_day: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        file_hash = self._get_data_file(file_path).sha
        self.repo_api.update_file(file_path, "Update", to_raw_loot_json(content), file_hash)


    def fix_loot_log(self, content: list[RawLoot], season: str, raid_day: str, reason: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        file_hash = self._get_data_file(file_path).sha
        self.repo_api.update_file(file_path, f"Fix: {reason}", to_raw_loot_json(content), file_hash)


def _cleanup_data(raw_loot: list[RawLoot], player_list: list[Player]) -> list[Loot]:
    result = []
    for raw_entry in raw_loot:

        # get player name for character
        player_name = ""
        for player in player_list:
            if raw_entry.player in player.chars:
                player_name = player.name
                break

        entry = Loot(
            id = raw_entry.id,
            timestamp = datetime.datetime.strptime(raw_entry.date + " " + raw_entry.time, "%d/%m/%y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S"),
            player = player_name,
            note = raw_entry.note.strip(),
            item_name = raw_entry.itemName,
            item_link = f"https://www.wowhead.com/item={raw_entry.itemID}",
            item_id = str(raw_entry.itemID),
            boss = raw_entry.boss.split(",")[0],
            difficulty = raw_entry.instance.split("-")[1],
            instance = raw_entry.instance.split("-")[0].split(",")[0],
            character = raw_entry.player,
            response = raw_entry.response
        )

        result.append(entry)
    return sorted(result, key=lambda entry: entry.timestamp, reverse=True)


def _get_raid_file():
    return f"data/raid.json"
def _get_player_file():
    return f"data/player.json"
def _get_loot_log_dir_path(season: str):
    return f"data/season/{season}"
def _get_loot_log_file_path(season: str, raid_day: str):
    return f"data/season/{season}/{raid_day}.json"
