# Primitive DB

Учебная база данных с управлением таблицами и CRUD-операциями.
Схемы хранятся в `db_meta.json`, записи каждой таблицы — в `data/<имя>.json`.

## Установка

```bash
uv add prettytable
uv sync
uv run database
```

Для сборки и установки команды `database` как самостоятельного инструмента:

```bash
rm -rf dist
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

Пример управления схемами:

```text
>>>Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool
>>>Введите команду: list_tables
- users
>>>Введите команду: drop_table users
Таблица "users" успешно удалена.
>>>Введите команду: exit
```

Метаданные сохраняются в `db_meta.json` в текущей рабочей директории, из которой запускается программа. При удалении таблицы удаляется и её файл `data/<имя>.json`.

## CRUD-операции

| Команда | Действие |
| --- | --- |
| `insert into users values ("Sergei", 28, true)` | Добавить запись (ID формируется автоматически) |
| `select from users` | Показать все записи |
| `select from users where age = 28` | Отобрать записи по условию |
| `update users set age = 29 where name = "Sergei"` | Изменить подходящие записи |
| `delete from users where ID = 1` | Удалить подходящие записи |
| `info users` | Показать схему и количество записей |

Ввод строк — только в кавычках (`"Sergei"`, `'Sergei'`). Числа (`28`, `-3`) и логические значения (`true`, `false`) — без кавычек. Все поля обязательны; `ID` передавать не нужно. Значения в `insert` перечисляются в порядке полей схемы без `ID`.

Пример:

```text
>>>Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool
>>>Введите команду: insert into users values ("Sergei", 28, true)
Запись с ID=1 успешно добавлена в таблицу "users".
>>>Введите команду: select from users where age = 28
+----+--------+-----+-----------+
| ID |  name  | age | is_active |
+----+--------+-----+-----------+
| 1  | Sergei | 28  |    True   |
+----+--------+-----+-----------+
>>>Введите команду: update users set age = 29 where name = "Sergei"
Запись с ID=1 в таблице "users" успешно обновлена.
>>>Введите команду: delete from users where ID = 1
Запись с ID=1 успешно удалена из таблицы "users".
>>>Введите команду: info users
Таблица: users
Столбцы: ID:int, name:str, age:int, is_active:bool
Количество записей: 0
```

## Тестирование

```bash
uv run python -m unittest discover -s tests -v
uv build
uvx twine check dist/*
```

После сборки установить новую версию можно командой `uv tool install --force dist/*.whl` (если в `dist/` только один wheel-файл), затем запустить `database`. Версия проекта — `0.2.0`.

Файлы данных из `data/` и `db_meta.json` не следует коммитить: они содержат состояние пользовательской базы данных.


## Демонстрация (аскинема)

Управление таблицами:

```markdown
[![asciicast](https://asciinema.org/a/oRjElhNBjvnetPta.svg)](https://asciinema.org/a/oRjElhNBjvnetPta)
```