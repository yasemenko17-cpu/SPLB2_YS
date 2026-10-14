"""Лабораторна SP-LAB02. Задача 5: Кадри з префіксом довжини з потоку.

Правила — у student.md (розділ 7, задача 5) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_05.py
"""


def encode_frame(payload: bytes) -> bytes:
    """Додає до даних двобайтовий префікс довжини."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі


def read_frames(fd: int, max_len: int = 65536) -> list[bytes]:
    """Читає кадри з дескриптора до кінця потоку."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
