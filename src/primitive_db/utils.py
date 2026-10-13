"""Read and write table schemas and records as JSON files."""

import json
from pathlib import Path

DATA_DIR = Path("data")


def load_metadata(filepath: str | Path) -> dict[str, list[str]]:
    """Load schemas, returning an empty dictionary if no file exists."""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str | Path, data: dict[str, list[str]]) -> None:
    """Save schemas in human-readable JSON."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.write("\n")


def _table_path(table_name: str) -> Path:
    """Build a safe table filename using a validated table identifier."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное значение: {table_name}. Попробуйте снова.")
    return DATA_DIR / f"{table_name}.json"


def load_table_data(table_name: str) -> list[dict]:
    """Read table records; return [] when their file does not exist."""
    try:
        with open(_table_path(table_name), encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name: str, data: list[dict]) -> None:
    """Write table records, creating the data directory if necessary."""
    filepath = _table_path(table_name)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.write("\n")


def delete_table_data(table_name: str) -> None:
    """Remove records when a table is dropped; missing files are fine."""
    _table_path(table_name).unlink(missing_ok=True)
