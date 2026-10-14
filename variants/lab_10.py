"""Лабораторна SP-LAB02. Задача 10: Розмір і швидкість серіалізації.

Правила — у student.md (розділ 7, задача 10) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_10.py
"""


def benchmark(rows: list, repeat: int = 3) -> dict:
    """Розмір і час кодування та декодування трьома кодеками."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def size_ratio(report: dict) -> dict[str, float]:
    """Розмір кожного кодека відносно struct."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def fastest(report: dict, phase: str) -> str:
    """Назва найшвидшого кодека у вказаній фазі."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
