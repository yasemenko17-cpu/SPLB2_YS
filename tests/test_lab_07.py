"""Відкриті тести задачі 7: Зміна записів на місці через mmap.

Запуск: pytest tests/test_lab_07.py
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

HEAD = struct.Struct("<4sI")
REC = struct.Struct("<I8sH")


def make(path, records, magic=b"STK1"):
    data = HEAD.pack(magic, len(records)) + b"".join(REC.pack(i, n.encode(), q) for i, n, q in records)
    Path(path).write_bytes(data)
    return data

T07 = [
    ("S1", "restock", [(1, "bolt", 5), (2, "nut", 20), (3, "gear", 0)], (10, 5), (2, [10, 20, 5])),
    ("S1", "restock", [(1, "a", 3)], (4, 1), (1, [4])),
    ("S1", "total", [(1, "a", 3), (2, "b", 4)], None, 7),
    ("S2", "restock", [(1, "a", 65530)], (65535, 10), (1, [65535])),
    ("S2", "restock", [(1, "a", 65535)], (65535, 1), (0, [65535])),
    ("S2", "restock", [(1, "a", 65000), (2, "b", 100)], (65535, 600), (2, [65535, 700])),
    ("S3", "bad", b"", None, "Файл закороткий"),
    ("S3", "bad", b"STK1", None, "Файл закороткий"),
    ("S3", "bad", b"XXXX" + struct.pack("<I", 0), None, "Невідома магія"),
    ("S3", "bad", HEAD.pack(b"STK1", 2) + REC.pack(1, b"a", 1), None, "Розмір файлу не відповідає заголовку"),
]


@pytest.mark.parametrize("tag,kind,records,args,expected", T07, ids=_ids(T07, "T07"))
def test_stock(tag, kind, records, args, expected, tmp_path, mmap_calls):
    path = str(tmp_path / "stock.bin")
    M = load(7)
    if kind == "restock":
        before = make(path, records)
        changed = M.restock(path, *args)
        assert changed == expected[0]
        after = Path(path).read_bytes()
        assert len(after) == len(before)
        # решта байтів не змінилась: перебудовуємо очікуваний файл із новими кількостями
        wanted = make(tmp_path / "wanted.bin", [(i, n, q) for (i, n, _), q in zip(records, expected[1])])
        assert after == wanted
        assert mmap_calls, "потрібно відобразити файл викликом mmap.mmap"
    elif kind == "total":
        before = make(path, records)
        assert M.total_quantity(path) == expected
        assert Path(path).read_bytes() == before
    else:                                   # bad: обидві функції відмовляються з однаковим текстом
        Path(path).write_bytes(records)
        for call in (lambda: M.restock(path, 10, 1), lambda: M.total_quantity(path)):
            with pytest.raises(ValueError) as info:
                call()
            assert str(info.value) == expected
        assert Path(path).read_bytes() == records



def test_missing_file(tmp_path):
    M = load(7)
    with pytest.raises(FileNotFoundError):
        M.restock(str(tmp_path / "немає.bin"), 1, 1)
    with pytest.raises(FileNotFoundError):
        M.total_quantity(str(tmp_path / "немає.bin"))


def test_total_quantity_works_on_read_only_file(tmp_path, mmap_calls):
    """Читання не повинно потребувати права запису (режим ACCESS_READ)."""
    if os.geteuid() == 0:
        pytest.skip("root ігнорує права доступу")
    path = tmp_path / "stock.bin"
    make(path, [(1, "a", 4), (2, "b", 5)])
    path.chmod(0o444)
    assert load(7).total_quantity(str(path)) == 9
    assert mmap_calls



def test_no_serialization_libraries():
    """Заборонено готову серіалізацію: pickle, marshal, shelve, numpy, json. Потрібні struct і власний код."""
    import ast
    banned = {"pickle", "marshal", "shelve", "numpy", "construct", "json"}
    for node in ast.walk(ast.parse(Path(load(7).__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in banned for a in node.names), "заборонений модуль"
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, "заборонений модуль"
