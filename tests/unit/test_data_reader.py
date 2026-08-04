"""Unit tests for automation/utils/data_reader.py"""

import pytest

from automation.utils.data_reader import read_json


def test_read_json_returns_dict():
    """read_json parses test_data/users.json and returns a dict."""
    result = read_json("test_data/users.json")
    assert isinstance(result, dict)


def test_read_json_has_expected_users():
    """users.json contains the standard_user and invalid_user entries."""
    users = read_json("test_data/users.json")
    assert "standard_user" in users
    assert "invalid_user" in users


def test_read_json_user_has_credentials():
    """Each user entry has username and password keys."""
    users = read_json("test_data/users.json")
    for user in users.values():
        assert "username" in user
        assert "password" in user


def test_read_json_missing_file_raises():
    """read_json raises FileNotFoundError for a non-existent path."""
    with pytest.raises(FileNotFoundError):
        read_json("test_data/does_not_exist.json")
