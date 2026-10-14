"""Відкриті тести задачі 9: Часткові суми в дочірніх процесах через спільний mmap.

Запуск: pytest tests/test_lab_09.py
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


import ast

T09 = [
    ("S1", "sums", list(range(1, 9)), 2, [10, 26]),
    ("S1", "sums", [5], 1, [5]),
    ("S1", "total", list(range(1, 101)), 4, 5050),
    ("S2", "sums", [1, 2, 3, 4, 5], 4, [3, 7, 5, 0]),
    ("S2", "sums", [7, 8], 3, [7, 8, 0]),
    ("S2", "sums", [], 3, [0, 0, 0]),
    ("S3", "sums", [-5, 5, -10, 10], 2, [0, 0]),
    ("S3", "sums", [-1, -2, -3], 3, [-1, -2, -3]),
    ("S3", "err", [1], 0, "Кількість процесів має бути додатною"),
]


def _no_children_left():
    try:
        os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        return True
    return False


@pytest.mark.parametrize("tag,kind,numbers,workers,expected", T09, ids=_ids(T09, "T09"))
def test_partial_sums(tag, kind, numbers, workers, expected, monkeypatch):
    forks = []
    real_fork = os.fork

    def counting_fork():
        forks.append(1)
        return real_fork()

    monkeypatch.setattr(os, "fork", counting_fork)
    real_mmap = mmap.mmap
    maps = []

    def spy(*args, **kwargs):
        maps.append(args)
        return real_mmap(*args, **kwargs)

    monkeypatch.setattr(mmap, "mmap", spy)
    M = load(9)
    original = list(numbers)
    if kind == "sums":
        assert M.partial_sums(numbers, workers) == expected
        assert len(forks) == workers, "потрібен рівно один fork на кожного робітника"
        assert maps and maps[0][0] == -1, "потрібне анонімне відображення mmap.mmap(-1, ...)"
    elif kind == "total":
        assert M.parallel_sum(numbers, workers) == expected
    elif kind == "err":
        with pytest.raises(ValueError) as info:
            M.partial_sums(numbers, workers)
        assert str(info.value) == expected
        assert not forks
    else:                                   # failure
        with pytest.raises(RuntimeError) as info:
            M.partial_sums(numbers, workers)
        assert str(info.value) == expected
    assert numbers == original
    assert _no_children_left(), "після виклику не повинно лишатися дочірніх процесів (зомбі)"


def test_no_shortcuts():
    """Заборонено multiprocessing, subprocess, threading, concurrent: у задачі потрібні fork і mmap."""
    source = Path(load(9).__file__).read_text(encoding="utf-8")
    banned = {"multiprocessing", "subprocess", "threading", "concurrent", "pty"}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"




def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(9).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
