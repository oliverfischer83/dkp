"""
Data classes concentrated into a single file to omit cyclic imports.
"""

import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


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


class FixEntry(BaseModel):
    name: str
    value: str


class Fix(BaseModel):
    id: str
    entries: list[FixEntry]


class Player(BaseModel):
    name: str
    chars: list[str]


class Raid(BaseModel):
    date: str
    report_url: str = Field(alias="report")
    attendees: list[str] = Field(alias="player")



class AdminView(BaseModel):
    date: str
    report_url: str
    player_list: Optional[list[str]]
    validations: Optional[list[str]]


class LootHistory(BaseModel):
    timestamp: datetime.datetime
    player: str
    cost: str
    item: str
    instance: str
    difficulty: str
    boss: str
    character: str


class BalanceView(BaseModel):
    season_name: str
    last_update: str
    balance: Optional[dict[str, dict[int, Any]]]
    loot_history: Optional[list[Loot]]
    validations: Optional[list[str]]

