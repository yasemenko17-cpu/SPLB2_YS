"""Лабораторна SP-LAB02. Задача 8: Двійковий пошук у відсортованому файлі.

Правила — у student.md (розділ 7, задача 8) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_08.py
"""


def lower_bound(path: str, key: int, probes: list | None = None) -> int:
    """Індекс першого запису з ключем не меншим за key."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def find_value(path: str, key: int, probes: list | None = None) -> int | None:
    """Значення першого запису з указаним ключем або None."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def count_range(path: str, lo: int, hi: int) -> int:
    """Кількість записів із ключем від lo до hi включно."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
