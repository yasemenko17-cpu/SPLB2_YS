"""Відкриті тести задачі 1: Кодек записів за схемою.

Запуск: pytest tests/test_lab_01.py
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


T01 = [
    ("S1", "size", ["u8", "u16", "u32"], None, 7),
    ("S1", "enc", ["u8", "u16", "u32"], (1, 258, 65536), "01 02 01 00 00 01 00"),
    ("S1", "dec", ["u16", "u16"], "ff 00 00 01", (255, 256)),
    ("S2", "enc", ["i8", "i16"], (-1, -2), "ff fe ff"),
    ("S2", "enc", ["f32"], (1.5,), "00 00 c0 3f"),
    ("S2", "dec", ["bool", "i32"], "01 ff ff ff ff", (True, -1)),
    ("S3", "enc", ["s4"], ("ab",), "61 62 00 00"),
    ("S3", "enc", ["u8", "s3"], (7, "é"), "07 c3 a9 00"),
    ("S3", "dec", ["s5", "u8"], "61 62 00 00 00 09", ("ab", 9)),
]


@pytest.mark.parametrize("tag,kind,schema,arg,expected", T01, ids=_ids(T01, "T01"))
def test_codec(tag, kind, schema, arg, expected):
    M = load(1)
    if kind == "size":
        assert M.record_size(schema) == expected
    elif kind == "enc":
        result = M.encode(schema, arg)
        assert isinstance(result, bytes)
        assert result == bytes.fromhex(expected)
    elif kind == "dec":
        result = M.decode(schema, bytes.fromhex(arg))
        assert isinstance(result, tuple)
        assert result == expected
    else:
        call = {"sizeerr": lambda: M.record_size(schema),
                "encerr": lambda: M.encode(schema, arg),
                "decerr": lambda: M.decode(schema, bytes.fromhex(arg))}[kind]
        with pytest.raises(ValueError) as info:
            call()
        assert str(info.value) == expected




def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(1).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
