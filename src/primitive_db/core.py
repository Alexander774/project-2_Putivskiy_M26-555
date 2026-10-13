"""Operations on table definitions and records."""

from .utils import load_table_data

Metadata = dict[str, list[str]]
ALLOWED_TYPES = {"int", "str", "bool"}


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


def drop_table(metadata: Metadata, table_name: str) -> Metadata:
    """Remove a table schema."""
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    del metadata[table_name]
    return metadata


def list_tables(metadata: Metadata) -> list[str]:
    """List table names alphabetically."""
    return sorted(metadata)


def table_schema(metadata: Metadata, table_name: str) -> dict[str, str]:
    """Return column names/types, rejecting missing tables."""
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    return dict(column.split(":", 1) for column in metadata[table_name])


def insert(metadata: Metadata, table_name: str, values: list) -> list[dict]:
    """Insert a record with the next available ID and return all table data."""
    schema = table_schema(metadata, table_name)
    columns = [(name, type_name) for name, type_name in schema.items() if name != "ID"]
    if len(values) != len(columns):
        raise ValueError(
            f"Некорректное значение: ожидалось {len(columns)} значений, "
            f"получено {len(values)}. Попробуйте снова."
        )

    for (name, type_name), value in zip(columns, values):
        if type(value).__name__ != type_name:
            raise ValueError(
                f"Некорректное значение: {value!r} для столбца {name}:{type_name}. "
                "Попробуйте снова."
            )

    table_data = load_table_data(table_name)
    next_id = max((row["ID"] for row in table_data), default=0) + 1
    record = {"ID": next_id}
    record.update((name, value) for (name, _), value in zip(columns, values))
    table_data.append(record)
    return table_data


def _matches(record: dict, clause: dict | None) -> bool:
    """Match a row by equality, distinguishing bool from int."""
    return clause is None or all(
        name in record and type(record[name]) is type(expected)
        and record[name] == expected
        for name, expected in clause.items()
    )


def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    """Return all records, or records matching the given condition."""
    return [row for row in table_data if _matches(row, where_clause)]


def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    """Change fields in every record matching the condition."""
    for row in table_data:
        if _matches(row, where_clause):
            row.update(set_clause)
    return table_data


def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    """Delete matching records, keeping the same outer list object."""
    table_data[:] = [row for row in table_data if not _matches(row, where_clause)]
    return table_data
