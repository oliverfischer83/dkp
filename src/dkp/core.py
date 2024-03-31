"""
Data classes concentrated into a single file to omit cyclic imports.
"""

import datetime
import json
from typing import Any
from pydantic import BaseModel, Field, ValidationInfo, field_validator


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
    def validate_note(cls, note, info):
        if note == "":  # empty note is valid
            return note
        message = f'Invalid note for entry {details(info)}: '
        if not note.isdigit():
            raise ValueError(message + f'Note must be a parsable integer, but was: "{note}"')
        if int(note) <= 0:
            raise ValueError(message + f'Note must be a positive value, but was: "{note}"')
        if int(note) % 10 != 0:
            raise ValueError(message + f'Note must be a multiple of 10 (e.g. 10, 20, ...), but was: "{note}"')
        return note

    @field_validator('player')
    def validate_player(cls, player, info):
        if not player:
            raise ValueError(f'Player must not be empty. {details(info)}')
        return player

    @field_validator('character')
    def validate_character(cls, character, info):
        if not character:
            raise ValueError(f'Character must not be empty. {details(info)}')
        return character

    @field_validator('response')
    def validate_response(cls, response, info):
        if not response:
            raise ValueError(f'Response must not be empty. {details(info)}')
        return response

def details(values: ValidationInfo):
    return f'(id="{values.data["id"]}", timestamp="{values.data["timestamp"]}")'


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


class FixEntry(BaseModel):
    name: str
    value: str


class Fix(BaseModel):
    id: str
    entries: list[FixEntry]


class Player(BaseModel):
    name: str
    chars: list[str]

    def __eq__(self, other):
        return isinstance(other, Player) and self.name == other.name

    def __hash__(self):
        return hash((self.name))

class Raid(BaseModel):
    date: str
    report_url: str = Field(alias="report")
    attendees: list[str] = Field(alias="player")

    def __eq__(self, other):
        return isinstance(other, Raid) and self.date == other.date

    def __hash__(self):
        return hash((self.date))

class Season(BaseModel):
    id: str
    descr: str
    order: str

    def __eq__(self, other):
        return isinstance(other, Season) and self.id == other.id

    def __hash__(self):
        return hash((self.id))


class AdminView(BaseModel):
    date: str
    report_url: str
    player_list: list[str]


class LootHistory(BaseModel):
    timestamp: datetime.datetime
    player: str
    cost: str
    item: str
    instance: str
    difficulty: str
    boss: str
    character: str


def to_raw_loot_list(content: str) -> list[RawLoot]:
    """Converts json str into raw loot lists."""
    loot_list = json.loads(content)
    return [RawLoot(**entry) for entry in loot_list]


def to_raw_date(date: str) -> str:
    """Converts date from %Y-%m-%d to %d/%m/%y."""
    return datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%-d/%-m/%y")  # like 1/1/24


def to_date(raw_date: str) -> str:
    """Converts date from %d/%m/%y to %Y-%m-%d."""
    return datetime.datetime.strptime(raw_date, "%d/%m/%y").strftime("%Y-%m-%d")  # like 2024-01-01


def to_raw_loot_json(loot_list: list[RawLoot]) -> str:
    """Converts raw loot lists into json str for database storage."""
    content = [loot.model_dump(by_alias=True) for loot in loot_list]
    sorted_content = sorted(content, key=lambda entry: entry['player'])  # sort by character name
    return to_json(sorted_content)


def to_player_json(player_list: list[Player]) -> str:
    """Converts player list into json str for database storage."""
    content = [player.model_dump() for player in player_list]
    sorted_content = sorted(content, key=lambda entry: entry['name'])  # sort by player name
    return to_json(sorted_content)


def to_json(content: Any) -> str:
    return json.dumps(content,
                      indent=2,             # beautify
                      ensure_ascii=False)   # allow non-ascii characters