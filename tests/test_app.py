from app import apply_fixes, merging_logs, validate_characters_known, validate_expected_state, validate_note_values

from core import Player
from tests.commons import create_test_object_fixes, create_test_object_raw_loot
import pytest


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


@pytest.mark.parametrize("note_list", [
    (["w"]),
    (["_"]),
    (["A", "B"]),
    (["-80"]),
    (["75"]),
    (["0"]),
    (["-0"]),
    (["5"])
])
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
        create_test_object_fixes("2", {"character": "Zelma", "note": "10", "response": "Gebot"})
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
    with pytest.raises(ValueError, match="Respone is \"Gebot\" but empty note!"):
        validate_expected_state(raw_loot_list)

