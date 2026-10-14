"""Відкриті тести задачі 8: Двійковий пошук у відсортованому файлі.

Запуск: pytest tests/test_lab_08.py
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

REC = struct.Struct("<II")
BIG = [(3 * i, i * 7 % 1000) for i in range(100000)]
SMALL = [(2, 20), (4, 40), (6, 60), (8, 80), (10, 100)]
DUPS = [(1, 10), (3, 30), (3, 31), (3, 32), (7, 70)]


def make(path, pairs):
    Path(path).write_bytes(b"".join(REC.pack(k, v) for k, v in pairs))

T08 = [
    ("S1", "find", SMALL, 6, 60),
    ("S1", "find", SMALL, 5, None),
    ("S1", "lb", SMALL, 5, 2),
    ("S2", "find", BIG, 0, 0),
    ("S2", "find", BIG, 299997, 99999 * 7 % 1000),
    ("S2", "find", BIG, 300, 100 * 7 % 1000),
    ("S2", "find", BIG, 301, None),
    ("S3", "find", DUPS, 3, 30),
    ("S3", "lb", DUPS, 3, 1),
    ("S3", "range", DUPS, (3, 3), 3),
]


@pytest.mark.parametrize("tag,kind,pairs,arg,expected", T08, ids=_ids(T08, "T08"))
def test_search(tag, kind, pairs, arg, expected, tmp_path, mmap_calls):
    path = str(tmp_path / "sorted.bin")
    M = load(8)
    if kind == "bad":
        Path(path).write_bytes(pairs)
        for call in (lambda: M.lower_bound(path, 1), lambda: M.find_value(path, 1), lambda: M.count_range(path, 0, 9)):
            with pytest.raises(ValueError) as info:
                call()
            assert str(info.value) == expected
        return
    make(path, pairs)
    limit = len(pairs).bit_length() + 1
    probes = []
    if kind == "find":
        assert M.find_value(path, arg, probes) == expected
    elif kind == "lb":
        assert M.lower_bound(path, arg, probes) == expected
    else:
        assert M.count_range(path, *arg) == expected
        probes = None
    if probes is not None:
        assert len(probes) <= limit, f"перевірено {len(probes)} записів, а потрібно не більше {limit}"
    if pairs and kind != "range":
        assert mmap_calls, "потрібно відобразити файл викликом mmap.mmap"



def test_probes_is_optional(tmp_path):
    path = str(tmp_path / "sorted.bin")
    make(path, SMALL)
    M = load(8)
    assert M.lower_bound(path, 6) == 2
    assert M.find_value(path, 8) == 80


def test_big_file_needs_few_probes(tmp_path):
    path = str(tmp_path / "sorted.bin")
    make(path, BIG)
    M = load(8)
    probes = []
    assert M.lower_bound(path, 150000, probes) == 50000
    assert 1 <= len(probes) <= 18



def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(8).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
