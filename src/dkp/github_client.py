"""
Client for interaction with github.com API
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import json
import logging
from threading import Lock
from typing import Callable, Type

from core import (
    Fix,
    Loot,
    Player,
    Raid,
    RaidChecklist,
    RaidStats,
    RawLoot,
    Season,
    csv_to_list,
    dict_to_csv,
    is_local_development,
    to_raw_loot_list,
    to_timestamp,
)
from github import Auth, Github, UnknownObjectException
from github.ContentFile import ContentFile

log = logging.getLogger(__name__)

USER_NAME = "oliverfischer83"
REPO_NAME = "dkp"


class GithubClient:

    def __init__(self, branch_name, token):
        self._branch_name = branch_name
        self._github_api = Github(auth=Auth.Token(token))
        self._repo_api = None
        self._raid_checklist = None
        self._player_list = None
        self._season_list = None
        self._raid_list = None
        self._raw_loot_list = None
        self._lock_player = Lock()
        self._lock_raid = Lock()
        self._lock_season = Lock()
        self._lock_loot = Lock()

    @property
    def raid_checklist(self):
        if self._raid_checklist is None:
            self._raid_checklist = RaidChecklist()
        return self._raid_checklist

    @property
    def repo_api(self):
        if self._repo_api is None:
            self._repo_api = self._github_api.get_user(USER_NAME).get_repo(REPO_NAME)
        return self._repo_api

    @property
    def player_list(self):
        if self._player_list is None:
            self._player_list = self._load_data(Player, _get_player_file(), self._lock_player)
        return self._player_list

    @property
    def season_list(self):
        if self._season_list is None:
            self._season_list = self._load_data(Season, _get_season_file(), self._lock_season)
        return self._season_list

    @property
    def raid_list(self):
        if self._raid_list is None:
            self._raid_list = self._load_data(Raid, _get_raid_file(), self._lock_raid)
        return self._raid_list

    @property
    def raw_loot_list(self):
        if self._raw_loot_list is None:
            self._raw_loot_list = self._load_raw_loot_list()
        return self._raw_loot_list

    def _load_raw_loot_list(self) -> dict[Season, dict[Raid, list[RawLoot]]]:
        with self._lock_loot:
            result = {}
            for season in self.season_list:
                dir_path = _get_loot_log_dir_path(season.name)
                try:
                    file_list = self.repo_api.get_contents(dir_path, ref=self._branch_name)
                except UnknownObjectException:
                    continue  # no loot logs for this season yet
                if isinstance(file_list, ContentFile):
                    file_list = [file_list]
                raid_dict = {}
                for file in reversed(file_list):  # get latest files first (only relevant for local development)
                    content = file.decoded_content.decode("utf-8")
                    raw_loot_list = to_raw_loot_list(content)
                    raid_day = file.name.split(".")[0]
                    raid = self.find_raid_by_date(raid_day)
                    raid_dict[raid] = raw_loot_list
                    if is_local_development() and len(raid_dict) >= 1:
                        break
                result[season] = raid_dict
            return result

    def _load_data[T](self, clazz: Type[T], file_path: str, lock: Lock) -> list[T]:
        with lock:
            content = self._get_data_file_content(file_path)
            return [clazz(**entry) for entry in json.loads(content)]

    def _get_data_file_hash(self, file_path: str) -> str:
        result = self.repo_api.get_contents(file_path, ref=self._branch_name)
        if isinstance(result, list):
            raise TypeError(f"Multiple files found for {file_path}")
        return result.sha

    def _get_data_file_content(self, file_path: str) -> str:
        result = self.repo_api.get_contents(file_path, ref=self._branch_name)
        if isinstance(result, list):
            raise TypeError(f"Multiple files found for {file_path}")
        return result.decoded_content.decode("utf-8")

    def add_player(self, player_name: str):
        player_id = max([player.id for player in self.player_list]) + 1
        self.player_list.append(Player(id=player_id, name=player_name, chars=[]))
        self._update_player_list()

    def delete_player(self, player_name: str):
        player = self.find_player_by_name(player_name)
        self.player_list.remove(player)
        self._update_player_list()

    def update_player(self, fixes: list[Fix]):
        for fix in fixes:
            for player in self.player_list:
                if player.id == int(fix.id):
                    for e in fix.entries:
                        if e.name == "name":
                            player.name = e.value
                        elif e.name == "chars":
                            player.chars = csv_to_list(e.value)
                        else:
                            raise KeyError(f"Invalid key: {e.name}")  # sanity check
                    break
        self._update_player_list()

    def add_raid(self, date: str):
        raid_id = max([raid.id for raid in self.raid_list]) + 1
        self.raid_list.append(Raid(id=raid_id, date=date, report_id="", player=[]))
        self._update_raid_list()

    def delete_raid(self, raid_date: str):
        raid = self.find_raid_by_date(raid_date)
        self.raid_list.remove(raid)
        self._update_raid_list()

    def update_raid(self, fixes: list[Fix]):
        for fix in fixes:
            for raid in self.raid_list:
                if raid.id == int(fix.id):
                    for e in fix.entries:
                        if e.name == "date":
                            raid.date = e.value
                        elif e.name == "report_id":
                            raid.report_id = e.value
                        elif e.name == "player":
                            raid.player = csv_to_list(e.value)
                        else:
                            raise KeyError(f"Invalid key: {e.name}")
        self._update_raid_list()

    def add_season(self, name: str):
        season_id = max([season.id for season in self.season_list]) + 1
        self.season_list.append(Season(id=season_id, name=name, desc="", start_date=""))
        self._update_season_list()

    def delete_season(self, season_desc: str):
        season = next((s for s in self.season_list if s.desc == season_desc))
        self.season_list.remove(season)
        self._update_season_list()

    def update_season(self, fixes: list[Fix]):
        for fix in fixes:
            for season in self.season_list:
                if season.id == int(fix.id):
                    for e in fix.entries:
                        if e.name == "name":
                            season.name = e.value
                        elif e.name == "desc":
                            season.desc = e.value
                        elif e.name == "start_date":
                            season.start_date = e.value
                        else:
                            raise KeyError(f"Invalid key: {e.name}")  # sanity check
                    break
        self._update_season_list()

    def _update_player_list(self):
        file_path = _get_player_file()
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", data_to_json(self.player_list, "name"), file_hash, self._branch_name)

    def _update_raid_list(self):
        file_path = _get_raid_file()
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", data_to_json(self.raid_list, "date"), file_hash, self._branch_name)

    def _update_season_list(self):
        file_path = _get_season_file()
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, "Update", data_to_json(self.season_list, "id"), file_hash, self._branch_name)

    def get_season_loot_raw(self, season: Season) -> list[RawLoot]:
        if season not in self.raw_loot_list:
            return []
        result = []
        for _, loot_list in self.raw_loot_list[season].items():
            result.extend(loot_list)
        return result

    def get_raid_loot_raw(self, raid_day: str) -> list[RawLoot]:
        raid = self.find_raid_by_date(raid_day)
        season = self.find_season_by_raid(raid)
        for raid, loot_list in self.raw_loot_list[season].items():
            if raid.date == raid_day:
                return loot_list
        return []

    def get_raid_loot(self, raid_day: str) -> list[Loot]:
        raid_loot = self.get_raid_loot_raw(raid_day)
        return self._cleaning(raid_loot)

    def get_season_loot(self, season: Season) -> list[Loot]:
        season_loot = self.get_season_loot_raw(season)
        return self._cleaning(season_loot)

    def _cleaning(self, raw_loot: list[RawLoot]) -> list[Loot]:
        result = []
        for raw_entry in raw_loot:
            player_name = self.find_player_by_character(
                raw_entry.player
            ).name  # raw_entry.player is actually the character name not the player name
            entry = Loot(
                id=raw_entry.id,
                timestamp=to_timestamp(raw_entry.date + " " + raw_entry.time),
                player=player_name,
                note=raw_entry.note.strip(),
                item_name=raw_entry.itemName,
                item_link=f"https://www.wowhead.com/item={raw_entry.itemID}",
                item_id=str(raw_entry.itemID),
                boss=raw_entry.boss.split(",")[0],
                difficulty=raw_entry.instance.split("-")[1],
                instance=raw_entry.instance.split("-")[0].split(",")[0],
                character=raw_entry.player,
                response=raw_entry.response,
            )
            result.append(entry)
        return sorted(result, key=lambda entry: entry.timestamp, reverse=True)

    def _get_season_end(self, season: Season) -> str | None:
        next_season = self._get_next_season(season)
        if next_season:
            return next_season.start_date
        else:
            return None

    def _get_next_season(self, season: Season) -> Season | None:
        sorted_list = sorted(self.season_list, key=lambda season: season.start_date)
        for i, s in enumerate(sorted_list):
            if s == season:
                if i + 1 < len(sorted_list):
                    return sorted_list[i + 1]
        return None

    def get_raid_list(self, season: Season) -> list[Raid]:
        season_end = self._get_season_end(season)
        if season_end:
            return [raid for raid in self.raid_list if season.start_date <= raid.date < season_end]
        else:
            return [raid for raid in self.raid_list if season.start_date <= raid.date]

    def get_empty_season_list(self) -> list[Season]:
        result = []
        for season in self.season_list:
            if season not in self.raw_loot_list:
                result.append(season)
        return result

    def get_absent_player_list(self) -> list[Player]:
        result = []
        for player in self.player_list:
            # player didn't attend any raid
            if not any([player.name in raid.player for raid in self.raid_list]):
                result.append(player)
        return result

    def get_empty_raid_list(self, season: Season) -> list[Raid]:
        result = []
        for raid in self.get_raid_list(season):
            # raid has no loot log yet
            if raid not in self.raw_loot_list[season]:
                result.append(raid)
        return result

    def find_season_by_raid(self, raid: Raid) -> Season:
        for season in sorted(self.season_list, key=lambda season: season.start_date, reverse=True):
            if season.start_date <= raid.date:
                return season
        raise ValueError(f"No season found for raid {raid.date}")

    def find_raid_by_date(self, raid_day: str) -> Raid:
        for raid in self.raid_list:
            if raid.date == raid_day:
                return raid
        raise ValueError(f"No raid found for {raid_day}")

    def find_player_by_name(self, player_name: str) -> Player:
        for player in self.player_list:
            if player.name == player_name:
                return player
        raise ValueError(f"No player found for {player_name}")

    def find_player_by_character(self, char_name: str) -> Player:
        for player in self.player_list:
            if char_name in player.chars:
                return player
        raise ValueError(f"No player found having character {char_name}")

    def update_raid_checklist(self, checklist: RaidChecklist):
        self._raid_checklist = checklist

    def create_loot_log(self, content: list[RawLoot], raid_day: str):
        def _create_loot_log(file_path: str, content: str, commit_msg: str):
            self.repo_api.create_file(file_path, commit_msg, content, self._branch_name)

        self._handle_github_file(content, raid_day, "Create", _create_loot_log)

    def _update_loot_log(self, file_path: str, content: str, commit_msg: str):
        file_hash = self._get_data_file_hash(file_path)
        self.repo_api.update_file(file_path, commit_msg, content, file_hash, self._branch_name)

    def update_loot_log(self, content: list[RawLoot], raid_day: str):
        self._handle_github_file(content, raid_day, "Update", self._update_loot_log)

    def fix_loot_log(self, content: list[RawLoot], raid_day: str, reason: str):
        self._handle_github_file(content, raid_day, f"Fix: {reason}", self._update_loot_log)

    def _handle_github_file(self, content: list[RawLoot], raid_day: str, commit_msg: str, specific_handling_func: Callable):
        season = self.find_season_by_raid(self.find_raid_by_date(raid_day))
        file_path = _get_loot_log_file_path(season.name, raid_day)
        # update file on github
        specific_handling_func(file_path, to_raw_loot_json(content), commit_msg)
        # update loot list
        raid = self.find_raid_by_date(raid_day)
        self.raw_loot_list[season][raid] = content

    def create_raid_excel_file(self, balance: dict[str, str]):
        file_path = _get_balance_fallback_file()
        file_hash = self._get_data_file_hash(file_path)
        content = dict_to_csv(balance)
        self.repo_api.update_file(file_path, "Update", content, file_hash, self._branch_name)


def _get_raid_file():
    return "data/raid.json"


def _get_player_file():
    return "data/player.json"


def _get_season_file():
    return "data/season.json"


def _get_balance_fallback_file():
    return "data/balance_fallback.csv"


def _get_loot_log_dir_path(season: str):
    return f"data/season/{season}"


def _get_loot_log_file_path(season: str, raid_day: str):
    return f"data/season/{season}/{raid_day}.json"


def to_raw_loot_json(loot_list: list[RawLoot]) -> str:
    """Converts raw loot lists into json str for database storage."""
    content = [loot.model_dump(by_alias=True) for loot in loot_list]
    sorted_content = sorted(content, key=lambda entry: entry["player"])  # sort by character name
    return _to_json(sorted_content)


def data_to_json[T: (Player, Raid, Season, RaidStats)](model_list: list[T], sort_by: str) -> str:
    content = [model.model_dump() for model in model_list]
    sorted_content = sorted(content, key=lambda entry: entry[sort_by])
    return _to_json(sorted_content)


def _to_json(content: list) -> str:
    return json.dumps(content, indent=2, ensure_ascii=False)  # allow non-ascii characters
