
from app import validate_characters_known, validate_notes
from github_client import Player


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

