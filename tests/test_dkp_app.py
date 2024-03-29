# Checking the import path
# import sys
# print(sys.path)
import os

from unittest import mock
from unittest.mock import patch

from dkp.config_mapper import Player
from . import app as app


def test_get_balance():
    player_list = [
        Player(name="Olli", chars=["Moppi", "Zelma"]),
        Player(name="Micha", chars=["Wurzel"]),
        Player(name="Tanja", chars=["Blair"]),
    ]
    raid_list = ["Moppi", "Wurzel"]
    char_to_cost_pair = [("Moppi", "10"), ("Moppi", "20")]
    #
    # balance_list = app.get_balance(player_list, raid_list, char_to_cost_pair)
    # assert len(balance_list) == 3
    # assert balance_list['Olli'] == 0
    #


def test_validate_characters_known():
    known_player = [
        Player(name="Olli", chars=["Moppi", "Zelma"]),
        Player(name="Micha", chars=["Wurzel"]),
    ]
    assert len(app.validate_characters_known(known_player, [])) == 0
    assert len(app.validate_characters_known(known_player, ["Moppi"])) == 0
    assert len(app.validate_characters_known(known_player, ["Zelma"])) == 0
    assert len(app.validate_characters_known(known_player, ["Wurzel"])) == 0
    assert len(app.validate_characters_known(known_player, ["Moppi", "Wurzel"])) == 0
    assert len(app.validate_characters_known(known_player, ["Unknown"])) == 1
    assert len(app.validate_characters_known(known_player, ["Unknown1", "Unknown2"])) == 2



def test_validate_costs_parsable():
    """Test the number of validations for costs parsable"""
    assert len(app.validate_costs([""])) == 1
    assert len(app.validate_costs([""])) == 1
    assert len(app.validate_costs([" "])) == 1
    assert len(app.validate_costs(["w"])) == 1
    assert len(app.validate_costs(["_"])) == 1
    assert len(app.validate_costs(["A", "B"])) == 2
    assert len(app.validate_costs(["-80"])) == 1  # must be positive
    assert len(app.validate_costs(["+80"])) == 0
    assert len(app.validate_costs(["80"])) == 0
    assert len(app.validate_costs(["75"])) == 1  # must be steps of 10
    assert len(app.validate_costs(["0"])) == 1  # at least 10
    assert len(app.validate_costs(["-0"])) == 1  # at least 10
    assert len(app.validate_costs(["5"])) == 1  # at least 10


#
# @patch("builtins.open")
# def test_get_of_not_existing_disclosure_document(mock_file_open):
#     """Testing the get of a not existing disclosure document"""
#     mock_file_open.side_effect = FileNotFoundError
#
#     disclosure = util.get_disclosure_document()
#     assert disclosure == "No disclosure document exists"
#
#
# @patch("builtins.open", mock.mock_open(read_data="Some;Data"))
# def test_get_of_disclosure_document():
#     """Testing the get of a not existing disclosure document"""
#
#     disclosure = util.get_disclosure_document()
#     assert disclosure == "Some;Data"
#
#
# @patch.dict(os.environ, {"DEVELOPMENT_MODE_LOCAL": "True"}, clear=True)
# def test_get_version_for_locale_run():
#     """Testing the get of the module version"""
#
#     version = util.get_version()
#     assert version == "local"
#
#
# @patch.dict(
#     os.environ, {"MODULE_IMAGE_TAG": "testImage", "DEVELOPMENT_MODE_LOCAL": "False"}, clear=True
# )
# def test_get_version_of_image():
#     """Testing the get of the module version"""
#
#     version = util.get_version()
#     assert version == "testImage"
#
#
# @patch.dict(os.environ, {"MODULE_IMAGE_TAG": "main", "DEVELOPMENT_MODE_LOCAL": "False"}, clear=True)
# def test_getversion_of_main_image():
#     """Testing the get of the module version"""
#
#     version = util.get_version()
#     assert version == am_test_oliver2.__version__


# from datetime import datetime
# from unittest.mock import patch

# from dkp.dkp_app import modify_data


# @patch("src.dkp.dkp_app.pandas")
# def test_modify_data(mock_pandas):
#     # Mock input data
#     dataframe = mock_pandas.DataFrame()
#     player_list = [
#         Player(name="Olli", chars=["Moppi", "Zelma"]),
#         Player(name="Micha", chars=["Wurzel"]),
#     ]

#     # Mock expected output data
#     expected_result = {
#         "timestamp": [datetime(2022, 1, 1, 12, 0, 0)],
#         "player": ["Olli"],
#         "cost": ["10"],
#         "item": ["Some Item"],
#         "instance": ["Instance"],
#         "difficulty": ["Normal"],
#         "boss": ["Boss"],
#         "character": ["Moppi"],
#     }

#     # Mock pandas DataFrame methods
#     mock_dataframe = mock_pandas.DataFrame.return_value
#     mock_dataframe.copy.return_value = mock_dataframe
#     mock_dataframe.__getitem__.side_effect = [
#         mock_pandas.Series(["Gebot"]),
#         mock_pandas.Series(["01/01/22"]),
#         mock_pandas.Series(["12:00:00"]),
#         mock_pandas.Series(["Some Item"]),
#         mock_pandas.Series(["Instance"]),
#         mock_pandas.Series(["Normal"]),
#         mock_pandas.Series(["Boss"]),
#         mock_pandas.Series(["Moppi"]),
#     ]
#     mock_dataframe.rename.return_value = mock_dataframe
#     mock_dataframe.sort_values.return_value = mock_dataframe
#     mock_dataframe.to_dict.return_value = expected_result

#     # Call the function
#     result = modify_data(dataframe, player_list)

#     # Assert the result
#     assert result == expected_result
