"""Відкриті тести задачі 3: Цілі змінної довжини (varint) і zigzag.

Запуск: pytest tests/test_lab_03.py
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


T03 = [
    ("S1", "enc", 0, "00"),
    ("S1", "enc", 300, "ac 02"),
    ("S1", "dec", ("ac 02 ff", 0), (300, 2)),
    ("S2", "zz", 0, 0),
    ("S2", "zz", -1, 1),
    ("S2", "zz", 1, 2),
    ("S2", "all", ("01 02", True), [-1, 1]),
    ("S3", "all", ("01 ac 02 7f", False), [1, 300, 127]),
    ("S3", "decerr", ("80", 0), "Обірваний varint"),
    ("S3", "all", ("", False), []),
]


@pytest.mark.parametrize("tag,kind,arg,expected", T03, ids=_ids(T03, "T03"))
def test_varint(tag, kind, arg, expected):
    M = load(3)
    if kind == "enc":
        assert M.encode_varint(arg) == bytes.fromhex(expected)
    elif kind == "dec":
        data, pos = arg
        assert M.decode_varint(bytes.fromhex(data), pos) == expected
    elif kind == "zz":
        assert M.zigzag(arg) == expected
    elif kind == "unzz":
        assert M.unzigzag(arg) == expected
    elif kind == "all":
        data, signed = arg
        assert M.decode_all(bytes.fromhex(data), signed) == expected
    else:
        call = {"encerr": lambda: M.encode_varint(arg),
                "decerr": lambda: M.decode_varint(bytes.fromhex(arg[0]), arg[1]),
                "zzerr": lambda: M.zigzag(arg),
                "allerr": lambda: M.decode_all(bytes.fromhex(arg[0]), arg[1])}[kind]
        with pytest.raises(ValueError) as info:
            call()
        assert str(info.value) == expected



def test_roundtrip_many():
    M = load(3)
    for n in [0, 1, 127, 128, 255, 256, 16383, 16384, 2**21, 2**32 - 1, 2**32, 2**63, 2**64 - 1]:
        blob = M.encode_varint(n)
        assert M.decode_varint(blob, 0) == (n, len(blob)), n
    for n in [-2**63, -2**31, -65, -64, -2, -1, 0, 1, 63, 64, 2**31, 2**63 - 1]:
        assert M.unzigzag(M.zigzag(n)) == n, n



def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(3).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
