"""Лабораторна SP-LAB02. Задача 1: Кодек записів за схемою.

Правила — у student.md (розділ 7, задача 1) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_01.py
"""


def record_size(schema: list[str]) -> int:
    """Розмір запису в байтах за схемою."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def encode(schema: list[str], values: tuple | list) -> bytes:
    """Пакує значення за схемою в bytes."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def decode(schema: list[str], data: bytes) -> tuple:
    """Розпаковує bytes у кортеж значень за схемою."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
