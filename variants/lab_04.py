"""Лабораторна SP-LAB02. Задача 4: Журнал подій у власному бінарному файлі.

Правила — у student.md (розділ 7, задача 4) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_04.py
"""


def write_log(path: str, entries: list[tuple[int, str]]) -> int:
    """Записує журнал у файл формату SLG1; повертає розмір файла."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def read_log(path: str) -> list[tuple[int, str]]:
    """Читає журнал і перевіряє формат та контрольну суму."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
