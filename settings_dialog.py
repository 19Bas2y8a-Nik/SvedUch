"""
Окно настроек приложения и диалог "О программе".
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QFormLayout, QDialogButtonBox, QMessageBox, QSpinBox, QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont

from version import __version__
from app_icon import get_icon_path
from db import Database


class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Настройки")
        self.setModal(True)
        
        # Установка иконки
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        layout = QVBoxLayout(self)
        
        # Группа "Тема оформления"
        theme_group = QGroupBox("Тема оформления")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        theme_layout.addRow("Тема:", self.theme_combo)
        
        # Загружаем текущую тему
        current_theme = self.db.settings_get("theme") or "Светлая"
        if current_theme == "Тёмная":
            self.theme_combo.setCurrentIndex(1)
        else:
            self.theme_combo.setCurrentIndex(0)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Группа "Размер шрифта"
        font_group = QGroupBox("Размер шрифта")
        font_layout = QFormLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(24)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" pt")
        
        # Загружаем текущий размер шрифта
        font_size_str = self.db.settings_get("font_size")
        if font_size_str:
            try:
                font_size = int(font_size_str)
                if 8 <= font_size <= 24:
                    self.font_size_spin.setValue(font_size)
            except ValueError:
                pass
        
        font_layout.addRow("Размер шрифта панелей:", self.font_size_spin)
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        buttons.accepted.connect(self._apply_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setMinimumWidth(350)
    
    def _apply_settings(self):
        """Применяет настройки и сохраняет их в БД."""
        # Сохраняем тему
        theme = "Тёмная" if self.theme_combo.currentIndex() == 1 else "Светлая"
        self.db.settings_set("theme", theme)
        
        # Сохраняем размер шрифта
        font_size = str(self.font_size_spin.value())
        self.db.settings_set("font_size", font_size)
        
        self.accept()


class AboutDialog(QDialog):
    """Диалог "О программе"."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setModal(True)
        
        # Установка иконки
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Название программы
        title_label = QLabel("SvedUch")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Описание
        desc_label = QLabel(
            "Программа для учёта сведений об учениках школы.\n\n"
            "Позволяет:\n"
            "• Вводить и редактировать сведения об учениках\n"
            "• Формировать выборки по классам и программам\n"
            "• Осуществлять перевод учеников между классами\n"
            "• Экспортировать данные в Excel\n\n"
            f"Версия: {__version__}"
        )
        desc_label.setAlignment(Qt.AlignLeft)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Кнопка "Закрыть"
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
