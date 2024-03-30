import pytest

from app import validate_expected_state
from core import Raid
from github_client import get_raid_by_date
from tests.commons import create_test_object_raid, create_test_object_raw_loot


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


def test_get_raid_by_date():
    raid_list = [create_test_object_raid({"date": "2024-01-01"})]

    # Test case for existing raid
    raid_day = "2024-01-01"
    expected_raid = create_test_object_raid({"date": "2024-01-01"})
    assert get_raid_by_date(raid_list, raid_day) == expected_raid

    # Test case for non-existing raid
    raid_day = "2024-01-02"
    with pytest.raises(ValueError, match="No raid found for 2022-01-04"):
        get_raid_by_date(raid_list, raid_day)

