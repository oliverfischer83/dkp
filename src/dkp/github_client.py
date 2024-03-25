"""
Client for interaction with github.com API
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import json
import logging
import os

from github import Auth, Github, UnknownObjectException
from github.ContentFile import ContentFile


log = logging.getLogger(__name__)

USER_NAME = "oliverfischer83"
REPO_NAME = "dkp"

class GithubClient:

    def __init__(self, token):
        github_api = Github(auth=Auth.Token(token))
        self.repo_api = github_api.get_user(USER_NAME).get_repo(REPO_NAME)


    def _get_data_file(self, file_path: str) -> ContentFile:
        result = self.repo_api.get_contents(file_path)
        if result is list:
            raise ValueError(f"Multiple files found for {file_path}")
        return result # type: ignore


    def get_loot_log(self, season: str, raid_day: str, raw=False) -> list[dict[str, str]] | None:
        """"Get loot log for a specific raid day from REMOTE repository at github.com."""

        file_path = _get_loot_log_file_path(season, raid_day)
        try:
            loot_log = to_python(self._get_data_file(file_path).decoded_content.decode("utf-8"))
            if raw:
                return loot_log
            else:
                return _cleanup_data(loot_log)
        except UnknownObjectException:
            return None


    def get_loot_log_all(self, season: str) -> list[dict[str, str]]:
        """"Get all loot logs for a season from LOCAL git repository."""

        dir_path = _get_loot_log_dir_path(season)
        result = []
        for file in os.listdir(dir_path):
            with open(os.path.join(dir_path, file), 'r') as file:
                result += to_python(file.read())
        return _cleanup_data(result)


    def create_loot_log(self, content: list[dict[str, str]], season: str, raid_day: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        self.repo_api.create_file(file_path, "Create", to_str(content))


    def update_loot_log(self, content: list[dict[str, str]], season: str, raid_day: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        file_hash = self._get_data_file(file_path).sha
        self.repo_api.update_file(file_path, "Update", to_str(content), file_hash)


    def fix_loot_log(self, content: list[dict[str, str]], season: str, raid_day: str, reason: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        file_hash = self._get_data_file(file_path).sha
        self.repo_api.update_file(file_path, f"Fix: {reason}", to_str(content), file_hash)


def _cleanup_data(data: list[dict[str, str]]) -> list[dict[str, str]]:
    result = data.copy()
    for entry in result:
        # creating timestamp column
        entry["timestamp"] = entry["date"] + " " + entry["time"]
        entry["timestamp"] = datetime.datetime.strptime(entry["timestamp"], "%d/%m/%y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        # remove irrelevant columns
        entry.pop("date")
        entry.pop("time")
        entry.pop("class")
        entry.pop("itemString")
        entry.pop("votes")
        entry.pop("gear1")
        entry.pop("gear2")
        entry.pop("responseID")
        entry.pop("isAwardReason")
        entry.pop("rollType")
        entry.pop("subType")
        entry.pop("equipLoc")
        entry.pop("owner")
        # renaming columns
        entry["character"] = entry.pop("player")
        entry["item_id"] = entry.pop("itemID")
        entry["item_name"] = entry.pop("itemName")
        # cleanup values
        entry["boss"] = entry["boss"].split(",")[0]
        entry["difficulty"] = entry["instance"].split("-")[1]
        entry["instance"] = entry["instance"].split("-")[0].split(",")[0]
    return result


def _get_loot_log_dir_path(season: str):
    return f"data/season/{season}"


def _get_loot_log_file_path(season: str, raid_day: str):
    return f"{_get_loot_log_dir_path(season)}/{raid_day}.json"


def to_str(content: list[dict[str, str]]) -> str:
    """Converts list of dicts into json str for database storage."""
    sorted_content = sorted(content, key=lambda x: x['player'])  # sort by character name
    return json.dumps(sorted_content,
                      indent=2,             # beautify
                      ensure_ascii=False)   # allow non-ascii characters


def to_python(content: str) -> list[dict[str, str]]:
    """Converts json str to list of dicts for data manipulation and transformation."""
    return json.loads(content)
