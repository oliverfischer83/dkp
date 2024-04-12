from core import Balance, Fix, FixEntry, Loot, Player, Raid, RawLoot, Season


def create_test_object_raw_loot(raw_loot: dict) -> RawLoot:
    fields = {
        "player": raw_loot.get("player", ""),
        "note": raw_loot.get("note", ""),
        "response": raw_loot.get("response", ""),
        "id": raw_loot.get("id", ""),
        "date": raw_loot.get("date", "2024-01-01"),
        "time": raw_loot.get("time", ""),
        "itemID": raw_loot.get("itemID", "0"),
        "itemString": raw_loot.get("itemString", ""),
        "votes": raw_loot.get("votes", "0"),
        "class_": raw_loot.get("class_", ""),
        "instance": raw_loot.get("instance", ""),
        "boss": raw_loot.get("boss", ""),
        "gear1": raw_loot.get("gear1", ""),
        "gear2": raw_loot.get("gear2", ""),
        "responseID": raw_loot.get("responseID", ""),
        "isAwardReason": raw_loot.get("isAwardReason", ""),
        "class": raw_loot.get("class", ""),
        "rollType": raw_loot.get("rollType", ""),
        "subType": raw_loot.get("subType", ""),
        "equipLoc": raw_loot.get("equipLoc", ""),
        "owner": raw_loot.get("owner", ""),
        "itemName": raw_loot.get("itemName", ""),
    }
    # sanity check
    for key in raw_loot:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return RawLoot(**fields)


def create_test_object_loot(loot: dict) -> Loot:
    fields = {
        "id": loot.get("id", ""),
        "timestamp": loot.get("timestamp", ""),
        "player": loot.get("player", "somePlayer"),
        "note": loot.get("note", "10"),
        "item_name": loot.get("item_name", ""),
        "item_link": loot.get("item_link", ""),
        "item_id": loot.get("item_id", ""),
        "boss": loot.get("boss", ""),
        "difficulty": loot.get("difficulty", ""),
        "instance": loot.get("instance", ""),
        "character": loot.get("character", "someCharacter"),
        "response": loot.get("response", "someResponse"),
    }
    # sanity check
    for key in loot:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return Loot(**fields)


def create_test_object_raid(raid: dict) -> Raid:
    fields = {
        "date": raid.get("date", ""),
        "report_id": raid.get("report_id", ""),
        "player": raid.get("player", []),
    }
    # sanity check
    for key in raid:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return Raid(**fields)


def create_test_object_season(season: dict) -> Season:
    fields = {
        "id": season.get("id", ""),
        "name": season.get("name", ""),
        "desc": season.get("desc", ""),
        "start": season.get("start", ""),
    }
    # sanity check
    for key in season:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return Season(**fields)


def create_test_object_fixes(fix_id: str, entries: dict[str, str]) -> Fix:
    return Fix(id=fix_id, entries=[FixEntry(name=name, value=value) for name, value in entries.items()])


def create_test_object_balance(balance: dict) -> Balance:
    fields = {
        "name": balance.get("name", ""),
        "value": balance.get("value", ""),
        "income": balance.get("income", ""),
        "cost": balance.get("cost", ""),
        "characters": balance.get("characters", []),
    }
    # sanity check
    for key in balance:
        if key not in fields:
            raise ValueError(f"Invalid field: {key}")
    return Balance(**fields)
