"""
Виджет для ввода даты с автоматическим форматированием дд.мм.гггг.
"""
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt
import re


class DateLineEdit(QLineEdit):
    """QLineEdit с автоматической вставкой точек при вводе даты в формате дд.мм.гггг."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("дд.мм.гггг")
        self.setMaxLength(10)
        self._is_formatting = False
        self.textChanged.connect(self._on_text_changed)

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш с автоматической вставкой точек."""
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Left, Qt.Key_Right, 
                          Qt.Key_Home, Qt.Key_End, Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter,
                          Qt.Key_Up, Qt.Key_Down):
            super().keyPressEvent(event)
            self._format_text()
            return
        
        if event.text() and event.text().isdigit():
            text = self.text()
            cursor_pos = self.cursorPosition()
            digits_only = re.sub(r'[^\d]', '', text)
            new_digit = event.text()
            
            digits_before_cursor = len(re.sub(r'[^\d]', '', text[:cursor_pos]))
            digits_only = digits_only[:digits_before_cursor] + new_digit + digits_only[digits_before_cursor:]
            
            if len(digits_only) > 8:
                digits_only = digits_only[:8]
            
            formatted = self._format_date(digits_only)
            self._is_formatting = True
            self.setText(formatted)
            self._is_formatting = False
            
            new_pos = self._calculate_cursor_position(digits_before_cursor + 1, formatted)
            self.setCursorPosition(new_pos)
        else:
            super().keyPressEvent(event)
            self._format_text()

    def _on_text_changed(self, text: str):
        """Обработка изменения текста (для вставки и других операций)."""
        if self._is_formatting:
            return
        self._format_text()

    def _format_text(self):
        """Форматирует текущий текст поля."""
        if self._is_formatting:
            return
        text = self.text()
        cursor_pos = self.cursorPosition()
        digits_only = re.sub(r'[^\d]', '', text)
        if len(digits_only) > 8:
            digits_only = digits_only[:8]
        formatted = self._format_date(digits_only)
        if formatted != text:
            digits_before = len(re.sub(r'[^\d]', '', text[:cursor_pos]))
            self._is_formatting = True
            self.setText(formatted)
            self._is_formatting = False
            new_pos = self._calculate_cursor_position(digits_before, formatted)
            self.setCursorPosition(new_pos)

    def _format_date(self, digits: str) -> str:
        """Форматирует строку цифр в дд.мм.гггг."""
        if len(digits) == 0:
            return ""
        elif len(digits) <= 2:
            return digits
        elif len(digits) <= 4:
            return f"{digits[:2]}.{digits[2:]}"
        else:
            return f"{digits[:2]}.{digits[2:4]}.{digits[4:]}"

    def _calculate_cursor_position(self, digits_count: int, formatted: str) -> int:
        """Вычисляет позицию курсора после digits_count цифр в отформатированном тексте."""
        count = 0
        for i, char in enumerate(formatted):
            if char.isdigit():
                count += 1
                if count >= digits_count:
                    return i + 1
        return len(formatted)
