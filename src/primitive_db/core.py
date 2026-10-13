"""Operations on table definitions and records."""

import json
from copy import deepcopy

from .decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from .utils import load_table_data

Metadata = dict[str, list[str]]
ALLOWED_TYPES = {"int", "str", "bool"}
_select_cache = create_cacher()


@handle_db_errors
def create_table(metadata: Metadata, table_name: str, columns: list[str]) -> Metadata:
    """Create a table schema with an automatically managed integer ID."""
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное значение: {table_name}. Попробуйте снова.")
    if not columns:
        raise ValueError(
            "Некорректное значение: отсутствуют столбцы. Попробуйте снова."
        )

    schema = ["ID:int"]
    seen = {"ID"}
    explicit_id = False

    for column in columns:
        if column.count(":") != 1:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        name, type_name = column.split(":")
        if not name.isidentifier() or type_name not in ALLOWED_TYPES:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        if name == "ID":
            if type_name != "int" or explicit_id:
                raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
            explicit_id = True
            continue
        if name in seen:
            raise ValueError(
                f"Некорректное значение: {column} (повтор столбца). Попробуйте снова."
            )
        seen.add(name)
        schema.append(column)

    metadata[table_name] = schema
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata: Metadata, table_name: str) -> Metadata:
    """Remove a table schema only after user confirmation."""
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    del metadata[table_name]
    return metadata


def list_tables(metadata: Metadata) -> list[str]:
    """List table names alphabetically."""
    return sorted(metadata)


def _table_schema(metadata: Metadata, table_name: str) -> dict[str, str]:
    """Schema validation for internal use, preserving exceptions."""
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    return dict(column.split(":", 1) for column in metadata[table_name])


@handle_db_errors
def table_schema(metadata: Metadata, table_name: str) -> dict[str, str]:
    """Return column names and types for an existing table."""
    return _table_schema(metadata, table_name)


@handle_db_errors
@log_time
def insert(metadata: Metadata, table_name: str, values: list) -> list[dict]:
    """Insert a type-checked record with an automatically generated ID."""
    schema = _table_schema(metadata, table_name)
    columns = [(name, kind) for name, kind in schema.items() if name != "ID"]
    if len(values) != len(columns):
        raise ValueError(
            f"Некорректное значение: ожидалось {len(columns)} значений, "
            f"получено {len(values)}. Попробуйте снова."
        )

    for (name, kind), value in zip(columns, values):
        if type(value).__name__ != kind:
            raise ValueError(
                f"Некорректное значение: {value!r} для столбца {name}:{kind}. "
                "Попробуйте снова."
            )

    table_data = load_table_data(table_name)
    next_id = max((row["ID"] for row in table_data), default=0) + 1
    record = {"ID": next_id}
    record.update((name, value) for (name, _), value in zip(columns, values))
    table_data.append(record)
    return table_data


def _matches(record: dict, clause: dict | None) -> bool:
    """Match by typed equality (True must not compare equal to integer 1)."""
    return clause is None or all(
        name in record
        and type(record[name]) is type(expected)
        and record[name] == expected
        for name, expected in clause.items()
    )


@handle_db_errors
@log_time
def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    """Select with a content-sensitive cache that never returns stale rows.

    Since each command reloads table data from disk, an object-identity cache
    would miss repeats or return stale results. The data snapshot is part of
    the key; deep copies prevent callers from mutating cached records.
    """
    data_key = json.dumps(table_data, sort_keys=True, ensure_ascii=False)
    where_key = json.dumps(where_clause, sort_keys=True, ensure_ascii=False)
    key = (data_key, where_key)
    rows = _select_cache(
        key,
        lambda: [deepcopy(row) for row in table_data if _matches(row, where_clause)],
    )
    return deepcopy(rows)


@handle_db_errors
def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    """Change the fields of all matching records."""
    for row in table_data:
        if _matches(row, where_clause):
            row.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    """Delete matching records in-place only after user confirmation."""
    table_data[:] = [row for row in table_data if not _matches(row, where_clause)]
    return table_data
