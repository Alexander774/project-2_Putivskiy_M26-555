"""Loop and command parsing."""

import json
import shlex
from pathlib import Path

import prompt

from .core import create_table, drop_table, list_tables
from .utils import load_metadata, save_metadata

METADATA_FILE = Path.cwd() / "db_meta.json"


def print_help() -> None:
    """Print information about the available database commands."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run() -> None:
    """Run the database command interpreter until the user exits."""
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
            parts = shlex.split(user_input or "")
        except ValueError:
            print("Некорректное значение: незакрытые кавычки. Попробуйте снова.")
            continue

        if not parts:
            continue
        command, *args = parts

        if command == "exit":
            if args:
                print(f"Некорректное значение: {' '.join(args)}. Попробуйте снова.")
            else:
                return

        elif command == "help":
            if args:
                print(f"Некорректное значение: {' '.join(args)}. Попробуйте снова.")
            else:
                print_help()

        elif command == "list_tables":
            if args:
                print(f"Некорректное значение: {' '.join(args)}. Попробуйте снова.")
                continue
            names = list_tables(metadata)
            if names:
                for name in names:
                    print(f"- {name}")
            else:
                print("Таблиц пока нет.")

        elif command == "create_table":
            if len(args) < 2:
                print("Некорректное значение: укажите таблицу и её столбцы. Попробуйте снова.")
                continue
            table_name, *columns = args
            try:
                create_table(metadata, table_name, columns)
                save_metadata(METADATA_FILE, metadata)
            except ValueError as exc:
                print(exc)
            except OSError as exc:
                print(f"Ошибка сохранения метаданных: {exc}")
            else:
                print(
                    f'Таблица "{table_name}" успешно создана со столбцами: '
                    f'{", ".join(metadata[table_name])}'
                )

        elif command == "drop_table":
            if len(args) != 1:
                print("Некорректное значение: укажите одно имя таблицы. Попробуйте снова.")
                continue
            table_name = args[0]
            try:
                drop_table(metadata, table_name)
                save_metadata(METADATA_FILE, metadata)
            except ValueError as exc:
                print(exc)
            except OSError as exc:
                print(f"Ошибка сохранения метаданных: {exc}")
            else:
                print(f'Таблица "{table_name}" успешно удалена.')

        else:
            print(f"Функции {command} нет. Попробуйте снова.")
