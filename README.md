# Стартовий проєкт SP-LAB02

1. Відкрийте проєкт у GitHub Codespaces (Code → Codespaces → Create codespace) або локально на Linux: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`.
2. Визначте свою задачу за номером варіанта: задача = `(номер - 1) // 3 + 1`. Реалізуйте її у файлі `variants/lab_NN.py` за карткою.
3. Запускайте відкриті тести своєї задачі: `pytest tests/test_lab_NN.py` (NN з двома цифрами). Права root не потрібні.
4. Змінюйте лише свій файл у `variants/` (і за бажанням `tests/test_my.py`).
5. Байти файла дивіться утилітою `xxd файл`; системні виклики вашого рішення: `strace -f -e trace=openat,mmap,munmap,msync -o trace.txt python3 ...`.
