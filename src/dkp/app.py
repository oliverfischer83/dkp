"""
Business logic for the DKP webapp.
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
from io import StringIO
import logging
import os
from typing import Any, Hashable, Optional

import pandas
from config_mapper import Config
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
    balance: Optional[dict[Hashable, Any]]
    loot_history: Optional[dict[Hashable, Any]]
    validations: Optional[list[str]]


def get_admin_password():
    return ADMIN_PASSWORD


def get_raw_data_from_files(export_dir):
    log.debug("get_raw_data_from_files")
    result = pandas.DataFrame()
    for file in os.listdir(export_dir):
        dataframe = pandas.read_json(os.path.join(export_dir, file), orient="records", convert_dates=False)
        result = pandas.concat([result, dataframe])
    return result


def modify_data(dataframe, player_list):
    log.debug("modify_data")
    result = dataframe.copy()
    # remove irrelevant data, need bids only
    result = result[result["response"] == "Gebot"]
    # creating timestamp column
    result["timestamp"] = result["date"] + " " + result["time"]
    result["timestamp"] = pandas.to_datetime(result["timestamp"], format="%d/%m/%y %H:%M:%S", dayfirst=True)
    result.set_index("timestamp")
    # creating item link column
    result["itemLink"] = "https://www.wowhead.com/item=" + result["itemID"].astype(str)
    # renaming columns
    result = result.rename(columns={"player": "character"})
    result = result.rename(columns={"itemName": "item"})
    result = result.rename(columns={"note": "cost"})
    # create and fill column 'player' using mapping table like {'Moppi': 'Olli', 'Zelma': 'Olli', ...}
    result["player"] = result["character"].map(lambda x: next((player.name for player in player_list if x in player.chars), None))
    # create difficulty column
    result["difficulty"] = result["instance"].str.split("-").str[1]
    # substring of instance name
    result["instance"] = result["instance"].str.split(",").str[0]
    # substring of boss name
    result["boss"] = result["boss"].str.split(",").str[0]
    # select and sort columns
    result = result[
        [
            "timestamp",
            "player",
            "cost",
            "item",
            "itemLink",
            "instance",
            "difficulty",
            "boss",
            "character",
        ]
    ]
    result = result.sort_values(by=["timestamp"], ascending=False, ignore_index=True)
    return result.to_dict()


def get_loot_from_local_files(season_key, player_list):
    log.debug("get_loot_from_local_files")
    raw_data = get_raw_data_from_files(os.path.join("data", "season", season_key))
    return modify_data(raw_data, player_list)


def get_player_to_cost_pair(player_list, loot_table):
    log.debug("get_player_to_cost_pair")
    result = dict()
    for player in player_list:
        result[player.name] = 0
        for i, char_name in enumerate(loot_table["character"].values()):
            if char_name in player.chars:
                result[player.name] += int(loot_table["cost"][i])
    return result


def init_balance_table(player_list):
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


def add_income_to_balance_table(balance_table, raid_list):
    log.debug("add_income_to_balance_table")
    for i, name in balance_table["name"].items():
        for raid in raid_list:
            for raid_player_name in raid.player:
                if name == raid_player_name:
                    balance_table["value"][i] += ATTENDANCE_BONUS
                    balance_table["income"][i] += ATTENDANCE_BONUS
    return balance_table


def add_cost_to_balance_table(balance_table, player_to_cost_dict):
    log.debug("add_cost_to_balance_table")
    for i, name in balance_table["name"].items():
        for key, value in player_to_cost_dict.items():
            player_name = key
            cost = value
            if name == player_name:
                balance_table["value"][i] -= cost
                balance_table["cost"][i] -= cost
    return balance_table


def get_balance(player_list, raid_list, loot_table):
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


def validate_costs(cost_list):
    log.debug("validate_costs")
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

    season_name = CONFIG.season.name
    player_list = CONFIG.player_list
    loot = get_loot_from_local_files(CONFIG.season.key, player_list)
    looting_characters = list(set([value for value in loot["character"].values()]))
    last_update = str(loot["timestamp"][0]) + " (Boss: " + str(loot["boss"][0]) + ", " + str(loot["difficulty"][0]) + ")"

    validations = []
    validations.extend(validate_characters_known(player_list, looting_characters))
    validations.extend(validate_costs(loot["cost"].values()))

    if validations:
        return BalanceView(
            season_name=season_name,
            last_update="",
            balance=None,
            loot_history=None,
            validations=validations,
        )

    balance = get_balance(player_list, CONFIG.raid_list, loot)

    return BalanceView(season_name=season_name, balance=balance, loot_history=loot, last_update=last_update, validations=None)


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
    existing_log = DATABASE.get_loot_log(season, raid_day)
    if not existing_log:
        raise Exception(f"No loot log found! season: {season}, raid day: {raid_day}")

    # apply fixes
    for fix_id, fix in fixes.items():
        for loot in existing_log:
            if loot["id"] == fix_id:
                for key, value in fix.items():
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
