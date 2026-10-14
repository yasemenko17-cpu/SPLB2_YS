"""Відкриті тести задачі 10: Розмір і швидкість серіалізації.

Запуск: pytest tests/test_lab_10.py
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


REPORT = {"struct": {"bytes": 100, "encode_s": 0.5, "decode_s": 0.2},
          "json": {"bytes": 250, "encode_s": 0.3, "decode_s": 0.4},
          "csv": {"bytes": 175, "encode_s": 0.9, "decode_s": 0.1}}
TIE = {"struct": {"encode_s": 1.0, "decode_s": 1.0}, "json": {"encode_s": 1.0, "decode_s": 2.0},
       "csv": {"encode_s": 3.0, "decode_s": 1.0}}
R3 = {"struct": {"bytes": 3}, "json": {"bytes": 10}}
EQUAL = {"struct": {"bytes": 8}, "json": {"bytes": 8}}

T10 = [
    ("S1", "sizes", [(1, 21.5, True), (2, 19.25, False)], None, (22, 31, 30)),
    ("S1", "sizes", [(0, 0.5, True)], None, (13, 14, 19)),
    ("S1", "sizes", [], None, (4, 2, 11)),
    ("S2", "sizes", [(i, 0.5, True) for i in range(1000)], None, (9004, 14891, 9901)),
    ("S2", "ratio", REPORT, None, {"struct": 1.0, "json": 2.5, "csv": 1.75}),
    ("S2", "ratio", R3, None, {"struct": 1.0, "json": 3.33}),
    ("S3", "fast", REPORT, "encode_s", "json"),
    ("S3", "fast", REPORT, "decode_s", "csv"),
    ("S3", "err", [(1, 0.1, True)], 3, "Кодек struct не відновлює дані"),
]


@pytest.mark.parametrize("tag,kind,arg,extra,expected", T10, ids=_ids(T10, "T10"))
def test_serialization(tag, kind, arg, extra, expected):
    M = load(10)
    if kind == "sizes":
        report = M.benchmark(arg, 1)
        assert set(report) == {"struct", "json", "csv"}
        assert (report["struct"]["bytes"], report["json"]["bytes"], report["csv"]["bytes"]) == expected
        for item in report.values():
            assert isinstance(item["bytes"], int)
            assert 0 < item["encode_s"] < 60 and 0 < item["decode_s"] < 60
    elif kind == "ratio":
        assert M.size_ratio(arg) == expected
    elif kind == "fast":
        assert M.fastest(arg, extra) == expected
    elif kind == "fasterr":
        with pytest.raises(ValueError) as info:
            M.fastest(arg, extra)
        assert str(info.value) == expected
    else:                                   # err: arg = рядки, extra = repeat
        with pytest.raises(ValueError) as info:
            M.benchmark(arg, extra)
        assert str(info.value) == expected



def test_default_repeat_and_structure():
    M = load(10)
    report = M.benchmark([(1, 1.5, True)] * 50)
    assert report["struct"]["bytes"] == 4 + 9 * 50
    assert report["struct"]["bytes"] < report["json"]["bytes"]


def test_rows_are_not_modified():
    M = load(10)
    rows = [[1, 0.5, True], [2, 0.25, False]]
    M.benchmark(rows, 1)
    assert rows == [[1, 0.5, True], [2, 0.25, False]]



def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct"}
    for node in ast.walk(ast.parse(Path(load(10).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
