import pytest
from github_client import GithubClient
from tests.commons import create_test_object_raid

def test_get_raid_by_date(mocker):
    expected_raid = create_test_object_raid({"date": "2024-01-01"})
    another_raid = create_test_object_raid({"date": "2024-01-02"})
    raid_list = [another_raid, expected_raid]

    cls = GithubClient("no-token")
    mocker.patch.object(cls, '_load_data', return_value=raid_list)

    # Test case for existing raid
    assert cls.find_raid_by_date("2024-01-01").date == "2024-01-01"

    # Test case for non-existing raid
    with pytest.raises(Exception, match="No raid found for 2099-12-31"):
        cls.find_raid_by_date("2099-12-31")