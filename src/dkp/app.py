"""
Business logic for the DKP webapp.
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import logging
import os

import toml
from config_mapper import Config
from core import (
    Balance,
    Fix,
    FixEntry,
    RaidChecklist,
    Season,
    get_evn_var,
    is_local_development,
    list_to_csv,
    to_date,
    today,
)
from dotenv import load_dotenv
from github_client import GithubClient, Loot, Player, Raid, RawLoot, csv_to_list
from warcraftlogs_client import WclClient

load_dotenv()
log = logging.getLogger(__name__)

PROJECT_DATA = toml.load("pyproject.toml")
PROJECT_VERSION = PROJECT_DATA["project"]["version"]

WCL_CLIENT_ID = get_evn_var("WCL_CLIENT_ID")
WCL_CLIENT_SECRET = get_evn_var("WCL_CLIENT_SECRET")
GITHUB_TOKEN = get_evn_var("GITHUB_CLIENT_TOKEN")
ADMIN_PASSWORD = get_evn_var("ADMIN_PASSWORD")
BRANCH_NAME = get_evn_var("BRANCH_NAME")

CONFIG = Config()

WCL_CLIENT = WclClient(CONFIG.auth.wcl_client, WCL_CLIENT_ID, WCL_CLIENT_SECRET)
DATABASE = GithubClient(BRANCH_NAME, GITHUB_TOKEN)


INITIAL_BALANCE = 100
ATTENDANCE_BONUS = 50


def get_admin_password():
    return ADMIN_PASSWORD if not is_local_development() else ""


def get_player_to_cost_pair(player_list: list[Player], loot_table: list[Loot]) -> dict[str, int]:
    log.debug("get_player_to_cost_pair")
    result = {}
    for player in player_list:
        result[player.name] = 0
        for loot in loot_table:
            if loot.character in player.chars:
                result[player.name] += int(loot.note)
    return result


def init_balance_list(player_list: list[Player]) -> list[Balance]:
    log.debug("init_balance_list")
    return [
        Balance(name=player.name, value=INITIAL_BALANCE, income=INITIAL_BALANCE, cost=0, characters=player.chars) for player in player_list
    ]


def add_income_to_balance_list(balance_list: list[Balance], raid_list: list[Raid]) -> list[Balance]:
    log.debug("add_income_to_balance_list")
    for balance in balance_list:
        for raid in raid_list:
            for raid_player_name in raid.player:
                if balance.name == raid_player_name:
                    balance.value += ATTENDANCE_BONUS
                    balance.income += ATTENDANCE_BONUS
    return balance_list


def add_cost_to_balance_list(balance_list: list[Balance], player_to_cost_pair: dict[str, int]) -> list[Balance]:
    log.debug("add_cost_to_balance_list")
    for balance in balance_list:
        cost = player_to_cost_pair.get(balance.name, 0)
        balance.value -= cost
        balance.cost -= cost
    return balance_list


def filter_by_active_player(balance_list: list[Balance], season: Season) -> list[Balance]:
    active_player = set()
    raid_list = get_raid_list(season)
    for raid in raid_list:
        for player in raid.player:
            active_player.add(player)

    result = []
    for balance in balance_list:
        if balance.name in active_player:
            result.append(balance)
    return result


def get_balance(season: Season) -> list[Balance]:
    log.debug("get_balance")
    loot = get_loot_history(season)
    player_to_cost_pair = get_player_to_cost_pair(DATABASE.player_list, loot)
    balance_list = init_balance_list(DATABASE.player_list)
    balance_list = add_income_to_balance_list(balance_list, DATABASE.get_raid_list(season))
    balance_list = add_cost_to_balance_list(balance_list, player_to_cost_pair)
    return balance_list


def validate_characters_known(known_player: list[Player], looting_characters: list[str]):
    known_characters = []
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
        except ValueError as e:
            raise ValueError("Note must be a parsable integer, but was: " + note) from e
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
    validate_characters_known(DATABASE.player_list, [entry.player for entry in raw_loot_list])
    validate_note_values([entry.note for entry in raw_loot_list])


def get_info_last_update(season: Season) -> tuple[str, str, str]:
    all_loot = DATABASE.get_season_loot(season)
    if not all_loot:
        return "1970-01-01 00:00:00", "unknown", "unknown"
    last_entry = max(all_loot, key=lambda entry: entry.timestamp)
    return last_entry.timestamp, last_entry.boss, last_entry.difficulty


def get_loot_history(season: Season) -> list[Loot]:
    season_loot = DATABASE.get_season_loot(season)
    return [entry for entry in season_loot if entry.response == "Gebot"]


def get_attending_player_list(report_id):
    char_list = WCL_CLIENT.get_attending_character_list(report_id)
    # find attending players
    player_list = []
    for player in DATABASE.player_list:
        for char in char_list:
            if char in player.chars:
                player_list.append(player.name)
                break
    return player_list


def upload_loot_log(raw_loot_list: list[RawLoot]):
    raid_day = to_date(raw_loot_list[0].date)
    existing_log = DATABASE.get_raid_loot_raw(raid_day)

    if existing_log:
        result = merging_logs(existing_log, raw_loot_list)
        DATABASE.update_loot_log(result, raid_day)
    else:
        DATABASE.create_loot_log(raw_loot_list, raid_day)


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


def apply_fix_to_loot_log(fixes: list[Fix], raid_day: str, reason: str):
    existing_log = DATABASE.get_raid_loot_raw(raid_day)
    if not existing_log:
        raise ValueError(f"No loot log found! raid day: {raid_day}")
    result = apply_fixes(existing_log, fixes)
    DATABASE.fix_loot_log(result, raid_day, reason)


def apply_fixes(existing_log: list[RawLoot], fixes: list[Fix]) -> list[RawLoot]:
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
                        raise KeyError(f"Invalid key: {e.name}")
    return result


def get_current_season() -> Season:
    current_day = today()
    possible_seasons = [season for season in DATABASE.season_list if season.start_date < current_day]
    if possible_seasons:
        return max(possible_seasons, key=lambda season: season.start_date)
    else:
        raise ValueError("No season found for current date: " + current_day)


def get_season_list_starting_with_current() -> list[Season]:
    current = get_current_season()
    others = DATABASE.season_list.copy()
    others.remove(current)
    return [current] + others


def get_current_raid() -> Raid | None:
    current_day = today()
    try:
        return DATABASE.find_raid_by_date(current_day)
    except ValueError:
        return None


def find_raid_by_date(date: str) -> Raid:
    return DATABASE.find_raid_by_date(date)


def get_raid_loot(raid_day: str) -> list[Loot]:
    return DATABASE.get_raid_loot(raid_day)


def get_raid_loot_raw(raid_day: str) -> list[RawLoot]:
    return DATABASE.get_raid_loot_raw(raid_day)


def get_player_list() -> list[Player]:
    return DATABASE.player_list


def get_absent_player_list() -> list[Player]:
    return DATABASE.get_absent_player_list()


def get_raid_list(season: Season) -> list[Raid]:
    return DATABASE.get_raid_list(season)


def get_empty_raid_list(season: Season) -> list[Raid]:
    return DATABASE.get_empty_raid_list(season)


def get_season_list() -> list[Season]:
    return DATABASE.season_list


def get_empty_season_list() -> list[Season]:
    return DATABASE.get_empty_season_list()


def add_player(player_name: str):
    if any(player.name == player_name for player in DATABASE.player_list):
        raise ValueError("Player with name already exists: " + player_name)
    else:
        DATABASE.add_player(player_name)


def delete_player(player_name: str):
    DATABASE.delete_player(player_name)


def update_player(fixes: list[Fix]):
    for fix in fixes:
        for e in fix.entries:
            if e.name == "name":
                if any(player.name == e.value for player in DATABASE.player_list):
                    raise ValueError("Player with name already exists: " + fix.entries[0].value)
            elif e.name == "chars":
                for char in csv_to_list(e.value):
                    try:
                        DATABASE.find_player_by_character(char)
                        raise AttributeError(f"Player with character name '{char}' already exists.")
                    except ValueError:
                        pass  # character name not alredy taken
            else:
                raise KeyError(f"Invalid key: {e.name}")  # sanity check
    DATABASE.update_player(fixes)


def add_raid(date: str):
    DATABASE.add_raid(date)


def start_raid():
    date = today()
    DATABASE.add_raid(date)


def stop_raid():
    raid = get_current_raid()
    if not raid:
        raise ValueError("No raid found for today.")
    if not raid.report_id:
        raise ValueError("No report id found for today's raid.")

    player_list = get_attending_player_list(raid.report_id)
    raid.player = player_list

    fixes = [Fix(id=str(raid.id), entries=[FixEntry(name="player", value=list_to_csv(player_list))])]
    _update_raid(fixes)


def update_raid(fixes: list[Fix]):
    _update_raid(fixes)


def _update_raid(fixes: list[Fix]):
    DATABASE.update_raid(fixes)
    balance_list = {balance.name: str(balance.value) for balance in get_balance(get_current_season())}
    DATABASE.create_raid_excel_file(balance_list)


def delete_raid(raid_date: str):
    DATABASE.delete_raid(raid_date)


def add_season(season_name: str):
    DATABASE.add_season(season_name)


def delete_season(season_desc: str):
    DATABASE.delete_season(season_desc)


def update_season(fixes: list[Fix]):
    DATABASE.update_season(fixes)


def get_raid_checklist() -> RaidChecklist:
    return DATABASE.raid_checklist


def update_raid_checklist(checklist: RaidChecklist):
    DATABASE.update_raid_checklist(checklist)


def is_raid_started() -> bool:
    # if a raid is found
    return bool(get_current_raid())


def is_raid_stopped() -> bool:
    # if no raid is found or raid is found but no player is assigned
    raid = get_current_raid()
    return not bool(raid) or bool(raid.player)


def find_past_raids_without_attendees() -> list[str]:
    result = []
    for raid in DATABASE.raid_list:
        if raid == get_current_raid():
            continue
        if not raid.player:
            result.append(raid.date)
    return result


def find_player_with_negative_balance(balance_list: list[Balance]) -> list[str]:
    return [balance.name for balance in balance_list if balance.value < 0]


def get_example_zones():
    return WCL_CLIENT.get_example_for_zones()


def get_example_rate_limits():
    return WCL_CLIENT.get_example_for_rate_limits()


def get_example_report(code: str):
    return WCL_CLIENT.get_example_for_report(code)


def get_example_player_details(code: str):
    return WCL_CLIENT.get_example_for_player_details(code)


def get_example_report_debug(code: str):
    return WCL_CLIENT.get_example_for_debugging_report(code)
