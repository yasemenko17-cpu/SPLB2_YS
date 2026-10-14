"""Відкриті тести задачі 2: Розкладка полів структури.

Запуск: pytest tests/test_lab_02.py
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


T02 = [
    ("S1", "layout", "bi", ([0, 4], 8)),
    ("S1", "layout", "bhi", ([0, 2, 4], 8)),
    ("S1", "layout", "", ([], 0)),
    ("S2", "waste", "bi", 3),
    ("S2", "waste", "ihb", 1),
    ("S2", "waste", "hhh", 0),
    ("S3", "best", "bdb", "dbb"),
    ("S3", "best", "bhbi", "ihbb"),
    ("S3", "best", "", ""),
]


@pytest.mark.parametrize("tag,kind,arg,expected", T02, ids=_ids(T02, "T02"))
def test_layout(tag, kind, arg, expected):
    M = load(2)
    if kind == "layout":
        offsets, total = M.native_layout(arg)
        assert (list(offsets), total) == (expected[0], expected[1])
    elif kind == "waste":
        assert M.wasted_bytes(arg) == expected
    elif kind == "best":
        assert M.best_order(arg) == expected
    else:
        for call in (M.native_layout, M.wasted_bytes, M.best_order):
            with pytest.raises(ValueError) as info:
                call(arg)
            assert str(info.value) == expected



LAYOUT_SAMPLES = ["bi", "bhi", "bd", "ihb", "bdb", "cBhH?", "fdfd", "bqbq", "ccccccci", "hhh", "BHB", "dbb", "?f"]
C_TYPES = {"c": "c_char", "b": "c_int8", "B": "c_uint8", "?": "c_bool", "h": "c_int16", "H": "c_uint16",
           "i": "c_int32", "I": "c_uint32", "f": "c_float", "l": "c_long", "L": "c_ulong",
           "q": "c_longlong", "Q": "c_ulonglong", "d": "c_double"}


def test_matches_c_compiler_layout():
    """Ваш розрахунок збігається з розкладкою структур C, яку будує ctypes (Linux, 64 біти)."""
    import ctypes
    if ctypes.sizeof(ctypes.c_long) != 8:
        pytest.skip("потрібен 64-бітний Linux")
    M = load(2)
    for codes in LAYOUT_SAMPLES:
        fields = [(f"f{i}", getattr(ctypes, C_TYPES[c])) for i, c in enumerate(codes)]
        cls = type("S", (ctypes.Structure,), {"_fields_": fields})
        offsets, total = M.native_layout(codes)
        assert total == ctypes.sizeof(cls), codes
        assert list(offsets) == [getattr(cls, name).offset for name, _ in fields], codes


def test_best_order_is_permutation_and_not_larger():
    M = load(2)
    for codes in LAYOUT_SAMPLES:
        result = M.best_order(codes)
        assert sorted(result) == sorted(codes), codes
        assert M.native_layout(result)[1] <= M.native_layout(codes)[1], codes


def test_no_calcsize():
    """Мета задачі: відтворити правила самому, а не викликати struct.calcsize чи ctypes."""
    source = Path(load(2).__file__).read_text(encoding="utf-8")
    assert "calcsize" not in source and "ctypes" not in source



def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(2).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
