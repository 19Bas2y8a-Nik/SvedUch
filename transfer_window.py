"""
Окно «Перевод»: перевод ученика (в другую школу / другой класс) и перевод класса (этап 6).
"""
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QComboBox, QGroupBox, QRadioButton, QButtonGroup,
    QMessageBox, QHeaderView, QAbstractItemView, QCheckBox,
)
from PyQt5.QtCore import Qt

from db import Database
from date_widget import DateLineEdit


def _row_to_dict(row) -> dict:
    """sqlite3.Row -> dict (без id для передачи в pupils_history_insert)."""
    d = {k: row[k] for k in row.keys() if k != "id"}
    return d


def _parse_class_number(number: str) -> tuple[str, str]:
    """Разбирает номер класса на цифры и букву. Например: '5А' -> ('5', 'А'), '11' -> ('11', '')."""
    number = (number or "").strip()
    m = re.match(r"^(\d+)(.*)$", number)
    if not m:
        return ("", number)
    return m.group(1), (m.group(2) or "")


def _increment_class_number(number: str) -> str:
    """Увеличивает число на 1, букву оставляет. '5А' -> '6А', '10Б' -> '11Б'."""
    num_part, letter = _parse_class_number(number)
    if not num_part:
        return number
    try:
        n = int(num_part)
        return f"{n + 1}{letter}"
    except ValueError:
        return number


