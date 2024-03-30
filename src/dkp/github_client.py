"""
Client for interaction with github.com API
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import json
import logging

from core import Loot, Player, Raid, RawLoot, Season, to_date, to_player_json, to_raw_loot_json, to_raw_loot_list
from github import Auth, Github
from github.ContentFile import ContentFile

log = logging.getLogger(__name__)

USER_NAME = "oliverfischer83"
REPO_NAME = "dkp"


class GithubClient:

    def __init__(self, token):
        github_api = Github(auth=Auth.Token(token))
        self.repo_api = github_api.get_user(USER_NAME).get_repo(REPO_NAME)
        self.player_list = self._load_players()
        self.season_list = self._load_seasons()
        self.raid_list = self._load_raids()
        self.raw_loot_list = self._load_raw_loot_list()


    def _get_data_file_hash(self, file_path: str) -> str:
        result = self.repo_api.get_contents(file_path)
        if isinstance(result, list):
            raise ValueError(f"Multiple files found for {file_path}")
        return result.sha


    def _get_data_file_content(self, file_path: str) -> str:
        result = self.repo_api.get_contents(file_path)
        if isinstance(result, list):
            raise ValueError(f"Multiple files found for {file_path}")
        return result.decoded_content.decode("utf-8")


    def _load_raw_loot_list(self) -> dict[Season, dict[Raid, list[RawLoot]]]:
        result = {}
        for season in self.season_list:
            dir_path = _get_loot_log_dir_path(season.key)
            file_list = self.repo_api.get_contents(dir_path)
            if isinstance(file_list, ContentFile):
                file_list = [file_list]
            raid_dict = []
            for file in file_list:
                content = file.decoded_content.decode("utf-8")
                raw_loot_list = to_raw_loot_list(content)
                raid_day = file.name.split(".")[0]
                raid = get_raid_by_date(self.raid_list, raid_day)
                raid_dict[raid] = raw_loot_list  # type: ignore
            result[season] = raid_dict
        return result


    def _load_raids(self) -> list[Raid]:
        content = self._get_data_file_content(_get_raid_file())
        return [Raid(**entry) for entry in json.loads(content)]


    def _load_players(self) -> list[Player]:
        content = self._get_data_file_content(_get_player_file())
        player_list = [Player(**entry) for entry in json.loads(content)]
        return player_list


    def _load_seasons(self) -> list[Season]:
        content = self._get_data_file_content(_get_season_file())
        season_list = [Season(**entry) for entry in json.loads(content)]
        return season_list


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
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", to_player_json(self.player_list), file_hash)


    def get_loot_log_raw(self, season: Season, raid_day: str) -> list[RawLoot]:
        season_logs = self.raw_loot_list[season]
        for raid, loot_list in season_logs.items():
            if to_date(raid.date) == raid_day:
                return loot_list
        return []


    def get_loot_log(self, season: Season, raid_day: str) -> list[Loot]:
        log = self.get_loot_log_raw(season, raid_day)
        return _cleanup_data(log, self.player_list)


    def get_all_loot_logs(self, season: Season) -> list[Loot]:
        season_logs = []
        for _, loot_list in self.raw_loot_list[season].items():
            season_logs += loot_list
        return _cleanup_data(season_logs, self.player_list)


    def create_loot_log(self, content: list[RawLoot], season: Season, raid_day: str):
        file_path = _get_loot_log_file_path(season.key, raid_day)
        self.repo_api.create_file(file_path, "Create", to_raw_loot_json(content))
        # TODO update self.raw_loot_list


    def update_loot_log(self, content: list[RawLoot], season: Season, raid_day: str):
        # update file on github
        file_path = _get_loot_log_file_path(season.key, raid_day)
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", to_raw_loot_json(content), file_hash)
        # update loot list
        raid = get_raid_by_date(self.raid_list, raid_day)
        self.raw_loot_list[season][raid] = content


    def fix_loot_log(self, content: list[RawLoot], season: Season, raid_day: str, reason: str):
        file_path = _get_loot_log_file_path(season.key, raid_day)
        file_hash = self._get_data_file_hash(file_path)
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
    return "data/raid.json"
def _get_player_file():
    return "data/player.json"
def _get_season_file():
    return "data/season.json"
def _get_loot_log_dir_path(season: str):
    return f"data/season/{season}"
def _get_loot_log_file_path(season: str, raid_day: str):
    return f"data/season/{season}/{raid_day}.json"


def get_raid_by_date(raid_list: list[Raid], raid_day: str) -> Raid:
    raid  = next((raid for raid in raid_list if raid.date == raid_day), None)
    if raid is None:
        raise Exception(f"No raid found for {raid_day}")
    return raid
