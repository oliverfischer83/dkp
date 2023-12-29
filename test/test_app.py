"""
Tests for the utils
"""

import os
from unittest import mock
from unittest.mock import patch

import dkp
from dkp import app

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
