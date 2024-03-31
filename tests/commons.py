from core import Fix, FixEntry, Loot, Player, Raid, RawLoot


def create_test_object_raw_loot(dict: dict) -> RawLoot:
    fields = {
        "player": dict.get("player", ""),
        "note": dict.get("note", ""),
        "response": dict.get("response", ""),
        "id": dict.get("id", ""),
        "date": dict.get("date", "2024-01-01"),
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
    # sanity check
    for key in dict:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return RawLoot(**fields)


def create_test_object_loot(dict: dict) -> Loot:
    fields = {
        "id": dict.get("id", ""),
        "timestamp": dict.get("timestamp", ""),
        "player": dict.get("player", "somePlayer"),
        "note": dict.get("note", "10"),
        "item_name": dict.get("item_name", ""),
        "item_link": dict.get("item_link", ""),
        "item_id": dict.get("item_id", ""),
        "boss": dict.get("boss", ""),
        "difficulty": dict.get("difficulty", ""),
        "instance": dict.get("instance", ""),
        "character": dict.get("character", "someCharacter"),
        "response": dict.get("response", "someResponse"),
    }
    # sanity check
    for key in dict:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return Loot(**fields)


def create_test_object_raid(dict: dict) -> Raid:
    fields = {
        "date": dict.get("date", ""),
        "report": dict.get("report", ""),
        "player": dict.get("player", []),
    }
    # sanity check
    for key in dict:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return Raid(**fields)


def create_test_object_fixes(id: str, entries: dict[str, str]) -> Fix:
    return Fix(id=id, entries=[FixEntry(name=name, value=value) for name, value in entries.items()])


def create_test_object_player_list(player_list: list[Player]) -> list[Player]:
    return []
