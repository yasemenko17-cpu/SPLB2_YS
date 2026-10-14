import pytest
import os
import struct
from conftest import load

# Завантажуємо модуль для 8-ї задачі
lab_08 = load(8)

@pytest.fixture
def sample_sorted_file(tmp_path):
    d = tmp_path / "test_sorted.bin"
    # Записуємо 4 пари (ключ, значення): (10, 100), (20, 200), (20, 205), (30, 300)
    # Формат <II означає 2 числа (ключ і значення). Оскільки пар 4, 
    # використовуємо чотири повторення пари: <IIIIIIII (або 8 цілих чисел).
    data = struct.pack("<IIIIIIII", 10, 100, 20, 200, 20, 205, 30, 300)
    d.write_bytes(data)
    return str(d)

def test_my_find_value(sample_sorted_file):
    # Перевірка пошуку існуючого та неіснуючого значень
    assert lab_08.find_value(sample_sorted_file, 20) == 200
    assert lab_08.find_value(sample_sorted_file, 99) is None

def test_my_count_range(sample_sorted_file):
    # Перевірка підрахунку кількості в діапазоні
    assert lab_08.count_range(sample_sorted_file, 15, 25) == 2
    assert lab_08.count_range(sample_sorted_file, 35, 40) == 0

def test_my_invalid_size(tmp_path):
    # Перевірка винятку, коли розмір файлу не кратний 8 байтам
    bad_file = tmp_path / "bad.bin"
    bad_file.write_bytes(b"12345") # 5 байтів замість кратності 8
    with pytest.raises(ValueError, match="Розмір файлу не кратний розміру запису"):
        lab_08.lower_bound(str(bad_file), 10)