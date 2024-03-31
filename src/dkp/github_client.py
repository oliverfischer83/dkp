"""
Client for interaction with github.com API
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import json
import logging
from threading import Lock

from core import (
    Loot,
    Player,
    Raid,
    RawLoot,
    Season,
    is_local_development,
    to_raw_loot_list,
)
from github import Auth, Github
from github.ContentFile import ContentFile

log = logging.getLogger(__name__)

USER_NAME = "oliverfischer83"
REPO_NAME = "dkp"
BRANCH = "develop" if is_local_development() else "main"


class GithubClient:

    def __init__(self, token):
        self._github_api = Github(auth=Auth.Token(token))
        self._repo_api = None
        self._player_list = None
        self._season_list = None
        self._raid_list = None
        self._raw_loot_list = None
        self._lock_player = Lock()
        self._lock_raid = Lock()
        self._lock_season = Lock()
        self._lock_loot = Lock()

    @property
    def repo_api(self):
        if self._repo_api is None:
            self._repo_api = self._github_api.get_user(USER_NAME).get_repo(REPO_NAME)
        return self._repo_api

    @property
    def player_list(self):
        if self._player_list is None:
            with self._lock_player:
                self._player_list = self._load_players()
        return self._player_list

    @property
    def season_list(self):
        if self._season_list is None:
            with self._lock_season:
                self._season_list = self._load_seasons()
        return self._season_list

    @property
    def raid_list(self):
        if self._raid_list is None:
            with self._lock_raid:
                self._raid_list = self._load_raids()
        return self._raid_list

    @property
    def raw_loot_list(self):
        if self._raw_loot_list is None:
            with self._lock_loot:
                self._raw_loot_list = self._load_raw_loot_list()
        return self._raw_loot_list

    def _load_raw_loot_list(self) -> dict[Season, dict[Raid, list[RawLoot]]]:
        result = {}
        for season in self.season_list:
            dir_path = _get_loot_log_dir_path(season.name)
            file_list = self.repo_api.get_contents(dir_path, ref=BRANCH)
            if isinstance(file_list, ContentFile):
                file_list = [file_list]
            raid_dict = {}
            for file in reversed(file_list):  # get latest files first (only relevant for local development)
                content = file.decoded_content.decode("utf-8")
                raw_loot_list = to_raw_loot_list(content)
                raid_day = file.name.split(".")[0]
                raid = self.find_raid_by_date(raid_day)
                raid_dict[raid] = raw_loot_list
                if is_local_development() and len(raid_dict) >= 2:
                    break
            result[season] = raid_dict
        return result


    def _load_raids(self) -> list[Raid]:
        content = self._get_data_file_content(_get_raid_file())
        return [Raid(**entry) for entry in json.loads(content)]


    def _load_players(self) -> list[Player]:
        content = self._get_data_file_content(_get_player_file())
        return [Player(**entry) for entry in json.loads(content)]


    def _load_seasons(self) -> list[Season]:
        content = self._get_data_file_content(_get_season_file())
        return [Season(**entry) for entry in json.loads(content)]


    def _get_data_file_hash(self, file_path: str) -> str:
        result = self.repo_api.get_contents(file_path, ref=BRANCH)
        if isinstance(result, list):
            raise Exception(f"Multiple files found for {file_path}")
        return result.sha


    def _get_data_file_content(self, file_path: str) -> str:
        result = self.repo_api.get_contents(file_path, ref=BRANCH)
        if isinstance(result, list):
            raise Exception(f"Multiple files found for {file_path}")
        return result.decoded_content.decode("utf-8")


    def add_player(self, player_name: str):
        id = max([player.id for player in self.player_list]) + 1
        self.player_list.append(Player(id=id, name=player_name, chars=[]))
        self._update_player_list()


    def add_player_character(self, player_name: str, character_name: str):
        player = self.find_player_by_name(player_name)
        player.chars.append(character_name)
        self._update_player_list()


    def add_raid(self, date: str):
        id = max([raid.id for raid in self.raid_list]) + 1
        self.raid_list.append(Raid(id=id, date=date, report="", player=[]))
        self._update_raid_list()


    def set_raid_details(self, report: str ,attendees: list[str]):
        raid = self.find_raid_by_date("2021-01-01")
        raid.player = attendees
        raid.report = report
        self._update_raid_list()


    def add_season(self, name: str, descr: str):
        id = max([season.id for season in self.season_list]) + 1
        self.season_list.append(Season(id=id, name=name, descr=descr))
        self._update_season_list()


    def _update_player_list(self):
        file_path = _get_player_file()
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", to_player_json(self.player_list), file_hash, BRANCH)


    def _update_raid_list(self):
        file_path = _get_raid_file()
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", to_raid_json(self.raid_list), file_hash, BRANCH)


    def _update_season_list(self):
        file_path = _get_season_file()
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", to_season_json(self.season_list), file_hash, BRANCH)


    def get_loot_log_raw(self, raid_day: str) -> list[RawLoot]:
        raid = self.find_raid_by_date(raid_day)
        season = self.find_season_by_raid(raid)
        season_logs = self.raw_loot_list[season]
        for raid, loot_list in season_logs.items():
            if raid.date == raid_day:
                return loot_list
        return []


    def get_loot_log(self, raid_day: str) -> list[Loot]:
        log = self.get_loot_log_raw(raid_day)
        return _cleanup_data(log, self.player_list)


    def get_all_loot_logs(self, season: Season) -> list[Loot]:
        season_logs = []
        for _, loot_list in self.raw_loot_list[season].items():
            season_logs += loot_list
        return _cleanup_data(season_logs, self.player_list)


    def find_season_by_raid(self, raid: Raid) -> Season:
        for season in self.season_list:
            if raid in self.raw_loot_list[season]:
                return season
        raise Exception(f"No season found for raid {raid.date}")


    def find_raid_by_date(self, raid_day: str) -> Raid:
        for raid in self.raid_list:
            if raid.date == raid_day:
                return raid
        raise Exception(f"No raid found for {raid_day}")


    def find_player_by_name(self, player_name: str) -> Player:
        for player in self.player_list:
            if player.name == player_name:
                return player
        raise ValueError(f"No player found for {player_name}")


    def create_loot_log(self, content: list[RawLoot], season: Season, raid_day: str):
        # update file on github
        file_path = _get_loot_log_file_path(season.name, raid_day)
        self.repo_api.create_file(file_path, "Create", to_raw_loot_json(content), BRANCH)
        # update loot list
        raid = self.find_raid_by_date(raid_day)
        self.raw_loot_list[season][raid] = content


    def update_loot_log(self, content: list[RawLoot], season: Season, raid_day: str):
        # update file on github
        file_path = _get_loot_log_file_path(season.name, raid_day)
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", to_raw_loot_json(content), file_hash, BRANCH)
        # update loot list
        raid = self.find_raid_by_date(raid_day)
        self.raw_loot_list[season][raid] = content


    def fix_loot_log(self, content: list[RawLoot], season: Season, raid_day: str, reason: str):
        # update file on github
        file_path = _get_loot_log_file_path(season.name, raid_day)
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, f"Fix: {reason}", to_raw_loot_json(content), file_hash, BRANCH)
        # update loot list
        raid = self.find_raid_by_date(raid_day)
        self.raw_loot_list[season][raid] = content


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


def to_raw_loot_json(loot_list: list[RawLoot]) -> str:
    """Converts raw loot lists into json str for database storage."""
    content = [loot.model_dump(by_alias=True) for loot in loot_list]
    sorted_content = sorted(content, key=lambda entry: entry['player'])  # sort by character name
    return to_json(sorted_content)


def to_player_json(player_list: list[Player]) -> str:
    content = [player.model_dump() for player in player_list]
    sorted_content = sorted(content, key=lambda entry: entry['name'])  # sort by player name
    return to_json(sorted_content)


def to_raid_json(raid_list: list[Raid]) -> str:
    content = [raid.model_dump() for raid in raid_list]
    sorted_content = sorted(content, key=lambda entry: entry['date'])  # sort by raid date
    return to_json(sorted_content)


def to_season_json(season_list: list[Season]) -> str:
    content = [season.model_dump() for season in season_list]
    sorted_content = sorted(content, key=lambda entry: entry['id'])  # sort by raid id
    return to_json(sorted_content)


def to_json(content: list) -> str:
    return json.dumps(content,
                      indent=2,             # beautify
                      ensure_ascii=False)   # allow non-ascii characters