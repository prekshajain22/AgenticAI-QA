import pytest

from automation.utils.data_reader import read_json


@pytest.fixture(scope="session")
def users():

    return read_json("test_data/users.json")
