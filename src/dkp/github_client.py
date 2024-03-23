"""
Client for interaction with github.com API
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import logging

from github import Auth, Github, UnknownObjectException
from github.GithubException import GithubException
from github.ContentFile import ContentFile


log = logging.getLogger(__name__)

USER_NAME = "oliverfischer83"
REPO_NAME = "dkp"

class GithubClient:

    def __init__(self, token):
        github_api = Github(auth=Auth.Token(token))
        self.repo_api = github_api.get_user(USER_NAME).get_repo(REPO_NAME)


    def _get_loot_log(self, season: str, raid_day: str) -> ContentFile:
        file_path = _get_loot_log_file_path(season, raid_day)
        result = self.repo_api.get_contents(file_path)
        if result is list:
            raise ValueError(f"Multiple files found for {file_path}")
        return result # type: ignore


    def get_loot_log_content(self, season: str, raid_day: str) -> str | None:
        try:
            return self._get_loot_log(season, raid_day).decoded_content.decode("utf-8")
        except UnknownObjectException:
            return None


    def update_or_create_loot_log(self, json_string: str, season: str, raid_day: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        try:
            self.repo_api.create_file(file_path, f"Create loot log for {raid_day}", json_string)
        except GithubException:
            file = self._get_loot_log(season, raid_day)
            self.repo_api.update_file(file_path, f"Update loot log for {raid_day}", json_string, file.sha)


def _get_loot_log_file_path(season: str, raid_day: str):
    return f"data/season/{season}/{raid_day}.json"
