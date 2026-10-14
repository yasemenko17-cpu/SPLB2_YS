"""Відкриті тести задачі 6: Пошук усіх входжень у файлі через mmap.

Запуск: pytest tests/test_lab_06.py
Тут лише приклади з карток варіантів; повний набір перевірок є у викладача.
"""
import mmap
import os
import signal
import struct
import sys
import threading
import time
import tracemalloc
import zlib
from pathlib import Path

import pytest
from conftest import load


def _ids(cases, prefix):
    return [f"{prefix}-{c[0]}-{i}" for i, c in enumerate(cases)]


@pytest.fixture(autouse=True)
def _watchdog():
    """Тест, що завис (наприклад, через нескінченний цикл читання), завершується за 20 с."""
    def boom(signum, frame):
        raise TimeoutError("тест завис довше 20 с: перевірте умови виходу з циклів")
    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(20)
    yield
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old)



@pytest.fixture
def mmap_calls(monkeypatch):
    """Лічильник викликів mmap.mmap: задача вимагає саме відображення файла."""
    real = mmap.mmap
    calls = []

    def spy(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(mmap, "mmap", spy)
    return calls

PAGE = mmap.PAGESIZE


class Blob(bytes):
    """Нульовий файл заданого розміру з вписаними мітками (для опису в картках)."""


def blob(size, *marks):
    data = bytearray(size)
    for offset, text in marks:
        data[offset:offset + len(text)] = text
    result = Blob(data)
    result.marks = marks
    result.size = size
    return result

T06 = [
    ("S1", "find", b"abracadabra", b"abra", [0, 7]),
    ("S1", "find", b"aaaa", b"aa", [0, 1, 2]),
    ("S1", "find", b"hello", b"xyz", []),
    ("S2", "find", blob(2 * PAGE, (PAGE - 2, b"MARK")), b"MARK", [PAGE - 2]),
    ("S2", "find", blob(3 * PAGE, (0, b"AB"), (PAGE - 1, b"AB"), (2 * PAGE, b"AB")), b"AB", [0, PAGE - 1, 2 * PAGE]),
    ("S2", "find", blob(PAGE, (PAGE - 3, b"end")), b"end", [PAGE - 3]),
    ("S3", "find", b"", b"a", []),
    ("S3", "err", b"abc", b"", "Порожній зразок"),
    ("S3", "find", b"ab", b"abc", []),
]


@pytest.mark.parametrize("tag,kind,content,pattern,expected", T06, ids=_ids(T06, "T06"))
def test_find_all(tag, kind, content, pattern, expected, tmp_path, mmap_calls):
    path = tmp_path / "data.bin"
    path.write_bytes(content)
    M = load(6)
    if kind == "find":
        assert M.find_all(str(path), pattern) == expected
        if expected:
            assert mmap_calls, "потрібно відобразити файл викликом mmap.mmap"
    elif kind == "err":
        with pytest.raises(ValueError) as info:
            M.find_all(str(path), pattern)
        assert str(info.value) == expected
    else:
        with pytest.raises(FileNotFoundError):
            M.find_all(str(tmp_path / "немає.bin"), pattern)



def test_large_sparse_file_does_not_load_into_memory(tmp_path, mmap_calls):
    """Файл на 16 МіБ шукається без читання його вмісту в пам'ять Python."""
    size = 16 * 1024 * 1024
    path = tmp_path / "big.bin"
    with open(path, "wb") as handle:
        handle.truncate(size)
        for offset in (0, size // 2 + 3, size - 4):
            handle.seek(offset)
            handle.write(b"MARK")
    M = load(6)
    tracemalloc.start()
    try:
        found = M.find_all(str(path), b"MARK")
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert found == [0, size // 2 + 3, size - 4]
    assert peak < 2 * 1024 * 1024, f"пік пам'яті Python {peak} байтів: файл читається цілком"
    assert mmap_calls



def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(6).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
