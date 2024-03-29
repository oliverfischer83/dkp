"""
Business logic for the DKP webapp.
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import logging
import os
from typing import Any

from config_mapper import Config
from dotenv import load_dotenv
from core import AdminView, BalanceView, Fix
from github_client import GithubClient, Loot, Player, Raid, RawLoot
from warcraftlogs_client import WclClient

load_dotenv()
log = logging.getLogger(__name__)


INITIAL_BALANCE = 100
ATTENDANCE_BONUS = 50

WCL_CLIENT_ID = os.environ.get("WCL_CLIENT_ID")
WCL_CLIENT_SECRET = os.environ.get("WCL_CLIENT_SECRET")
GITHUB_TOKEN = os.environ.get("GITHUB_CLIENT_TOKEN")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

CONFIG = Config()

WCL_CLIENT = WclClient(CONFIG.auth.wcl_client, WCL_CLIENT_ID, WCL_CLIENT_SECRET)
DATABASE = GithubClient(GITHUB_TOKEN)



def get_admin_password():
    return ADMIN_PASSWORD



def get_player_to_cost_pair(player_list: list[Player], loot_table: list[Loot]) -> dict[str, int]:
    log.debug("get_player_to_cost_pair")
    result = dict()
    for player in player_list:
        result[player.name] = 0
        for loot in loot_table:
            if loot.character in player.chars:
                result[player.name] += int(loot.note)
    return result


def init_balance_table(player_list: list[Player]) -> dict[str, dict[int, Any]]:  # TODO refactor: dict[int, Any] is not very descriptive
    log.debug("init_balance_table")
    balance_list = dict()
    balance_list["name"] = dict()
    balance_list["value"] = dict()
    balance_list["income"] = dict()
    balance_list["cost"] = dict()
    balance_list["characters"] = dict()
    for i, player in enumerate(player_list):
        balance_list["name"][i] = player.name
        balance_list["value"][i] = INITIAL_BALANCE
        balance_list["income"][i] = INITIAL_BALANCE
        balance_list["cost"][i] = 0
        balance_list["characters"][i] = player.chars
    return balance_list


def add_income_to_balance_table(balance_table: dict[str, dict[int, Any]], raid_list: list[Raid]) -> dict[str, dict[int, Any]]:
    log.debug("add_income_to_balance_table")
    for i, name in balance_table["name"].items():
        for raid in raid_list:
            for raid_player_name in raid.attendees:
                if name == raid_player_name:
                    balance_table["value"][i] += ATTENDANCE_BONUS
                    balance_table["income"][i] += ATTENDANCE_BONUS
    return balance_table


def add_cost_to_balance_table(balance_table: dict[str, dict[int, Any]], player_to_cost_pair: dict[str, int]) -> dict[str, dict[int, Any]]:
    log.debug("add_cost_to_balance_table")
    for i, name in balance_table["name"].items():
        for key, value in player_to_cost_pair.items():
            player_name = key
            cost = value
            if name == player_name:
                balance_table["value"][i] -= cost
                balance_table["cost"][i] -= cost
    return balance_table


def get_balance(player_list: list[Player], raid_list: list[Raid], loot_table: list[Loot]) -> dict[str, dict[int, Any]]:
    log.debug("get_balance")
    player_to_cost_pair = get_player_to_cost_pair(player_list, loot_table)
    balance_table = init_balance_table(player_list)
    balance_table = add_income_to_balance_table(balance_table, raid_list)
    balance_table = add_cost_to_balance_table(balance_table, player_to_cost_pair)
    return balance_table


def validate_characters_known(known_player: list[Player], looting_characters: list[str]):
    known_characters = list()
    for player in known_player:
        known_characters.extend(player.chars)

    for char in looting_characters:
        if char not in known_characters:
            raise ValueError("Unknown character: " + char)


def validate_note_values(cost_list: list[str]):
    for note in cost_list:
        if note.strip() == "":
            continue
        try:
            int(note)
        except ValueError:
            raise ValueError("Note must be a parsable integer, but was: " + note)
        if int(note) < 10:
            raise ValueError("Note minimum is 10, but was: " + note)
        if int(note) % 10 != 0:
            raise ValueError("Note must be within steps of 10, but was: " + note)


def validate_expected_state(raw_loot_list: list[RawLoot]):
    # validate list is not empty
    if not raw_loot_list:
        raise ValueError("Empty list. Updated same list before?")

    # validate each entry has a unique id
    unique_ids = set()
    for entry in raw_loot_list:
        if entry.id in unique_ids:
            raise ValueError(f'Duplicate id found! (id="{entry.id}").')
        unique_ids.add(entry.id)

    # validate each date is the same
    first_date = raw_loot_list[0].date
    for entry in raw_loot_list:
        if entry.date != first_date:
            raise ValueError("Dates differ from each other.")

    # each entry having response == "Gebot" must have a non empty note
    for entry in raw_loot_list:
        if entry.response == "Gebot" and entry.note.strip() == "":
            raise ValueError(f'Respone is "Gebot" but empty note! (id="{entry.id}").')


def validate_import(raw_loot_list: list[RawLoot]):
    validate_expected_state(raw_loot_list)
    validate_characters_known(DATABASE.get_players(), [entry.player for entry in raw_loot_list])
    validate_note_values([entry.note for entry in raw_loot_list])


def get_balance_view():
    player_list = DATABASE.get_players()  # TODO refactor: player_list is already in all_loot, should not be necessary here
    season_name = CONFIG.season.name
    season_key = CONFIG.season.key

    all_loot = DATABASE.get_loot_logs_from_local_files(season_key)
    latest_entry = max(all_loot, key=lambda entry: entry.timestamp)
    relevant_loot = [entry for entry in all_loot if entry.response == "Gebot"]
    last_update = f"{latest_entry.timestamp} (Boss: {latest_entry.boss}, {latest_entry.difficulty})"

    balance = get_balance(player_list, DATABASE.get_raids(), relevant_loot)

    return BalanceView(season_name=season_name, balance=balance, loot_history=relevant_loot, last_update=last_update)


def get_admin_view(report_id):
    all_players = DATABASE.get_players()
    date, report_url, raiding_char_list = WCL_CLIENT.get_raid_details(report_id)

    # find attending players
    player_list = []
    for player in all_players:
        for char in raiding_char_list:
            if char in player.chars:
                player_list.append(player.name)
                break

    return AdminView(date=date, report_url=report_url, player_list=player_list)


def upload_loot_log(raw_loot_list: list[RawLoot]):
    season = CONFIG.season.key
    raid_day = datetime.datetime.strptime(raw_loot_list[0].date, "%d/%m/%y").strftime("%Y-%m-%d")  # first entry
    existing_log = DATABASE.get_loot_log_raw(season, raid_day)

    if existing_log:
        result = merging_logs(existing_log, raw_loot_list)
        DATABASE.update_loot_log(result, season, raid_day)
    else:
        DATABASE.create_loot_log(raw_loot_list, season, raid_day)


def apply_loot_log_fix(fixes: list[Fix], raid_day: str, reason: str):
    season = CONFIG.season.key
    existing_log = DATABASE.get_loot_log_raw(season, raid_day)
    if not existing_log:
        raise Exception(f"No loot log found! season: {season}, raid day: {raid_day}")

    result = apply_fixes(existing_log, fixes)
    DATABASE.fix_loot_log(result, season, raid_day, reason)


def get_loot_log(raid_day: str) -> list[Loot]:
    season = CONFIG.season.key
    return DATABASE.get_loot_log(season, raid_day)


def get_loot_log_raw(raid_day: str) -> list[RawLoot]:
    season = CONFIG.season.key
    return DATABASE.get_loot_log_raw(season, raid_day)


def filter_logs(existing_log: list[RawLoot], new_log: list[RawLoot]) -> list[RawLoot]:
    existing_ids = {loot.id for loot in existing_log}
    return [item for item in new_log if item.id not in existing_ids]


def merging_logs(existing_log: list[RawLoot], new_log: list[RawLoot]) -> list[RawLoot]:
    result = existing_log
    existing_ids = [loot.id for loot in existing_log]
    for item in new_log:
        if item.id not in existing_ids:
            result.append(item)
    return result


def apply_fixes(existing_log: list[RawLoot], fixes: list[Fix]):
    result = existing_log
    for fix in fixes:
        for loot in existing_log:
            if loot.id == fix.id:
                for e in fix.entries:
                    if e.name == "character":
                        # hack:
                        #   due to naming clash between player and character
                        #   clean up function shifted raw field 'player' to clean field 'character'
                        #   need to revert here
                        loot.player = e.value
                    elif e.name == "note":
                        loot.note = e.value
                    elif e.name == "response":
                        loot.response = e.value
                    else:
                        # sanity check
                        raise Exception(f"Invalid key: {e.name}")
    return result
