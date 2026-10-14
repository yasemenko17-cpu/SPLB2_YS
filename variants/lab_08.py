import mmap
import struct
import os

RECORD_SIZE = 8  # 4 байти ключ + 4 байти значення

def _get_file_size(path: str) -> int:
    """Допоміжна функція для перевірки та отримання розміру файлу."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не знайдено: {path}")
    size = os.path.getsize(path)
    if size % RECORD_SIZE != 0:
        raise ValueError("Розмір файлу не кратний розміру запису")
    return size

def lower_bound(path: str, key: int, probes: list | None = None) -> int:
    """
    Повертає індекс першого запису, ключ якого не менший за key.
    Якщо такого немає, повертає загальну кількість записів.
    """
    size = _get_file_size(path)
    n = size // RECORD_SIZE
    if n == 0:
        return 0

    low, high = 0, n
    with open(path, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as view:
            while low < high:
                mid = (low + high) // 2
                if probes is not None:
                    probes.append(mid)
                
                offset = mid * RECORD_SIZE
                k_val, _ = struct.unpack_from("<II", view, offset)
                
                if k_val < key:
                    low = mid + 1
                else:
                    high = mid
    return low

def find_value(path: str, key: int, probes: list | None = None) -> int | None:
    """
    Шукає значення першого запису з ключем, що дорівнює key.
    Повертає значення (int) або None, якщо ключ не знайдено.
    """
    size = _get_file_size(path)
    n = size // RECORD_SIZE
    if n == 0:
        return None

    idx = lower_bound(path, key, probes)
    if idx >= n:
        return None

    with open(path, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as view:
            offset = idx * RECORD_SIZE
            k_val, v_val = struct.unpack_from("<II", view, offset)
            if k_val == key:
                return v_val
    return None

def count_range(path: str, lo: int, hi: int) -> int:
    """
    Повертає кількість записів із ключем від lo до hi включно.
    """
    if lo > hi:
        return 0
    
    size = _get_file_size(path)
    n = size // RECORD_SIZE
    if n == 0:
        return 0

    # Початок діапазону: перший елемент з ключем >= lo
    start_idx = lower_bound(path, lo)
    if start_idx >= n:
        return 0
    
    # Кінець діапазону: перший елемент з ключем строго більшим за hi (тобто hi + 1)
    end_idx = lower_bound(path, hi + 1)
    
    return end_idx - start_idx