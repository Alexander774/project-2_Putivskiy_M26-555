"""Operations on database table schemas."""

Metadata = dict[str, list[str]]
ALLOWED_TYPES = {"int", "str", "bool"}


def create_table(metadata: Metadata, table_name: str, columns: list[str]) -> Metadata:
    """Add a table definition to metadata, including a primary-key ID field."""
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное значение: {table_name}. Попробуйте снова.")
    if not columns:
        raise ValueError("Некорректное значение: отсутствуют столбцы. Попробуйте снова.")

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
            raise ValueError(f"Некорректное значение: {column} (повтор столбца). Попробуйте снова.")
        seen.add(name)
        schema.append(column)

    metadata[table_name] = schema
    return metadata


def drop_table(metadata: Metadata, table_name: str) -> Metadata:
    """Remove a table from metadata."""
    if table_name not in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" не существует.')
    del metadata[table_name]
    return metadata


def list_tables(metadata: Metadata) -> list[str]:
    """Return table names in a stable, alphabetical order."""
    return sorted(metadata)
