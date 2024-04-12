import pytest
from app import (
    ATTENDANCE_BONUS,
    INITIAL_BALANCE,
    add_cost_to_balance_list,
    add_income_to_balance_list,
    apply_fixes,
    init_balance_list,
    merging_logs,
    validate_characters_known,
    validate_expected_state,
    validate_note_values,
)
from core import Player

from tests.commons import (
    create_test_object_balance,
    create_test_object_fixes,
    create_test_object_raid,
    create_test_object_raw_loot,
)


def test_validate_characters_known_fails():
    known_player = [
        Player(name="Olli", chars=["Moppi", "Zelma"]),
        Player(name="Micha", chars=["Wurzel"]),
    ]
    with pytest.raises(ValueError):
        validate_characters_known(known_player, [])
        validate_characters_known(known_player, ["Moppi", "Wurzel"])
        validate_characters_known(known_player, ["Unknown"])
        validate_characters_known(known_player, ["Unknown1", "Unknown2"])


def test_validate_characters_known_succeeds():
    known_player = [
        Player(name="Olli", chars=["Moppi", "Zelma"]),
        Player(name="Micha", chars=["Wurzel"]),
    ]
    validate_characters_known(known_player, ["Moppi"])
    validate_characters_known(known_player, ["Zelma"])
    validate_characters_known(known_player, ["Wurzel"])
    validate_characters_known(known_player, ["Moppi", "Wurzel"])


@pytest.mark.parametrize("note_list", [(["w"]), (["_"]), (["A", "B"]), (["-80"]), (["75"]), (["0"]), (["-0"]), (["5"])])
def test_validate_notes(note_list):
    with pytest.raises(ValueError):
        validate_note_values(note_list)


def test_validate_costs_succeeds():
    validate_note_values([""])
    validate_note_values([" "])
    validate_note_values(["+80"])
    validate_note_values(["80"])


def test_merging_logs():
    existing_log = [
        create_test_object_raw_loot({"id": "1", "response": "first"}),
    ]
    new_log = [
        create_test_object_raw_loot({"id": "1", "response": "second"}),
        create_test_object_raw_loot({"id": "2", "response": "second"}),
    ]
    expected_result = [
        create_test_object_raw_loot({"id": "1", "response": "first"}),
        create_test_object_raw_loot({"id": "2", "response": "second"}),
    ]
    assert merging_logs(existing_log, new_log) == expected_result


def test_apply_fixes():
    existing_log = [
        create_test_object_raw_loot({"id": "1", "player": "Unknown", "note": "10", "response": "Gebot"}),
        create_test_object_raw_loot({"id": "2", "player": "Moppi", "note": "", "response": "Pass"}),
        create_test_object_raw_loot({"id": "3", "player": "Moppi", "note": "", "response": "Pass"}),
    ]
    fixes = [
        create_test_object_fixes("1", {"character": "Known"}),
        create_test_object_fixes("2", {"character": "Zelma", "note": "10", "response": "Gebot"}),
    ]
    expected_result = [
        create_test_object_raw_loot({"id": "1", "player": "Known", "note": "10", "response": "Gebot"}),
        create_test_object_raw_loot({"id": "2", "player": "Zelma", "note": "10", "response": "Gebot"}),
        create_test_object_raw_loot({"id": "3", "player": "Moppi", "note": "", "response": "Pass"}),
    ]
    assert apply_fixes(existing_log, fixes) == expected_result


def test_validate_expected_state_empty_list():
    with pytest.raises(ValueError, match="Empty list."):
        validate_expected_state([])


def test_validate_expected_state_duplicate_ids():
    raw_loot_list = [
        create_test_object_raw_loot({"date": "2022-01-01"}),
        create_test_object_raw_loot({"date": "2022-01-01"}),
    ]
    with pytest.raises(ValueError, match="Duplicate id found."):
        validate_expected_state(raw_loot_list)


def test_validate_expected_state_different_dates():
    raw_loot_list = [
        create_test_object_raw_loot({"id": "1", "date": "2022-01-01"}),
        create_test_object_raw_loot({"id": "2", "date": "2022-01-02"}),
    ]
    with pytest.raises(ValueError, match="Dates differ from each other."):
        validate_expected_state(raw_loot_list)


def test_validate_expected_state_succeeds():
    raw_loot_list = [
        create_test_object_raw_loot({"id": "1"}),
        create_test_object_raw_loot({"id": "2"}),
    ]
    validate_expected_state(raw_loot_list)


def test_validate_expected_state_response_gebot_empty_note():
    raw_loot_list = [
        create_test_object_raw_loot({"id": "1", "response": "Gebot", "note": ""}),
    ]
    with pytest.raises(ValueError, match='Respone is "Gebot" but empty note!'):
        validate_expected_state(raw_loot_list)


def test_init_balance_list():
    player_list = [
        Player(name="Olli", chars=["Moppi", "Zelma"]),
        Player(name="Micha", chars=["Wurzel"]),
    ]
    expected_result = [
        create_test_object_balance(
            {"name": "Olli", "value": INITIAL_BALANCE, "income": INITIAL_BALANCE, "cost": 0, "characters": ["Moppi", "Zelma"]}
        ),
        create_test_object_balance(
            {"name": "Micha", "value": INITIAL_BALANCE, "income": INITIAL_BALANCE, "cost": 0, "characters": ["Wurzel"]}
        ),
    ]
    assert init_balance_list(player_list) == expected_result


def test_add_income_to_balance_list():
    balance_list = [
        create_test_object_balance({"name": "Olli", "value": 0, "income": 0, "cost": 0}),
        create_test_object_balance({"name": "Micha", "value": 0, "income": 0, "cost": 0}),
    ]
    raid_list = [create_test_object_raid({"player": ["Olli"]})]
    expected_result = [
        create_test_object_balance({"name": "Olli", "value": ATTENDANCE_BONUS, "income": ATTENDANCE_BONUS, "cost": 0}),
        create_test_object_balance({"name": "Micha", "value": 0, "income": 0, "cost": 0}),
    ]
    assert add_income_to_balance_list(balance_list, raid_list) == expected_result


def test_add_cost_to_balance_list():
    balance_list = [
        create_test_object_balance({"name": "Olli", "value": 0, "income": 0, "cost": 0}),
        create_test_object_balance({"name": "Micha", "value": 0, "income": 0, "cost": 0}),
    ]
    player_to_cost_pair = {
        "Olli": 10,
        "Micha": 0,
    }
    expected_result = [
        create_test_object_balance({"name": "Olli", "value": -10, "income": 0, "cost": -10}),
        create_test_object_balance({"name": "Micha", "value": 0, "income": 0, "cost": 0}),
    ]
    assert add_cost_to_balance_list(balance_list, player_to_cost_pair) == expected_result
