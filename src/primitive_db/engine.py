"""Interactive commands for table management and CRUD operations."""

import json
from pathlib import Path

import prompt
from prettytable import PrettyTable

from .core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    table_schema,
    update,
)
from .parser import (
    parse_assignment,
    parse_set,
    parse_values,
    tokenize,
    validate_clause,
)
from .utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

METADATA_FILE = Path("db_meta.json")


def print_help() -> None:
    """Print help for table management and CRUD commands."""
    print("\n***База данных***")
    print("\nУправление таблицами:")
    print("<command> create_table <имя> <столбец:тип> ... - создать таблицу")
    print("<command> list_tables - показать список таблиц")
    print("<command> drop_table <имя> - удалить таблицу")
    print("\nОперации с данными:")
    print('<command> insert into <имя> values ("строка", 28, true) - добавить запись')
    print(
        "<command> select from <имя> [where <столбец> = <значение>] - прочитать записи"
    )
    print(
        "<command> update <имя> set <столбец> = <значение> where <столбец> = <значение>"
    )
    print("<command> delete from <имя> where <столбец> = <значение> - удалить записи")
    print("<command> info <имя> - информация о таблице")
    print("\nОбщие команды:")
    print("<command> help - справочная информация")
    print("<command> exit - выход из программы\n")


def _invalid(message: str) -> ValueError:
    return ValueError(f"Некорректное значение: {message}. Попробуйте снова.")


def _display_rows(metadata: dict, table_name: str, rows: list[dict]) -> None:
    """Print rows using the original schema's column order."""
    schema = table_schema(metadata, table_name)
    if schema is None:
        return
    column_names = list(schema)
    output = PrettyTable()
    output.field_names = column_names
    for row in rows:
        output.add_row([row[name] for name in column_names])
    print(output)


def _print_mutation_result(action: str, table_name: str, affected: list[dict]) -> None:
    """Report the affected record IDs when possible."""
    if not affected:
        print("Записей, соответствующих условию, не найдено.")
    elif len(affected) == 1:
        if action == "update":
            print(
                f'Запись с ID={affected[0]["ID"]} в таблице "{table_name}" '
                "успешно обновлена."
            )
        else:
            print(
                f"Запись с ID={affected[0]['ID']} успешно удалена "
                f'из таблицы "{table_name}".'
            )
    else:
        verb = "Обновлено" if action == "update" else "Удалено"
        print(f"{verb} записей: {len(affected)}.")


def run() -> None:
    """Run commands until exit or Ctrl+D."""
    print_help()
    while True:
        try:
            metadata = load_metadata(METADATA_FILE)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Ошибка чтения метаданных: {exc}")
            return

        try:
            user_input = prompt.string(prompt=">>>Введите команду: ")
        except (KeyboardInterrupt, EOFError):
            print("\nВыход из программы.")
            return

        try:
            tokens = tokenize(user_input or "")
            if not tokens:
                continue
            command, *args = tokens
            command = command.lower()

            if command == "exit":
                if args:
                    raise _invalid("лишние аргументы для exit")
                return

            if command == "help":
                if args:
                    raise _invalid("лишние аргументы для help")
                print_help()

            elif command == "list_tables":
                if args:
                    raise _invalid("лишние аргументы для list_tables")
                names = list_tables(metadata)
                if names:
                    print("\n".join(f"- {name}" for name in names))
                else:
                    print("Таблиц пока нет.")

            elif command == "create_table":
                if len(args) < 2:
                    raise _invalid("укажите таблицу и её столбцы")
                table_name, *columns = args
                if create_table(metadata, table_name, columns) is None:
                    continue
                save_table_data(table_name, [])
                save_metadata(METADATA_FILE, metadata)
                print(
                    f'Таблица "{table_name}" успешно создана со столбцами: '
                    f"{', '.join(metadata[table_name])}"
                )

            elif command == "drop_table":
                if len(args) != 1:
                    raise _invalid("укажите одно имя таблицы")
                table_name = args[0]
                if drop_table(metadata, table_name) is None:
                    continue
                save_metadata(METADATA_FILE, metadata)
                delete_table_data(table_name)
                print(f'Таблица "{table_name}" успешно удалена.')

            elif command == "insert":
                if (
                    len(args) < 5
                    or args[0].lower() != "into"
                    or args[2].lower() != "values"
                ):
                    raise _invalid("синтаксис: insert into <таблица> values (...)")
                table_name = args[1]
                values = parse_values(args[3:])
                data = insert(metadata, table_name, values)
                if data is None:
                    continue
                save_table_data(table_name, data)
                print(
                    f"Запись с ID={data[-1]['ID']} успешно добавлена "
                    f'в таблицу "{table_name}".'
                )

            elif command == "select":
                if len(args) < 2 or args[0].lower() != "from":
                    raise _invalid("синтаксис: select from <таблица> [where ...]")
                table_name = args[1]
                schema = table_schema(metadata, table_name)
                if schema is None:
                    continue
                if len(args) == 2:
                    where_clause = None
                elif len(args) >= 3 and args[2].lower() == "where":
                    where_clause = parse_assignment(args[3:])
                    validate_clause(where_clause, schema)
                else:
                    raise _invalid("синтаксис: select ... where <столбец> = <значение>")
                data = load_table_data(table_name)
                rows = select(data, where_clause)
                if rows is None:
                    continue
                _display_rows(metadata, table_name, rows)

            elif command == "update":
                if len(args) < 8 or args[1].lower() != "set":
                    raise _invalid("синтаксис: update <таблица> set ... where ...")
                table_name = args[0]
                schema = table_schema(metadata, table_name)
                if schema is None:
                    continue
                try:
                    where_index = next(
                        i for i in range(2, len(args)) if args[i].lower() == "where"
                    )
                except StopIteration as exc:
                    raise _invalid("для update обязательно условие where") from exc
                set_clause = parse_set(args[2:where_index])
                where_clause = parse_assignment(args[where_index + 1 :])
                validate_clause(set_clause, schema, editable=True)
                validate_clause(where_clause, schema)
                data = load_table_data(table_name)
                affected = select(data, where_clause)
                if affected is None:
                    continue
                if affected:
                    changed = update(data, set_clause, where_clause)
                    if changed is None:
                        continue
                    save_table_data(table_name, changed)
                _print_mutation_result("update", table_name, affected)

            elif command == "delete":
                if (
                    len(args) < 6
                    or args[0].lower() != "from"
                    or args[2].lower() != "where"
                ):
                    raise _invalid("синтаксис: delete from <таблица> where ...")
                table_name = args[1]
                schema = table_schema(metadata, table_name)
                if schema is None:
                    continue
                where_clause = parse_assignment(args[3:])
                validate_clause(where_clause, schema)
                data = load_table_data(table_name)
                affected = select(data, where_clause)
                if affected is None:
                    continue
                if affected:
                    changed = delete(data, where_clause)
                    if changed is None:
                        continue
                    save_table_data(table_name, changed)
                _print_mutation_result("delete", table_name, affected)

            elif command == "info":
                if len(args) != 1:
                    raise _invalid("укажите одно имя таблицы")
                table_name = args[0]
                if table_schema(metadata, table_name) is None:
                    continue
                data = load_table_data(table_name)
                print(f"Таблица: {table_name}")
                print(f"Столбцы: {', '.join(metadata[table_name])}")
                print(f"Количество записей: {len(data)}")

            else:
                print(f"Функции {command} нет. Попробуйте снова.")

        except ValueError as exc:
            print(exc)
        except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
            print(f"Ошибка работы с данными: {exc}")
