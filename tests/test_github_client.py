import pytest

from github_client import RawLoot, validate_raw_loot_list


def test_validate_raw_loot_list_empty_list():
    with pytest.raises(Exception, match="Empty list."):
        validate_raw_loot_list([])

def test_validate_raw_loot_list_duplicate_ids():
    raw_loot_list = [
        create_test_object_raw_loot({"date": "2022-01-01"}),
        create_test_object_raw_loot({"date": "2022-01-01"}),
    ]
    with pytest.raises(Exception, match="Duplicate id found."):
        validate_raw_loot_list(raw_loot_list)

def test_validate_raw_loot_list_different_dates():
    raw_loot_list = [
        create_test_object_raw_loot({"id": "1", "date": "2022-01-01"}),
        create_test_object_raw_loot({"id": "2", "date": "2022-01-02"}),
    ]
    with pytest.raises(Exception, match="Dates in the new log differ from each other."):
        validate_raw_loot_list(raw_loot_list)

def test_validate_raw_loot_list_succeeds():
    raw_loot_list = [
        create_test_object_raw_loot({"id": "1", "date": "2022-01-01"}),
        create_test_object_raw_loot({"id": "2", "date": "2022-01-01"}),
    ]
    validate_raw_loot_list(raw_loot_list)


def create_test_object_raw_loot(dict: dict):
    fields = {
        "player": dict.get("player", ""),
        "note": dict.get("note", ""),
        "response": dict.get("response", ""),
        "id": dict.get("id", ""),
        "date": dict.get("date", ""),
        "time": dict.get("time", ""),
        "itemID": dict.get("itemID", "0"),
        "itemString": dict.get("itemString", ""),
        "votes": dict.get("votes", "0"),
        "class_": dict.get("class_", ""),
        "instance": dict.get("instance", ""),
        "boss": dict.get("boss", ""),
        "gear1": dict.get("gear1", ""),
        "gear2": dict.get("gear2", ""),
        "responseID": dict.get("responseID", ""),
        "isAwardReason": dict.get("isAwardReason", ""),
        "class": dict.get("class", ""),
        "rollType": dict.get("rollType", ""),
        "subType": dict.get("subType", ""),
        "equipLoc": dict.get("equipLoc", ""),
        "owner": dict.get("owner", ""),
        "itemName": dict.get("itemName", ""),
    }
    return RawLoot(**fields)


