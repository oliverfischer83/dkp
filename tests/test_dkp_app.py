from app import apply_fixes, merging_logs, validate_characters_known, validate_notes
from github_client import Player

from tests.commons import create_test_object_fixes, create_test_object_raw_loot


def test_validate_characters_known():
    known_player = [
        Player(name="Olli", chars=["Moppi", "Zelma"]),
        Player(name="Micha", chars=["Wurzel"]),
    ]
    assert len(validate_characters_known(known_player, [])) == 0
    assert len(validate_characters_known(known_player, ["Moppi"])) == 0
    assert len(validate_characters_known(known_player, ["Zelma"])) == 0
    assert len(validate_characters_known(known_player, ["Wurzel"])) == 0
    assert len(validate_characters_known(known_player, ["Moppi", "Wurzel"])) == 0
    assert len(validate_characters_known(known_player, ["Unknown"])) == 1
    assert len(validate_characters_known(known_player, ["Unknown1", "Unknown2"])) == 2


def test_validate_costs_parsable():
    """Test the number of validations for costs parsable"""
    assert len(validate_notes([""])) == 1
    assert len(validate_notes([""])) == 1
    assert len(validate_notes([" "])) == 1
    assert len(validate_notes(["w"])) == 1
    assert len(validate_notes(["_"])) == 1
    assert len(validate_notes(["A", "B"])) == 2
    assert len(validate_notes(["-80"])) == 1  # must be positive
    assert len(validate_notes(["+80"])) == 0
    assert len(validate_notes(["80"])) == 0
    assert len(validate_notes(["75"])) == 1  # must be steps of 10
    assert len(validate_notes(["0"])) == 1  # at least 10
    assert len(validate_notes(["-0"])) == 1  # at least 10
    assert len(validate_notes(["5"])) == 1  # at least 10


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
