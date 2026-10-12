"""Persistence for table metadata."""

import json
from pathlib import Path

from .core import Metadata


def load_metadata(filepath: str | Path) -> Metadata:
    """Read metadata; return {} if the file does not exist."""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str | Path, data: Metadata) -> None:
    """Save metadata as human-readable UTF-8 JSON."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.write("\n")
