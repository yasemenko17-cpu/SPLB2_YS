"""Лабораторна SP-LAB02. Задача 2: Розкладка полів структури.

Правила — у student.md (розділ 7, задача 2) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_02.py
"""


def native_layout(codes: str) -> tuple[list[int], int]:
    """Зсуви полів і розмір структури за рідного вирівнювання."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def wasted_bytes(codes: str) -> int:
    """Кількість байтів вирівнювання."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def best_order(codes: str) -> str:
    """Порядок полів, що найекономніше використовує пам'ять."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
