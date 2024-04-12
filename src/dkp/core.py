"""
Data classes concentrated into a single file to omit cyclic imports.
"""

import datetime
import json
import os

import pytz
from pydantic import BaseModel, Field, ValidationInfo, field_validator

ORIGINAL = "original"
CHANGE = "change"


def is_local_development() -> bool:
    # used to speed up testing
    return os.environ.get("LOCAL_DEVELOPMENT", "false").lower() == "true"


def get_evn_var(name: str):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"{name} not set in environment variables.")
    return value


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

    @field_validator("note")
    def validate_note(cls, note, info):
        if note == "":  # empty note is valid
            return note
        message = f"Invalid note for entry {details(info)}: "
        if not note.isdigit():
            raise ValueError(message + f'Note must be a parsable integer, but was: "{note}"')
        if int(note) <= 0:
            raise ValueError(message + f'Note must be a positive value, but was: "{note}"')
        if int(note) % 10 != 0:
            raise ValueError(message + f'Note must be a multiple of 10 (e.g. 10, 20, ...), but was: "{note}"')
        return note

    @field_validator("player")
    def validate_player(cls, player, info):
        if not player:
            raise ValueError(f"Player must not be empty. {details(info)}")
        return player

    @field_validator("character")
    def validate_character(cls, character, info):
        if not character:
            raise ValueError(f"Character must not be empty. {details(info)}")
        return character

    @field_validator("response")
    def validate_response(cls, response, info):
        if not response:
            raise ValueError(f"Response must not be empty. {details(info)}")
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
    id: int = 0
    name: str
    chars: list[str]

    def __eq__(self, other):
        return isinstance(other, Player) and self.id == other.id

    def __hash__(self):
        return hash((self.id))


class Raid(BaseModel):
    id: int = 0
    date: str
    report_id: str
    player: list[str]

    def __eq__(self, other):
        return isinstance(other, Raid) and self.id == other.id

    def __hash__(self):
        return hash((self.id))


class Season(BaseModel):
    id: int = 0
    name: str
    desc: str
    start_date: str

    def __eq__(self, other):
        return isinstance(other, Season) and self.id == other.id

    def __hash__(self):
        return hash((self.id))


class RaidChecklist(BaseModel):
    video_recording: bool = False
    logs_recording: bool = False
    rclc_installed: bool = False
    consumables: bool = False

    def is_fullfilled(self) -> bool:
        return self.video_recording and self.logs_recording and self.rclc_installed and self.consumables


class Balance(BaseModel):
    name: str
    value: int = 0
    income: int = 0
    cost: int = 0
    characters: list[str]


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


def to_timestamp(raw_timestamp: str) -> str:
    return datetime.datetime.strptime(raw_timestamp, "%d/%m/%y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")  # like 2024-01-01 00:00:00


def csv_to_list(csv: str) -> list[str]:
    return [item.strip() for item in csv.split(",") if csv]  # "a, b, c" -> ["a", "b", "c"] and "" -> []


def list_to_csv(list_of_strings: list[str]) -> str:
    return ", ".join(list_of_strings)  # ["a", "b", "c"] -> "a, b, c"


def dict_to_csv(dict_: dict[str, str]) -> str:
    return "\n".join([f"{key},{value}" for key, value in dict_.items()])  # {"a": "1", "b": "2", "c": "3"} -> "a,1\nb,2\nc,3"


def today() -> str:
    return datetime.date.today().isoformat()


def now() -> str:
    """Returns current time in Europe/Berlin timezone."""
    return datetime.datetime.now(pytz.timezone("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
