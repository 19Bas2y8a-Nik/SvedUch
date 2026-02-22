"""
Окно «Выборки»: фильтры по классу/программе, список учеников или агрегация по программе,
выбор полей, экспорт в Excel (этап 5).
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QGroupBox, QRadioButton, QButtonGroup, QFileDialog,
    QMessageBox, QHeaderView, QScrollArea,     QCheckBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from app_icon import get_icon_path
from db import Database

# Все колонки для режима «Список учеников» (ключ, заголовок)
PUPIL_COLUMNS = [
    ("id", "id"),
    ("class", "Класс"),
    ("surname", "Фамилия"),
    ("name", "Имя"),
    ("patronymic", "Отчество"),
    ("birth_date", "Дата рожд."),
    ("address", "Дом.адр."),
    ("gender", "Пол"),
    ("pmpk_date", "ПМПК дата"),
    ("pmpk_number", "ПМПК №"),
    ("program_name", "Программа"),
    ("program_version", "Версия"),
    ("order_number", "Приказ №"),
    ("order_date", "Дата приказа"),
    ("rec_spec_1", "Рек.1"),
    ("rec_spec_2", "Рек.2"),
    ("rec_spec_3", "Рек.3"),
    ("rec_spec_4", "Рек.4"),
    ("rec_spec_5", "Рек.5"),
]


class QueriesWindow(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Выборки")
        # Установка иконки
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self._rows_list = []   # текущие строки (список dict/Row) для экспорта
        self._mode_count = False  # True = режим «Количество по программе»
        self._result_is_aggregate = False  # True = в таблице общая статистика (программа «все»)
        self._form_map = {}
        self._program_map = {}

        layout = QVBoxLayout(self)

        # Критерии фильтрации
        filter_grp = QGroupBox("Критерии")
        filter_layout = QHBoxLayout(filter_grp)
        filter_layout.addWidget(QLabel("Класс:"))
        self.combo_class = QComboBox()
        self.combo_class.setMinimumWidth(120)
        self.combo_class.addItem("— все —", None)
        filter_layout.addWidget(self.combo_class)
        filter_layout.addWidget(QLabel("Программа:"))
        self.combo_program = QComboBox()
        self.combo_program.setMinimumWidth(200)
        self.combo_program.addItem("— все —", None)
        filter_layout.addWidget(self.combo_program)
        layout.addWidget(filter_grp)

        # Режим: список учеников / количество по программе
        mode_grp = QGroupBox("Режим")
        mode_layout = QHBoxLayout(mode_grp)
        self.radio_list = QRadioButton("Список учеников")
        self.radio_list.setChecked(True)
        self.radio_count = QRadioButton("Количество учеников по программе")
        mode_layout.addWidget(self.radio_list)
        mode_layout.addWidget(self.radio_count)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.radio_list)
        self.mode_group.addButton(self.radio_count)
        layout.addWidget(mode_grp)

        # Выбор полей (для списка учеников и для списка по выбранной программе)
        fields_grp = QGroupBox("Отображаемые поля (для списка учеников и списка по программе)")
        fields_inner = QWidget()
        fields_layout = QHBoxLayout(fields_inner)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        self.field_checks = []
        for key, title in PUPIL_COLUMNS:
            cb = QCheckBox(title)
            cb.setChecked(True)
            cb.setProperty("col_key", key)
            self.field_checks.append(cb)
            fields_layout.addWidget(cb)
        fields_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidget(fields_inner)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(60)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        fields_grp_layout = QVBoxLayout(fields_grp)
        fields_grp_layout.addWidget(scroll)
        layout.addWidget(fields_grp)

        # Кнопки Выполнить, Экспорт, Очистить
        btn_layout = QHBoxLayout()
        self.btn_run = QPushButton("Выполнить")
        self.btn_run.clicked.connect(self._run)
        self.btn_export = QPushButton("Экспорт в Excel")
        self.btn_export.clicked.connect(self._export_excel)
        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self._clear)
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        # Таблица результатов
        layout.addWidget(QLabel("Результат:"))
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        self._refresh_combos()

    def _refresh_combos(self):
        """Заполнить комбобоксы класса и программы."""
        self._form_map = {r["id"]: r["number"] for r in self.db.forms_get_all()}
        self._program_map = {r["id"]: (r["name"], r["version"]) for r in self.db.programs_get_all()}

        self.combo_class.blockSignals(True)
        self.combo_program.blockSignals(True)
        self.combo_class.clear()
        self.combo_program.clear()
        self.combo_class.addItem("— все —", None)
        self.combo_program.addItem("— все —", None)
        for fid, num in self._form_map.items():
            self.combo_class.addItem(num, fid)
        for pid, (name, ver) in self._program_map.items():
            self.combo_program.addItem(f"{name} ({ver})", pid)
        self.combo_class.blockSignals(False)
        self.combo_program.blockSignals(False)

    def _run(self):
        self._mode_count = self.radio_count.isChecked()
        program_id = self.combo_program.currentData()
        if self._mode_count and program_id is None:
            self._run_count_by_program()
        elif self._mode_count and program_id is not None:
            self._run_pupils_by_program(program_id)
        else:
            self._run_pupils_list()

    def _run_pupils_list(self):
        self._result_is_aggregate = False
        form_id = self.combo_class.currentData()
        program_id = self.combo_program.currentData()
        if form_id is not None and program_id is not None:
            rows = self.db.pupils_get_by_form_id(form_id)
            rows = [r for r in rows if r["program_id"] == program_id]
        elif form_id is not None:
            rows = self.db.pupils_get_by_form_id(form_id)
        elif program_id is not None:
            rows = self.db.pupils_get_by_program_id(program_id)
        else:
            rows = self.db.pupils_get_all()
        self._rows_list = list(rows)
        self._fill_pupils_table()

    def _run_pupils_by_program(self, program_id: int):
        """Список учеников по выбранной программе с выбором полей."""
        self._result_is_aggregate = False
        rows = self.db.pupils_get_by_program_id(program_id)
        self._rows_list = list(rows)
        self._fill_pupils_table()

    def _run_count_by_program(self):
        """Общая статистика: количество учеников по каждой программе (программа «— все —»)."""
        self._result_is_aggregate = True
        rows = self.db.pupils_count_by_program()
        self._rows_list = list(rows)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Программа", "Версия", "Количество учеников", "program_id"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["program_name"] or "")))
            self.table.setItem(i, 1, QTableWidgetItem(str(r["program_version"] or "")))
            self.table.setItem(i, 2, QTableWidgetItem(str(r["pupils_count"])))
            self.table.setItem(i, 3, QTableWidgetItem(str(r["program_id"] or "")))
        self.table.setColumnHidden(3, True)

    def _row_to_cells(self, r) -> list:
        """Одна строка pupils (Row) в список ячеек для отображаемых колонок."""
        form_num = self._form_map.get(r["form_id"], str(r["form_id"]))
        prog = self._program_map.get(r["program_id"], ("", ""))
        data = {
            "id": str(r["id"]),
            "class": form_num,
            "surname": r["surname"] or "",
            "name": r["name"] or "",
            "patronymic": r["patronymic"] or "",
            "birth_date": r["birth_date"] or "",
            "address": (r["address"] if "address" in r.keys() else "") or "",
            "gender": (r["gender"] if "gender" in r.keys() else "") or "",
            "pmpk_date": r["pmpk_date"] or "",
            "pmpk_number": r["pmpk_number"] or "",
            "program_name": prog[0],
            "program_version": prog[1],
            "order_number": r["order_number"] or "",
            "order_date": r["order_date"] or "",
            "rec_spec_1": r["rec_spec_1"] or "",
            "rec_spec_2": r["rec_spec_2"] or "",
            "rec_spec_3": r["rec_spec_3"] or "",
            "rec_spec_4": r["rec_spec_4"] or "",
            "rec_spec_5": r["rec_spec_5"] or "",
        }
        return [data.get(key, "") for key, _ in PUPIL_COLUMNS]

    def _get_selected_columns(self):
        """Список выбранных полей: [(key, title), ...]. Пусто, если ничего не выбрано."""
        return [(PUPIL_COLUMNS[i][0], PUPIL_COLUMNS[i][1]) for i in range(len(PUPIL_COLUMNS))
                if self.field_checks[i].isChecked()]

    def _fill_pupils_table(self):
        selected = self._get_selected_columns()
        if not selected:
            QMessageBox.information(self, "Поля", "Выберите хотя бы одно поле для отображения.")
            return
        self.table.setColumnCount(len(selected))
        self.table.setHorizontalHeaderLabels([t for _, t in selected])
        self.table.setRowCount(len(self._rows_list))
        keys = [k for k, _ in selected]
        for i, r in enumerate(self._rows_list):
            cells = self._row_to_cells(r)
            cell_map = dict(zip([k for k, _ in PUPIL_COLUMNS], cells))
            for j, key in enumerate(keys):
                self.table.setItem(i, j, QTableWidgetItem(str(cell_map.get(key, ""))))

    def _export_excel(self):
        if not self._rows_list:
            QMessageBox.information(self, "Экспорт", "Нет данных для экспорта. Выполните выборку.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить в Excel", "", "Excel (*.xlsx);;Все файлы (*)"
        )
        if not path:
            return
        try:
            self._write_excel(path)
            QMessageBox.information(self, "Экспорт", f"Файл сохранён:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))

    def _write_excel(self, path: str):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Выборка"
        if self._result_is_aggregate:
            headers = ["Программа", "Версия", "Количество учеников"]
            ws.append(headers)
            for r in self._rows_list:
                ws.append([r["program_name"] or "", r["program_version"] or "", r["pupils_count"]])
        else:
            selected = self._get_selected_columns()
            if not selected:
                selected = [(k, t) for k, t in PUPIL_COLUMNS]
            headers = [t for _, t in selected]
            keys = [k for k, _ in selected]
            ws.append(headers)
            cell_map_keys = [k for k, _ in PUPIL_COLUMNS]
            for r in self._rows_list:
                cells = self._row_to_cells(r)
                cell_map = dict(zip(cell_map_keys, cells))
                row_data = [cell_map.get(key, "") for key in keys]
                ws.append(row_data)
        wb.save(path)

    def _clear(self):
        self._rows_list = []
        self._result_is_aggregate = False
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.combo_class.setCurrentIndex(0)
        self.combo_program.setCurrentIndex(0)
        self.radio_list.setChecked(True)
