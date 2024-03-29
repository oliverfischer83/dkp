import pytest

from github_client import validate_raw_loot_list
from tests.commons import create_test_object_raw_loot


def test_validate_raw_loot_list_empty_list():
    with pytest.raises(ValueError, match="Empty list."):
        validate_raw_loot_list([])

def test_validate_raw_loot_list_duplicate_ids():
    raw_loot_list = [
        create_test_object_raw_loot({"date": "2022-01-01"}),
        create_test_object_raw_loot({"date": "2022-01-01"}),
    ]
    with pytest.raises(ValueError, match="Duplicate id found."):
        validate_raw_loot_list(raw_loot_list)

def test_validate_raw_loot_list_different_dates():
    raw_loot_list = [
        create_test_object_raw_loot({"id": "1", "date": "2022-01-01"}),
        create_test_object_raw_loot({"id": "2", "date": "2022-01-02"}),
    ]
    with pytest.raises(ValueError, match="Dates differ from each other."):
        validate_raw_loot_list(raw_loot_list)

def test_validate_raw_loot_list_succeeds():
    raw_loot_list = [
        create_test_object_raw_loot({"id": "1"}),
        create_test_object_raw_loot({"id": "2"}),
    ]
    validate_raw_loot_list(raw_loot_list)


