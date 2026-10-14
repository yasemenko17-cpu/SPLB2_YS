"""Лабораторна SP-LAB02. Задача 9: Часткові суми в дочірніх процесах через спільний mmap.

Правила — у student.md (розділ 7, задача 9) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_09.py
"""


def partial_sums(numbers: list[int], workers: int) -> list[int]:
    """Суми частин списку, пораховані в дочірніх процесах."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def parallel_sum(numbers: list[int], workers: int) -> int:
    """Сума всіх чисел."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
