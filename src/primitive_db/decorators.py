"""Reusable error handling, confirmation, timing, and closure-based caching."""

from functools import wraps
from time import monotonic
from typing import Callable, Hashable, TypeVar

R = TypeVar("R")


def handle_db_errors(func: Callable[..., R]) -> Callable[..., R | None]:
    """Report expected database errors and suppress a failed operation."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база не инициализирована.")
        except KeyError as exc:
            print(f"Ошибка: Таблица или столбец {exc} не найден.")
        except ValueError as exc:
            message = str(exc)
            if message.startswith(("Ошибка:", "Некорректное значение:")):
                print(message)
            else:
                print(f"Ошибка валидации: {message}")
        except Exception as exc:
            print(f"Произошла непредвиденная ошибка: {exc}")
        return None

    return wrapper


def confirm_action(action_name: str) -> Callable:
    """Require an explicit 'y' before calling a destructive operation."""

    def decorator(func: Callable[..., R]) -> Callable[..., R | None]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                print("\nОперация отменена.")
                return None
            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func: Callable[..., R]) -> Callable[..., R]:
    """Print execution time, including when the operation raises an error."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = monotonic() - start
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд")

    return wrapper


def create_cacher() -> Callable[[Hashable, Callable[[], R]], R]:
    """Create a cache whose private dictionary lives in a closure."""
    cache: dict[Hashable, object] = {}

    def cache_result(key: Hashable, value_func: Callable[[], R]) -> R:
        if key not in cache:
            cache[key] = value_func()
        return cache[key]  # type: ignore[return-value]

    return cache_result
