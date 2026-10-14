"""Відкриті тести задачі 4: Журнал подій у власному бінарному файлі.

Запуск: pytest tests/test_lab_04.py
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


def seal(body):
    """Додає до тіла файла контрольну суму CRC32 (як у форматі SLG1)."""
    return body + struct.pack("<I", zlib.crc32(body))


def build(entries):
    """Незалежна збірка еталонного файла SLG1 з пар (мітка, повідомлення)."""
    body = struct.pack("<4sI", b"SLG1", len(entries))
    for stamp, message in entries:
        raw = message.encode("utf-8")
        body += struct.pack("<QI", stamp, len(raw)) + raw
    return seal(body)


def flip(blob, index):
    """Копія з інвертованим молодшим бітом одного байта."""
    data = bytearray(blob)
    data[index] ^= 1
    return bytes(data)


def head(n):
    return b"SLG1" + struct.pack("<I", n)

T04 = [
    ("S1", "write", [], 12, "53 4c 47 31 00 00 00 00"),
    ("S1", "write", [(1, "hi")], 26, "53 4c 47 31 01 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00"),
    ("S1", "write", [(10, "a"), (20, "bc")], 39, "53 4c 47 31 02 00 00 00 0a 00 00 00 00 00 00 00 01 00 00 00"),
    ("S2", "write", [(5, "привіт")], 36, "53 4c 47 31 01 00 00 00 05 00 00 00 00 00 00 00 0c 00 00 00"),
    ("S2", "write", [(1, "é"), (2, "日本")], 44, "53 4c 47 31 02 00 00 00 01 00 00 00 00 00 00 00 02 00 00 00"),
    ("S3", "bad", build([(1, "a")])[:-1], "Контрольна сума не збігається", ""),
    ("S3", "bad", b"", "Файл закороткий", ""),
    ("S3", "bad", b"XXXX" + build([])[4:], "Невідома магія", ""),
]


@pytest.mark.parametrize("tag,kind,arg,expected,head_hex", T04, ids=_ids(T04, "T04"))
def test_log(tag, kind, arg, expected, head_hex, tmp_path):
    M = load(4)
    path = str(tmp_path / "events.slg")
    if kind == "write":
        size = M.write_log(path, arg)
        blob = Path(path).read_bytes()
        assert size == len(blob) == expected
        assert blob == build(arg)
        assert blob[:len(bytes.fromhex(head_hex))] == bytes.fromhex(head_hex)
        assert M.read_log(path) == arg
    elif kind == "roundtrip":
        size = M.write_log(path, arg)
        assert size == len(build(arg)) == Path(path).stat().st_size
        assert M.read_log(path) == arg
    elif kind == "twice":
        M.write_log(path, arg[0])
        M.write_log(path, arg[1])
        assert Path(path).read_bytes() == build(arg[1])
        assert M.read_log(path) == arg[1]
    elif kind == "bad":
        Path(path).write_bytes(arg)
        with pytest.raises(ValueError) as info:
            M.read_log(path)
        assert str(info.value) == expected
    elif kind == "writeerr":
        with pytest.raises(ValueError) as info:
            M.write_log(path, arg)
        assert str(info.value) == expected
    else:
        with pytest.raises(FileNotFoundError):
            M.read_log(path)




def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(4).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
