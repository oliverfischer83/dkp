"""
Business logic for the DKP webapp.
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
from io import StringIO
import logging
import os
from typing import Any, Optional

import pandas
from config_mapper import Config, Player, Raid
from dotenv import load_dotenv
from github_client import GithubClient, to_python
from pydantic import BaseModel
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
    loot_history: Optional[list[dict[str, Any]]]
    validations: Optional[list[str]]


def get_admin_password():
    return ADMIN_PASSWORD


def modify_data(data: list[dict[str, str]], player_list: list[Player]) -> list[dict[str, str]]:
    result = []
    for data_entry in data:
        entry = data_entry.copy()
        # add item link
        entry["item_link"] = f"https://www.wowhead.com/item={entry["item_id"]}"
        # add player name
        for player in player_list:
            if entry["character"] in player.chars:
                entry["player"] = player.name
                break
        result.append(entry)
    return sorted(result, key=lambda entry: entry["timestamp"], reverse=True)


def filter_data(data: list[dict[str, str]]) -> list[dict[str, str]]:
    # remove non-bid entries (irrelevant for loot history)
    return [entry.copy() for entry in data if entry["response"] == "Gebot"]


def get_player_to_cost_pair(player_list: list[Player], loot_table: list[dict[str, str]]) -> dict[str, int]:
    log.debug("get_player_to_cost_pair")
    result = dict()
    for player in player_list:
        result[player.name] = 0
        for i in range(len(loot_table)):
            char_name = loot_table[i]["character"]
            if char_name in player.chars:
                result[player.name] += int(loot_table[i]["note"])
    return result


def init_balance_table(player_list: list[Player]) -> dict[str, dict[int, Any]]:
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
            for raid_player_name in raid.player:
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


def get_balance(player_list: list[Player], raid_list: list[Raid], loot_table: list[dict[str, str]]) -> dict[str, dict[int, Any]]:
    log.debug("get_balance")
    player_to_cost_pair = get_player_to_cost_pair(player_list, loot_table)
    balance_table = init_balance_table(player_list)
    balance_table = add_income_to_balance_table(balance_table, raid_list)
    balance_table = add_cost_to_balance_table(balance_table, player_to_cost_pair)
    return balance_table


def validate_characters_known(known_player, looting_characters):
    log.debug("validate_characters_known")
    known_characters = list()
    for player in known_player:
        for char in player.chars:
            known_characters.append(char)

    result = []
    for char in looting_characters:
        if char not in known_characters:
            result.append("Unknown character: " + char)
    return result


def validate_notes(cost_list):
    log.debug("validate_notes")
    result = []
    for cost in cost_list:
        try:
            int(cost)
        except ValueError:
            result.append("Cost must be an integer, but was: " + cost)
            continue
        if int(cost) < 10:
            result.append("Cost minimum is 10, but was: " + cost)
            continue
        if int(cost) % 10 != 0:
            result.append("Cost must be within steps of 10, but was: " + cost)
            continue
    return result


def get_balance_view():
    log.debug("get_balance_view")

    player_list = CONFIG.player_list
    season_name = CONFIG.season.name
    season_key = CONFIG.season.key

    all_loot = DATABASE.get_loot_log_all(season_key)
    modified_loot = modify_data(all_loot, player_list)
    first_entry = modified_loot[0]
    filtered_loot = filter_data(modified_loot)
    looting_characters = list(set([entry["character"] for entry in filtered_loot]))
    last_update = f"{first_entry["timestamp"]} (Boss: {first_entry["boss"]}, {first_entry["difficulty"]})"

    validations = []
    validations.extend(validate_characters_known(player_list, looting_characters))
    validations.extend(validate_notes([entry["note"] for entry in filtered_loot]))

    if validations:
        return BalanceView(
            season_name=season_name,
            last_update="",
            balance=None,
            loot_history=None,
            validations=validations,
        )

    balance = get_balance(player_list, CONFIG.raid_list, filtered_loot)

    return BalanceView(season_name=season_name, balance=balance, loot_history=filtered_loot, last_update=last_update, validations=None)


def get_admin_view(report_id):
    log.debug("get_admin_view")

    all_players = CONFIG.player_list
    date, report_url, raiding_char_list = WCL_CLIENT.get_raid_details(report_id)

    player_list = []
    for player in all_players:
        for char in raiding_char_list:
            if char in player.chars:
                player_list.append(player.name)
                break

    validations = []
    validations.extend(validate_characters_known(all_players, raiding_char_list))

    if validations:
        return AdminView(date=date, report_url=report_url, player_list=None, validations=validations)

    return AdminView(date=date, report_url=report_url, player_list=player_list, validations=None)


# TODO test case
def update_or_create_loot_log(new_log_str: str):

    # validate each date is the same
    # TODO: try not to use pandas for this
    new_loot_df = pandas.read_json(StringIO(new_log_str), orient="records", convert_dates=False)
    first_date = new_loot_df["date"][0]
    for date in new_loot_df["date"]:
        if date != first_date:
            raise Exception("Dates in the dataframe differ from each other.")

    season = CONFIG.season.key
    raid_day = datetime.datetime.strptime(first_date, "%d/%m/%y").strftime("%Y-%m-%d")
    new_log = to_python(new_log_str)
    existing_log = DATABASE.get_loot_log(season, raid_day)

    if existing_log:
        # appending new logs to existing loot log
        unique_ids = set()
        filtered_log = []
        for item in existing_log + new_log:
            if item["id"] not in unique_ids:
                filtered_log.append(item)
                unique_ids.add(item["id"])
        DATABASE.update_loot_log(filtered_log, season, raid_day)
    else:
        # create new loot log
        DATABASE.create_loot_log(new_log, season, raid_day)


def apply_loot_log_fix(fixes: dict[str, dict[str, str]], raid_day: str, reason: str):

    season = CONFIG.season.key
    existing_log = DATABASE.get_loot_log(season, raid_day, raw=True)
    if not existing_log:
        raise Exception(f"No loot log found! season: {season}, raid day: {raid_day}")

    # apply fixes
    for fix_id, fix in fixes.items():
        for loot in existing_log:
            if loot["id"] == fix_id:
                for key, value in fix.items():
                    if key == "character":  # hack: clean up renamed player > character, need to revert here
                        loot["player"] = value
                    else:
                        loot[key] = value
                    loot["data_status"] = "fixed"  # indicate that this loot has been fixed

    DATABASE.fix_loot_log(existing_log, season, raid_day, reason)


def get_loot_log(raid_day: str) -> list[dict[str, str]]:
    season = CONFIG.season.key
    loot_log_content = DATABASE.get_loot_log(season, raid_day)
    if loot_log_content is None:
        return []
    return loot_log_content


def reload_config():
    CONFIG.reload_config()
