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
from pydantic import BaseModel, Field, field_validator

log = logging.getLogger(__name__)

USER_NAME = "oliverfischer83"
REPO_NAME = "dkp"


class Loot(BaseModel):
    id: str
    timestamp: str
    player: str
    note: str
    item_name: str
    item_link: str
    item_id: str
    boss: str
    difficulty: str
    instance: str
    character: str
    response: str

    @field_validator('note')
    def validate_note(cls, note):
        if note == "":  # empty note is valid
            return note

        message = f'Invalid note for entry: "{note}". '

        if not note.isdigit():
            raise ValueError(message + "Note must be a parsable integer.")
        if int(note) <= 0:
            raise ValueError(message + "Note must be a positive value.")
        if int(note) % 10 != 0:
            raise ValueError(message + "Note must be a multiple of 10 (e.g. 10, 20, 30, ...).")
        return note

    # @validator('character')
    # def validate_character(cls, character, values):
    #     player_list: list[Player] = values.get('player_list')
    #     for player in player_list:
    #         if character in player.chars:
    #             return character
    #     raise ValueError(f'Unknown character: {character}')

class RawLoot(BaseModel):
    player: str
    date: str
    time: str
    id: str
    itemID: int
    itemString: str
    response: str
    votes: int
    class_: str = Field(alias="class")
    instance: str
    boss: str
    gear1: str
    gear2: str
    responseID: str
    isAwardReason: str
    rollType: str
    subType: str
    equipLoc: str
    note: str
    owner: str
    itemName: str


class Player(BaseModel):
    name: str
    chars: list[str]


class Raid(BaseModel):
    date: str
    report_url: str = Field(alias="report")
    attendees: list[str] = Field(alias="player")


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
        return [Player(**entry) for entry in json.loads(content)]

    def get_players(self) -> list[Player]:
        return self.player_list


    def get_loot_log_raw(self, season: str, raid_day: str) -> list[RawLoot] | None:
        """"Get loot log for a specific raid day from REMOTE repository at github.com."""
        file_path = _get_loot_log_file_path(season, raid_day)
        try:
            content = self._get_data_file(file_path).decoded_content.decode("utf-8")
            return to_raw_loot_list(content)
        except UnknownObjectException:
            return None


    def get_loot_log(self, season: str, raid_day: str) -> list[Loot] | None:
        """"Get loot log for a specific raid day from REMOTE repository at github.com."""
        file_path = _get_loot_log_file_path(season, raid_day)
        try:
            content = self._get_data_file(file_path).decoded_content.decode("utf-8")
            raw_loot_list = to_raw_loot_list(content)
            return _cleanup_data(raw_loot_list, self.player_list)
        except UnknownObjectException:
            return None


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
        self.repo_api.create_file(file_path, "Create", to_str(content))


    def update_loot_log(self, content: list[RawLoot], season: str, raid_day: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        file_hash = self._get_data_file(file_path).sha
        self.repo_api.update_file(file_path, "Update", to_str(content), file_hash)


    def fix_loot_log(self, content: list[RawLoot], season: str, raid_day: str, reason: str):
        file_path = _get_loot_log_file_path(season, raid_day)
        file_hash = self._get_data_file(file_path).sha
        self.repo_api.update_file(file_path, f"Fix: {reason}", to_str(content), file_hash)


def to_str(loot_list: list[RawLoot]) -> str:
    """Converts loot lists into json str for database storage."""
    content = [loot.model_dump(by_alias=True) for loot in loot_list]
    sorted_content = sorted(content, key=lambda entry: entry['player'])  # sort by character name
    return json.dumps(sorted_content,
                      indent=2,             # beautify
                      ensure_ascii=False)   # allow non-ascii characters


def to_raw_loot_list(content: str) -> list[RawLoot]:
    loot_list = json.loads(content)
    raw_loot_list = [RawLoot(**entry) for entry in loot_list]
    validate_raw_loot_list(raw_loot_list)
    return raw_loot_list


def validate_raw_loot_list(raw_loot_list: list[RawLoot]):
    # validate list is not empty
    if not raw_loot_list:
        raise Exception("Empty list.")

    # validate each entry has a unique id
    unique_ids = set()
    for entry in raw_loot_list:
        if entry.id in unique_ids:
            raise Exception("Duplicate id found.")
        unique_ids.add(entry.id)

    # validate each date is the same
    first_date = raw_loot_list[0].date
    for entry in raw_loot_list:
        if entry.date != first_date:
            raise Exception("Dates in the new log differ from each other.")


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
