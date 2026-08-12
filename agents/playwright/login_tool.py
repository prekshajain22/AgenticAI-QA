"""
login_tool.py — AutoGen login FunctionTool for Playwright MCP agent.
This tool uses test_data/users.json and data_reader.read_json to provide credentials.
"""

from autogen_core.tools import FunctionTool

from automation.utils.data_reader import read_json

_USERS = read_json("test_data/users.json")


def login(user_key: str) -> dict:
    """
    Returns credentials for the requested user_key from users.json.

    Parameters
    ----------
    user_key : str
        User key present in test_data/users.json.

    Returns
    -------
    dict with fields: username, password
    """
    if user_key not in _USERS:
        raise ValueError(
            f"user_key '{user_key}' not found in users.json. "
            f"Available: {list(_USERS.keys())}"
        )
    return dict(_USERS[user_key])


login_tool = FunctionTool(
    login,
    name="login",
    description=(
        "Fetch credentials for the given user_key. Use this before any authenticated step. "
        "Credentials are returned as a dict with fields: username, password."
    ),
)
