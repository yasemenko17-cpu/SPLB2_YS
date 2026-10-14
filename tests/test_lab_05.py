"""Відкриті тести задачі 5: Кадри з префіксом довжини з потоку.

Запуск: pytest tests/test_lab_05.py
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


def feed(data, chunk):
    """Повертає читальний кінець каналу; окремий потік пише дані порціями по chunk байтів."""
    r, w = os.pipe()
    step = chunk or max(len(data), 1)

    def run():
        try:
            for i in range(0, len(data), step):
                os.write(w, data[i:i + step])
                if step < 8:
                    time.sleep(0.0005)
        except OSError:
            pass
        finally:
            os.close(w)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return r, thread


def read_with(M, raw, chunk, max_len):
    r, thread = feed(bytes.fromhex(raw), chunk)
    try:
        return M.read_frames(r) if max_len is None else M.read_frames(r, max_len)
    finally:
        os.close(r)
        thread.join(5)

T05 = [
    ("S1", "frames", "00 02 61 62 00 01 63", None, None, ["61 62", "63"]),
    ("S1", "frames", "", None, None, []),
    ("S1", "frames", "00 00 00 03 78 79 7a", None, None, ["", "78 79 7a"]),
    ("S2", "frames", "00 02 61 62 00 01 63", 1, None, ["61 62", "63"]),
    ("S2", "frames", "00 03 01 02 03", 2, None, ["01 02 03"]),
    ("S2", "frames", "00 01 41 00 01 42 00 01 43", 5, None, ["41", "42", "43"]),
    ("S3", "ferr", "00 05 61 62", None, None, "Обірваний кадр"),
    ("S3", "ferr", "00", None, None, "Обірваний кадр"),
    ("S3", "ferr", "00 0a 61 62", None, 4, "Кадр завеликий: 10"),
]


@pytest.mark.parametrize("tag,kind,raw,chunk,max_len,expected", T05, ids=_ids(T05, "T05"))
def test_frames(tag, kind, raw, chunk, max_len, expected):
    M = load(5)
    if kind == "frames":
        result = read_with(M, raw, chunk, max_len)
        assert result == [bytes.fromhex(x) for x in expected]
        assert all(isinstance(x, bytes) for x in result)
    elif kind == "ferr":
        with pytest.raises(ValueError) as info:
            read_with(M, raw, chunk, max_len)
        assert str(info.value) == expected
    elif kind == "enc":
        assert M.encode_frame(bytes.fromhex(raw)) == bytes.fromhex(expected)
    else:
        with pytest.raises(ValueError) as info:
            M.encode_frame(b"\0" * raw)
        assert str(info.value) == expected



def test_reader_does_not_close_descriptor():
    M = load(5)
    r, thread = feed(bytes.fromhex("00 01 41"), None)
    try:
        assert M.read_frames(r) == [b"A"]
        os.fstat(r)                      # дескриптор лишився відкритим
    finally:
        os.close(r)
        thread.join(5)



def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(5).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
