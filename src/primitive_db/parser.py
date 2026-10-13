"""Parsers for SQL-like commands with explicitly quoted string values."""

import ast
import re
import shlex

INTEGER_RE = re.compile(r"[+-]?\d+\Z")
PUNCTUATION = "(),="


def tokenize(command: str) -> list[str]:
    """Preserve quoted strings while splitting punctuation into separate tokens."""
    lexer = shlex.shlex(command, posix=False, punctuation_chars=PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        raw_tokens = list(lexer)
    except ValueError as exc:
        raise ValueError(
            "Некорректное значение: незакрытые кавычки. Попробуйте снова."
        ) from exc

    tokens = []
    for token in raw_tokens:
        if token and all(char in PUNCTUATION for char in token):
            tokens.extend(token)
        else:
            tokens.append(token)
    return tokens


def parse_value(token: str) -> str | int | bool:
    """Parse a quoted string, integer, or case-insensitive boolean."""
    if token.startswith(('"', "'")) and token.endswith(token[0]):
        try:
            result = ast.literal_eval(token)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(
                f"Некорректное значение: {token}. Попробуйте снова."
            ) from exc
        if type(result) is str:
            return result
    elif INTEGER_RE.fullmatch(token):
        return int(token)
    elif token.lower() in {"true", "false"}:
        return token.lower() == "true"
    raise ValueError(f"Некорректное значение: {token}. Попробуйте снова.")


def parse_values(tokens: list[str]) -> list[str | int | bool]:
    """Parse a comma-separated list of literals enclosed in parentheses."""
    if len(tokens) < 3 or tokens[0] != "(" or tokens[-1] != ")":
        raise ValueError("Некорректное значение: список values. Попробуйте снова.")
    contents = tokens[1:-1]
    if not contents:
        raise ValueError(
            "Некорректное значение: пустой список values. Попробуйте снова."
        )
    values = []
    expect_value = True
    for token in contents:
        if expect_value:
            if token in PUNCTUATION:
                raise ValueError(f"Некорректное значение: {token}. Попробуйте снова.")
            values.append(parse_value(token))
        elif token != ",":
            raise ValueError(f"Некорректное значение: {token}. Попробуйте снова.")
        expect_value = not expect_value
    if expect_value:
        raise ValueError("Некорректное значение: лишняя запятая. Попробуйте снова.")
    return values


def parse_assignment(tokens: list[str]) -> dict[str, str | int | bool]:
    """Parse a single condition such as 'age = 28'."""
    if len(tokens) != 3 or tokens[1] != "=" or not tokens[0].isidentifier():
        raise ValueError(
            f"Некорректное значение: {' '.join(tokens)}. Попробуйте снова."
        )
    return {tokens[0]: parse_value(tokens[2])}


def parse_set(tokens: list[str]) -> dict[str, str | int | bool]:
    """Parse one or more assignments separated by commas."""
    if not tokens:
        raise ValueError("Некорректное значение: пустое условие set. Попробуйте снова.")
    groups: list[list[str]] = [[]]
    for token in tokens:
        if token == ",":
            groups.append([])
        else:
            groups[-1].append(token)
    assignments = {}
    for group in groups:
        assignment = parse_assignment(group)
        key = next(iter(assignment))
        if key in assignments:
            raise ValueError(
                f"Некорректное значение: повтор столбца {key}. Попробуйте снова."
            )
        assignments.update(assignment)
    return assignments


def validate_clause(
    clause: dict, schema: dict[str, str], *, editable: bool = False
) -> None:
    """Check that columns exist and values have their declared types."""
    for name, value in clause.items():
        if name not in schema:
            raise ValueError(
                f"Некорректное значение: столбец {name}. Попробуйте снова."
            )
        if editable and name == "ID":
            raise ValueError(
                "Некорректное значение: ID нельзя изменять. Попробуйте снова."
            )
        if type(value).__name__ != schema[name]:
            raise ValueError(
                f"Некорректное значение: {value!r} для столбца "
                f"{name}:{schema[name]}. Попробуйте снова."
            )
