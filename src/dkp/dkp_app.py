"""
Business logic for the DKP webapp.
"""
import datetime
import logging
import os
from typing import Any, Hashable, Optional

import pandas
from dotenv import load_dotenv
from pydantic import BaseModel

from .config_mapper import Config
from .warcraftlogs_client import WclClient

load_dotenv()
log = logging.getLogger(__name__)

INITIAL_BALANCE = 100
ATTENDANCE_BONUS = 50


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
    balance: Optional[dict[Hashable, Any]]
    loot_history: Optional[dict[Hashable, Any]]
    validations: Optional[list[str]]


def get_raw_data_from_files(export_dir):
    log.debug("get_raw_data_from_files")
    result = pandas.DataFrame()
    for file in os.listdir(export_dir):
        dataframe = pandas.read_json(os.path.join(export_dir, file), orient="records", convert_dates=False)
        result = pandas.concat([result, dataframe])
    return result


def make_clickable(val):
    log.debug("make_clickable")
    return '<a href="{}">{}</a>'.format(val, val)


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
    result.style.format({"itemLink": make_clickable})
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
    for i, player in enumerate(player_list):
        balance_list["name"][i] = player.name
        balance_list["value"][i] = INITIAL_BALANCE
        balance_list["income"][i] = INITIAL_BALANCE
        balance_list["cost"][i] = 0
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

    config = Config()

    season_name = config.season.name
    player_list = config.player_list
    loot = get_loot_from_local_files(config.season.key, player_list)
    looting_characters = list(set([value for value in loot["character"].values()]))

    validations = []
    validations.extend(validate_characters_known(player_list, looting_characters))
    validations.extend(validate_costs(loot["cost"].values()))

    if validations:
        return BalanceView(
            season_name=season_name,
            balance=None,
            loot_history=None,
            validations=validations,
        )

    balance = get_balance(player_list, config.raid_list, loot)

    return BalanceView(season_name=season_name, balance=balance, loot_history=loot, validations=None)


def get_admin_view(report_id):
    log.debug("get_admin_view")

    config = Config()

    wcl_client = WclClient(config.auth.wcl_client)
    date, report_url, raiding_char_list = wcl_client.get_raid_details(report_id)

    player_list = []
    for player in config.player_list:
        for char in raiding_char_list:
            if char in player.chars:
                player_list.append(player.name)
                break

    validations = []
    validations.extend(validate_characters_known(config.player_list, raiding_char_list))

    if validations:
        return AdminView(date=date, report_url=report_url, player_list=None, validations=validations)

    return AdminView(date=date, report_url=report_url, player_list=player_list, validations=None)
