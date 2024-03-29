from github_client import Fix, FixEntry, RawLoot


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


def create_test_object_fixes(id: str, entries: dict[str, str]) -> Fix:
    return Fix(id=id, entries=[FixEntry(name=name, value=value) for name, value in entries.items()])
