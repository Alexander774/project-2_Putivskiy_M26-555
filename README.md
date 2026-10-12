# Primitive DB

Учебная база данных для управления схемами таблиц.

## Установка

```bash
uv sync
uv run database
```

Для сборки и установки команды `database` как самостоятельного инструмента:

```bash
uv build
uvx twine check dist/*
uv tool install --force dist/*.whl
```

После установки из wheel запустите `database` в терминале.

## Управление таблицами

Поддерживаемые типы: `int`, `str`, `bool`. Столбец `ID:int` автоматически добавляется к каждой таблице.

| Команда | Действие |
| --- | --- |
| `create_table <имя> <столбец:тип> ...` | Создать таблицу |
| `list_tables` | Показать таблицы |
| `drop_table <имя>` | Удалить таблицу |
| `help` | Показать справку |
| `exit` | Завершить программу |

Пример сеанса:

```text
>>>Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool
>>>Введите команду: list_tables
- users
>>>Введите команду: drop_table users
Таблица "users" успешно удалена.
>>>Введите команду: exit
```

Метаданные сохраняются в `db_meta.json` в текущей рабочей директории, из которой запускается команда.

## Демонстрация (аскинемы)

Базовые функции:
[![asciicast](https://asciinema.org/a/oRjElhNBjvnetPta.svg)](https://asciinema.org/a/oRjElhNBjvnetPta)
