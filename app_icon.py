# -*- coding: utf-8 -*-
"""Путь к иконке приложения. Учитывает запуск из исходников и из exe (PyInstaller)."""
import os
import sys

ICON_NAME = "app.ico"


def get_icon_path():
    """Возвращает путь к файлу иконки app.ico."""
    if getattr(sys, "frozen", False):
        # Сборка PyInstaller: данные извлекаются в sys._MEIPASS
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, ICON_NAME)
