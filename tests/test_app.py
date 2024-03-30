from unittest.mock import patch
from app import apply_fixes, merging_logs, validate_characters_known, validate_note_values

from core import Player
from tests.commons import create_test_object_fixes, create_test_object_raw_loot
import pytest


@pytest.fixture(autouse=True)
def mock_github_client():
    # prevents github_client initialization, which loads all data from github
    with patch('app.DATABASE') as mock:
        yield mock


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
