"""Лабораторна SP-LAB02. Задача 3: Цілі змінної довжини (varint) і zigzag.

Правила — у student.md (розділ 7, задача 3) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_03.py
"""


def encode_varint(n: int) -> bytes:
    """Кодує невід'ємне число в varint."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def decode_varint(data: bytes, pos: int = 0) -> tuple[int, int]:
    """Читає varint із позиції pos: (значення, нова позиція)."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def zigzag(n: int) -> int:
    """Відображає ціле зі знаком на ціле без знака."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def unzigzag(u: int) -> int:
    """Обернене відображення до zigzag."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def decode_all(data: bytes, signed: bool = False) -> list[int]:
    """Читає всі varint із даних."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
