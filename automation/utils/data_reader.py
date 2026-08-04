import json
from pathlib import Path


def read_json(relative_path: str) -> dict:
    """
    Reads a JSON file from the project root.

    Args:
        relative_path: Relative path from project root.

    Returns:
        Dictionary containing JSON data.
    """

    project_root = Path(__file__).resolve().parent.parent.parent

    file_path = project_root / relative_path

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)
