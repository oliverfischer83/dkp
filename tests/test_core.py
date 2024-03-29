import pytest
from core import Loot, to_date, to_raw_date
from tests.commons import create_test_object_loot


def test_to_date_succeeds():
    expected_date = "2024-01-01"
    assert to_date("1/1/24") == expected_date
    assert to_date("01/1/24") == expected_date
    assert to_date("1/01/24") == expected_date
    assert to_date("01/01/24") == expected_date


def test_to_raw_date_succeeds():
    assert to_raw_date("2024-01-01") == "1/1/24"
    assert to_raw_date("2024-12-01") == "1/12/24"
    assert to_raw_date("2024-01-21") == "21/1/24"
    assert to_raw_date("2024-12-20") == "20/12/24"


@pytest.mark.parametrize("field_list", [
    # {"id": ""},
    # {"timestamp": ""},
    {"player": ""},
    {"note": "-10"},
    # {"item_name": ""},
    # {"item_link": ""},
    # {"item_id": ""},
    # {"boss": ""},
    # {"difficulty": ""},
    # {"instance": ""},
    {"character": ""},
    {"response": ""}
])
def test_validate_loot_fails(field_list):
    with pytest.raises(ValueError):
        create_test_object_loot(field_list)
        pass
    pass


def test_validate_loot_succeeds():
    Loot(
        id="1",
        timestamp="2024-01-01 00:00:00",
        player="player",
        note="10",
        item_name="item_name",
        item_link="item_link",
        item_id="item_id",
        boss="boss",
        difficulty="difficulty",
        instance="instance",
        character="character",
        response="response",
    )