class TransferWindow(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Перевод")
        self._pupil_rows = []   # результат поиска учеников (блок 1)
        self._class_pupil_rows = []  # ученики выбранного класса (блок 2)
        self._form_map = {}  # id -> number
        self._program_map = {}  # id -> (name, version)

        layout = QVBoxLayout(self)

        # ---- Блок 1: Перевод ученика ----
        grp_pupil = QGroupBox("Перевод ученика")
        layout.addWidget(grp_pupil)
        pupil_layout = QVBoxLayout(grp_pupil)

        # Фильтр
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фамилия:"))
        self.pupil_surname = QLineEdit()
        self.pupil_surname.setPlaceholderText("часть фамилии")
        filter_layout.addWidget(self.pupil_surname)
        filter_layout.addWidget(QLabel("Имя:"))
        self.pupil_name = QLineEdit()
        self.pupil_name.setPlaceholderText("часть имени")
        filter_layout.addWidget(self.pupil_name)
        filter_layout.addWidget(QLabel("Отчество:"))
        self.pupil_patronymic = QLineEdit()
        self.pupil_patronymic.setPlaceholderText("часть отчества")
        filter_layout.addWidget(self.pupil_patronymic)
        filter_layout.addWidget(QLabel("Класс:"))
        self.pupil_class_combo = QComboBox()
        self.pupil_class_combo.setMinimumWidth(80)
        self.pupil_class_combo.addItem("— любой —", None)
        filter_layout.addWidget(self.pupil_class_combo)
        self.btn_pupil_find = QPushButton("Найти")
        self.btn_pupil_find.clicked.connect(self._pupil_find)
        filter_layout.addWidget(self.btn_pupil_find)
        pupil_layout.addLayout(filter_layout)

        # Таблица результатов (одна строка — один ученик)
        self.pupil_table = QTableWidget()
        self.pupil_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pupil_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pupil_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        pupil_layout.addWidget(self.pupil_table)

        # Дата, причина, тип перевода
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Дата перевода:"))
        self.pupil_date = DateLineEdit()
        row2.addWidget(self.pupil_date)
        row2.addWidget(QLabel("Причина перевода:"))
        self.pupil_reason = QLineEdit()
        row2.addWidget(self.pupil_reason)
        pupil_layout.addLayout(row2)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип перевода:"))
        self.radio_out = QRadioButton("В другую школу / окончание школы")
        self.radio_out.setChecked(True)
        self.radio_internal = QRadioButton("В другой класс или на другую программу")
        type_layout.addWidget(self.radio_out)
        type_layout.addWidget(self.radio_internal)
        self.radio_out.toggled.connect(self._on_pupil_transfer_type)
        pupil_layout.addLayout(type_layout)

        # Новый класс/программа (для «другой класс/программа»)
        self.internal_widget = QWidget()
        internal_layout = QHBoxLayout(self.internal_widget)
        internal_layout.setContentsMargins(0, 0, 0, 0)
        internal_layout.addWidget(QLabel("Новый класс:"))
        self.pupil_new_class = QComboBox()
        self.pupil_new_class.addItem("— не менять —", None)
        internal_layout.addWidget(self.pupil_new_class)
        internal_layout.addWidget(QLabel("Новая программа:"))
        self.pupil_new_program = QComboBox()
        self.pupil_new_program.addItem("— не менять —", None)
        internal_layout.addWidget(self.pupil_new_program)
        pupil_layout.addWidget(self.internal_widget)
        self.internal_widget.setVisible(False)

        self.btn_pupil_save = QPushButton("Сохранить (перевод ученика)")
        self.btn_pupil_save.clicked.connect(self._pupil_save)
        pupil_layout.addWidget(self.btn_pupil_save)

        # ---- Блок 2: Перевод класса ----
        grp_class = QGroupBox("Перевод класса")
        layout.addWidget(grp_class)
        class_layout = QVBoxLayout(grp_class)

        class_row = QHBoxLayout()
        class_row.addWidget(QLabel("Класс:"))
        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(100)
        self.class_combo.addItem("— выберите —", None)
        class_row.addWidget(self.class_combo)
        self.btn_class_load = QPushButton("Загрузить учеников")
        self.btn_class_load.clicked.connect(self._class_load)
        class_row.addWidget(self.btn_class_load)
        class_layout.addLayout(class_row)

        self.class_table = QTableWidget()
        self.class_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        class_layout.addWidget(self.class_table)

        class_row2 = QHBoxLayout()
        class_row2.addWidget(QLabel("Дата перевода:"))
        self.class_date = DateLineEdit()
        class_row2.addWidget(self.class_date)
        class_row2.addWidget(QLabel("Причина перевода:"))
        self.class_reason = QLineEdit()
        class_row2.addWidget(self.class_reason)
        class_layout.addLayout(class_row2)

        self.btn_class_save = QPushButton("Сохранить (перевод класса)")
        self.btn_class_save.clicked.connect(self._class_save)
        class_layout.addWidget(self.btn_class_save)

        self._refresh_combos()

    def _refresh_combos(self):
        self._form_map = {r["id"]: r["number"] for r in self.db.forms_get_all()}
        self._program_map = {r["id"]: (r["name"], r["version"]) for r in self.db.programs_get_all()}

        for combo, first_text in [
            (self.pupil_class_combo, "— любой —"),
            (self.pupil_new_class, "— не менять —"),
            (self.class_combo, "— выберите —"),
        ]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(first_text, None)
            for fid, num in self._form_map.items():
                combo.addItem(num, fid)
            combo.blockSignals(False)

        self.pupil_new_program.blockSignals(True)
        self.pupil_new_program.clear()
        self.pupil_new_program.addItem("— не менять —", None)
        for pid, (name, ver) in self._program_map.items():
            self.pupil_new_program.addItem(f"{name} ({ver})", pid)
        self.pupil_new_program.blockSignals(False)

    def _on_pupil_transfer_type(self):
        self.internal_widget.setVisible(self.radio_internal.isChecked())

    def _pupil_find(self):
        form_id = self.pupil_class_combo.currentData()
        surname = self.pupil_surname.text().strip().lower()
        name = self.pupil_name.text().strip().lower()
        patronymic = self.pupil_patronymic.text().strip().lower()
        if form_id is not None:
            rows = self.db.pupils_get_by_form_id(form_id)
        else:
            rows = self.db.pupils_get_all()
        result = []
        for r in rows:
            if surname and (r["surname"] or "").lower().find(surname) < 0:
                continue
            if name and (r["name"] or "").lower().find(name) < 0:
                continue
            if patronymic and (r["patronymic"] or "").lower().find(patronymic) < 0:
                continue
            result.append(r)
        self._pupil_rows = result
        self._fill_pupil_table()

    def _fill_pupil_table(self):
        self.pupil_table.setColumnCount(5)
        self.pupil_table.setHorizontalHeaderLabels(["id", "Класс", "Фамилия", "Имя", "Отчество"])
        self.pupil_table.setRowCount(len(self._pupil_rows))
        for i, r in enumerate(self._pupil_rows):
            form_num = self._form_map.get(r["form_id"], "")
            self.pupil_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.pupil_table.setItem(i, 1, QTableWidgetItem(form_num))
            self.pupil_table.setItem(i, 2, QTableWidgetItem(r["surname"] or ""))
            self.pupil_table.setItem(i, 3, QTableWidgetItem(r["name"] or ""))
            self.pupil_table.setItem(i, 4, QTableWidgetItem(r["patronymic"] or ""))

    def _pupil_save(self):
        row_idx = self.pupil_table.currentRow()
        if row_idx < 0 or row_idx >= len(self._pupil_rows):
            QMessageBox.warning(self, "Выбор", "Выберите ученика в таблице.")
            return
        row = self._pupil_rows[row_idx]
        transfer_date = self.pupil_date.text().strip()
        transfer_reason = self.pupil_reason.text().strip()

        if self.radio_out.isChecked():
            if not transfer_date:
                QMessageBox.warning(self, "Данные", "Укажите дату перевода.")
                return
            try:
                d = _row_to_dict(row)
                self.db.pupils_history_insert(d, transfer_date, transfer_reason)
                self.db.pupils_delete(row["id"])
                QMessageBox.information(self, "Сохранено", "Ученик перенесён в архив.")
                self._pupil_find()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
        else:
            new_form_id = self.pupil_new_class.currentData()
            new_program_id = self.pupil_new_program.currentData()
            if new_form_id is None and new_program_id is None:
                QMessageBox.warning(self, "Данные", "Выберите новый класс и/или программу.")
                return
            try:
                upd = _row_to_dict(row)
                if new_form_id is not None:
                    upd["form_id"] = new_form_id
                if new_program_id is not None:
                    upd["program_id"] = new_program_id
                self.db.pupils_update(row["id"], upd)
                QMessageBox.information(self, "Сохранено", "Запись ученика обновлена.")
                self._pupil_find()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _class_load(self):
        form_id = self.class_combo.currentData()
        if form_id is None:
            QMessageBox.warning(self, "Выбор", "Выберите класс.")
            return
        self._class_pupil_rows = self.db.pupils_get_by_form_id(form_id)
        self._fill_class_table()

    def _fill_class_table(self):
        self.class_table.setColumnCount(6)
        self.class_table.setHorizontalHeaderLabels(["", "id", "Фамилия", "Имя", "Отчество", "Класс"])
        self.class_table.setRowCount(len(self._class_pupil_rows))
        for i, r in enumerate(self._class_pupil_rows):
            cb = QCheckBox()
            self.class_table.setCellWidget(i, 0, cb)
            form_num = self._form_map.get(r["form_id"], "")
            self.class_table.setItem(i, 1, QTableWidgetItem(str(r["id"])))
            self.class_table.setItem(i, 2, QTableWidgetItem(r["surname"] or ""))
            self.class_table.setItem(i, 3, QTableWidgetItem(r["name"] or ""))
            self.class_table.setItem(i, 4, QTableWidgetItem(r["patronymic"] or ""))
            self.class_table.setItem(i, 5, QTableWidgetItem(form_num))

    def _class_save(self):
        form_id = self.class_combo.currentData()
        if form_id is None:
            QMessageBox.warning(self, "Выбор", "Выберите класс и загрузите учеников.")
            return
        form_number = self._form_map.get(form_id, "")
        transfer_date = self.class_date.text().strip()
        transfer_reason = self.class_reason.text().strip()
        if not transfer_date:
            QMessageBox.warning(self, "Данные", "Укажите дату перевода.")
            return

        selected = []
        for i in range(self.class_table.rowCount()):
            w = self.class_table.cellWidget(i, 0)
            if isinstance(w, QCheckBox) and w.isChecked():
                if i < len(self._class_pupil_rows):
                    selected.append(self._class_pupil_rows[i])
        if not selected:
            QMessageBox.warning(self, "Выбор", "Отметьте хотя бы одного ученика.")
            return

        is_11 = form_number.strip().startswith("11")
        try:
            if is_11:
                for r in selected:
                    d = _row_to_dict(r)
                    self.db.pupils_history_insert(d, transfer_date, transfer_reason)
                    self.db.pupils_delete(r["id"])
                QMessageBox.information(self, "Сохранено", "Ученики 11-го класса перенесены в архив.")
            else:
                new_number = _increment_class_number(form_number)
                forms_all = self.db.forms_get_all()
                new_form_id = None
                for f in forms_all:
                    if f["number"] == new_number:
                        new_form_id = f["id"]
                        break
                if new_form_id is None:
                    new_form_id = self.db.forms_add(new_number)
                for r in selected:
                    upd = _row_to_dict(r)
                    upd["form_id"] = new_form_id
                    self.db.pupils_update(r["id"], upd)
                QMessageBox.information(self, "Сохранено", f"Номер класса обновлён на {new_number}.")
            self._class_load()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
