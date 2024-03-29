import pytest

from app import validate_expected_state
from tests.commons import create_test_object_raw_loot


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
