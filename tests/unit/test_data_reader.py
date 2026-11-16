"""Unit tests for automation/utils/data_reader.py"""

import pytest

from automation.utils.data_reader import read_json


def test_read_json_users_have_expected_entries_and_credentials():
    """users.json parses to a dict with standard_user/invalid_user, each with credentials."""
    users = read_json("test_data/users.json")
    assert isinstance(users, dict)
    assert "standard_user" in users
    assert "invalid_user" in users
    for user in users.values():
        assert "username" in user
        assert "password" in user


def test_read_json_missing_file_raises():
    """read_json raises FileNotFoundError for a non-existent path."""
    with pytest.raises(FileNotFoundError):
        read_json("test_data/does_not_exist.json")
