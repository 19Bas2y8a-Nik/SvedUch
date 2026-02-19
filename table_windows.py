"""
Окно «Таблицы» и диалоги для работы с таблицами БД (этап 3).
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QHeaderView,
    QLabel, QAbstractItemView, QTabWidget,
)
from PyQt5.QtCore import Qt

from db import Database
from pupil_form import PupilEntryTab, EditPupilTab


class TablesWindow(QWidget):
    """Окно с кнопками для открытия работы с каждой таблицей."""
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Таблицы")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите таблицу для просмотра и редактирования:"))
        btn_layout = QVBoxLayout()
        for title, handler in [
            ("Классы (forms)", self._open_forms),
            ("Программы (programs)", self._open_programs),
            ("Рекомендации (recommendations)", self._open_recommendations),
            ("Ученики (pupils)", self._open_pupils),
            ("Архив (pupils_history)", self._open_archive),
            ("Настройки (settings)", self._open_settings),
        ]:
            b = QPushButton(title)
            b.clicked.connect(handler)
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)
        self.setMinimumSize(320, 320)

    def _open_window(self, widget_class, *args, **kwargs):
        """Открывает дочернее окно как отдельное (Qt.Window) и выводит на передний план."""
        w = widget_class(self.db, self, *args, **kwargs)
        w.setWindowFlags(w.windowFlags() | Qt.Window)
        w.show()
        w.raise_()
        w.activateWindow()

    def _open_forms(self):
        self._open_window(FormsTableDialog)

    def _open_programs(self):
        self._open_window(ProgramsTableDialog)

    def _open_recommendations(self):
        self._open_window(RecommendationsTableDialog)

    def _open_pupils(self):
        self._open_window(PupilsWindow)

    def _open_archive(self):
        self._open_window(ArchiveTableDialog)

    def _open_settings(self):
        self._open_window(SettingsDialog)


def _row_to_dict(row) -> dict:
    """sqlite3.Row -> dict."""
    return {k: row[k] for k in row.keys()}


# --- Справочник: Классы ---
class FormsTableDialog(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Классы")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["id", "Номер класса"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self._add)
        edit_btn = QPushButton("Изменить")
        edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("Удалить")
        del_btn.clicked.connect(self._delete)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setToolTip("Обновить данные из базы (не сохраняет введённую информацию)")
        refresh_btn.clicked.connect(self._refresh)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        self._refresh()

    def _refresh(self):
        rows = self.db.forms_get_all()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["number"] or ""))

    def _add(self):
        d = FormEditDialog(None, "", self)
        if d.exec_() == QDialog.Accepted and d.number:
            try:
                self.db.forms_add(d.number)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для редактирования.")
            return
        id_val = int(self.table.item(row, 0).text())
        number = self.table.item(row, 1).text()
        d = FormEditDialog(id_val, number, self)
        if d.exec_() == QDialog.Accepted and d.number:
            try:
                self.db.forms_update(id_val, d.number)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для удаления.")
            return
        id_val = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Подтверждение", "Удалить этот класс?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.db.forms_delete(id_val)
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class FormEditDialog(QDialog):
    def __init__(self, id_val, number: str, parent=None):
        super().__init__(parent)
        self.id_val = id_val
        self.setWindowTitle("Редактирование класса" if id_val is not None else "Новый класс")
        layout = QFormLayout(self)
        self.number_edit = QLineEdit()
        self.number_edit.setText(number)
        self.number_edit.setPlaceholderText("Например: 5А")
        layout.addRow("Номер класса:", self.number_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addRow(bb)

    @property
    def number(self):
        return self.number_edit.text().strip()


# --- Справочник: Программы ---
class ProgramsTableDialog(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Программы")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["id", "Наименование", "Версия"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        for label, slot in [("Добавить", self._add), ("Изменить", self._edit), ("Удалить", self._delete), ("Обновить", self._refresh)]:
            b = QPushButton(label)
            if label == "Обновить":
                b.setToolTip("Обновить данные из базы (не сохраняет введённую информацию)")
            b.clicked.connect(slot)
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)
        self._refresh()

    def _refresh(self):
        rows = self.db.programs_get_all()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["name"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(r["version"] or ""))

    def _add(self):
        d = ProgramEditDialog(None, "", "", self)
        if d.exec_() == QDialog.Accepted and d.name:
            try:
                self.db.programs_add(d.name, d.version)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для редактирования.")
            return
        id_val = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        version = self.table.item(row, 2).text()
        d = ProgramEditDialog(id_val, name, version, self)
        if d.exec_() == QDialog.Accepted and d.name:
            try:
                self.db.programs_update(id_val, d.name, d.version)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для удаления.")
            return
        id_val = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Подтверждение", "Удалить эту программу?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.db.programs_delete(id_val)
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class ProgramEditDialog(QDialog):
    def __init__(self, id_val, name: str, version: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование программы" if id_val is not None else "Новая программа")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setText(name)
        layout.addRow("Наименование:", self.name_edit)
        self.version_edit = QLineEdit()
        self.version_edit.setText(version)
        layout.addRow("Версия:", self.version_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addRow(bb)

    @property
    def name(self):
        return self.name_edit.text().strip()

    @property
    def version(self):
        return self.version_edit.text().strip()


# --- Справочник: Рекомендации ---
class RecommendationsTableDialog(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Рекомендации специалистам")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["id", "Специалист", "Рекомендация"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        for label, slot in [("Добавить", self._add), ("Удалить", self._delete), ("Обновить", self._refresh)]:
            b = QPushButton(label)
            if label == "Обновить":
                b.setToolTip("Обновить данные из базы (не сохраняет введённую информацию)")
            b.clicked.connect(slot)
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)
        self._refresh()

    def _refresh(self):
        rows = self.db.recommendations_get_all()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(r["specialist_name"] or ""))
            self.table.setItem(i, 2, QTableWidgetItem(r["recommendation_name"] or ""))

    def _add(self):
        d = RecommendationEditDialog("", "", self)
        if d.exec_() == QDialog.Accepted and d.specialist_name:
            try:
                self.db.recommendations_add(d.specialist_name, d.recommendation_name)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для удаления.")
            return
        id_val = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Подтверждение", "Удалить эту рекомендацию?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.db.recommendations_delete(id_val)
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class RecommendationEditDialog(QDialog):
    def __init__(self, specialist_name: str, recommendation_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая рекомендация")
        layout = QFormLayout(self)
        self.spec_edit = QLineEdit()
        self.spec_edit.setText(specialist_name)
        self.spec_edit.setPlaceholderText("Профиль специалиста")
        layout.addRow("Специалист:", self.spec_edit)
        self.rec_edit = QLineEdit()
        self.rec_edit.setText(recommendation_name)
        self.rec_edit.setPlaceholderText("Текст рекомендации")
        layout.addRow("Рекомендация:", self.rec_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addRow(bb)

    @property
    def specialist_name(self):
        return self.spec_edit.text().strip()

    @property
    def recommendation_name(self):
        return self.rec_edit.text().strip()


# --- Ученики: вкладки «Список» и «Добавить ученика» ---
class PupilsWindow(QWidget):
    """Окно «Ученики»: вкладка со списком и вкладка ввода нового ученика."""
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Ученики")
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.list_tab = PupilsTableDialog(self.db, self, pupils_window=self)
        self.tabs.addTab(self.list_tab, "Список учеников")
        self.tabs.addTab(PupilEntryTab(self.db, self), "Добавить ученика")
        self.edit_tab = EditPupilTab(self.db, self)
        self.tabs.addTab(self.edit_tab, "Изменения по ученику")
        layout.addWidget(self.tabs)
        self.setMinimumSize(900, 500)

    def switch_to_add_tab(self):
        self.tabs.setCurrentIndex(1)

    def switch_to_edit_tab_with_pupil_id(self, pupil_id: int) -> bool:
        if self.edit_tab.load_pupil_by_id(pupil_id):
            self.tabs.setCurrentIndex(2)
            return True
        return False


class PupilsTableDialog(QWidget):
    PAGE_SIZE = 50

    def __init__(self, db: Database, parent=None, pupils_window=None):
        super().__init__(parent)
        self.db = db
        self.pupils_window = pupils_window
        self._all_rows = []
        self._current_page = 0
        self.setWindowTitle("Ученики")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self._build_columns()
        layout.addWidget(self.table)

        # Пагинация
        page_layout = QHBoxLayout()
        self.page_label = QLabel("Страница: 0 (0 из 0)")
        page_layout.addWidget(self.page_label)
        btn_prev = QPushButton("◄ Предыдущая")
        btn_prev.clicked.connect(self._prev_page)
        page_layout.addWidget(btn_prev)
        btn_next = QPushButton("Следующая ►")
        btn_next.clicked.connect(self._next_page)
        page_layout.addWidget(btn_next)
        page_layout.addStretch()
        layout.addLayout(page_layout)

        # CRUD и Обновить
        crud_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add)
        crud_layout.addWidget(btn_add)
        btn_edit = QPushButton("Изменить")
        btn_edit.clicked.connect(self._edit)
        crud_layout.addWidget(btn_edit)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete)
        crud_layout.addWidget(btn_delete)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setToolTip("Обновить данные из базы (не сохраняет введённую информацию)")
        refresh_btn.clicked.connect(self._refresh)
        crud_layout.addWidget(refresh_btn)
        layout.addLayout(crud_layout)

        self._refresh()

    def _build_columns(self):
        headers = [
            "id", "Класс", "Фамилия", "Имя", "Отчество", "Дата рожд.", "ПМПК дата", "ПМПК №",
            "Программа", "Версия", "Приказ №", "Дата приказа",
            "Рек.1", "Рек.2", "Рек.3", "Рек.4", "Рек.5"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

    def _refresh(self):
        forms = {r["id"]: r["number"] for r in self.db.forms_get_all()}
        programs = {r["id"]: (r["name"], r["version"]) for r in self.db.programs_get_all()}
        self._all_rows = list(self.db.pupils_get_all())
        self._current_page = 0
        self._fill_page(forms, programs)

    def _fill_page(self, forms=None, programs=None):
        if forms is None:
            forms = {r["id"]: r["number"] for r in self.db.forms_get_all()}
        if programs is None:
            programs = {r["id"]: (r["name"], r["version"]) for r in self.db.programs_get_all()}
        total = len(self._all_rows)
        start = self._current_page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, total)
        page_rows = self._all_rows[start:end]
        self.table.setRowCount(len(page_rows))
        for i, r in enumerate(page_rows):
            form_num = forms.get(r["form_id"], str(r["form_id"]))
            prog = programs.get(r["program_id"], ("", ""))
            prog_name, prog_ver = prog[0], prog[1]
            cells = [
                str(r["id"]), form_num, r["surname"] or "", r["name"] or "", r["patronymic"] or "",
                r["birth_date"] or "", r["pmpk_date"] or "", r["pmpk_number"] or "",
                prog_name, prog_ver, r["order_number"] or "", r["order_date"] or "",
                (r["rec_spec_1"] or ""), (r["rec_spec_2"] or ""), (r["rec_spec_3"] or ""),
                (r["rec_spec_4"] or ""), (r["rec_spec_5"] or ""),
            ]
            for j, val in enumerate(cells):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()
        self.page_label.setText(
            f"Страница: {self._current_page + 1} "
            f"(строки {start + 1}–{end} из {total})" if total else "Страница: 0 (0 из 0)"
        )

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._fill_page()

    def _next_page(self):
        total = len(self._all_rows)
        if (self._current_page + 1) * self.PAGE_SIZE < total:
            self._current_page += 1
            self._fill_page()

    def _add(self):
        if self.pupils_window:
            self.pupils_window.switch_to_add_tab()

    def _edit(self):
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для редактирования.")
            return
        id_item = self.table.item(row_idx, 0)
        if not id_item:
            return
        try:
            pupil_id = int(id_item.text())
        except ValueError:
            return
        if self.pupils_window:
            self.pupils_window.switch_to_edit_tab_with_pupil_id(pupil_id)

    def _delete(self):
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для удаления.")
            return
        id_item = self.table.item(row_idx, 0)
        if not id_item:
            return
        try:
            pupil_id = int(id_item.text())
        except ValueError:
            return
        surname = self.table.item(row_idx, 2).text() if self.table.item(row_idx, 2) else ""
        name = self.table.item(row_idx, 3).text() if self.table.item(row_idx, 3) else ""
        if QMessageBox.question(
            self, "Подтверждение", f"Удалить ученика {surname} {name}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            self.db.pupils_delete(pupil_id)
            QMessageBox.information(self, "Успех", "Запись удалена.")
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


# --- Архив (просмотр) ---
class ArchiveTableDialog(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Архив (pupils_history)")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        headers = [
            "id", "Класс", "Фамилия", "Имя", "Отчество", "Дата перевода", "Причина перевода"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setToolTip("Обновить данные из базы (не сохраняет введённую информацию)")
        refresh_btn.clicked.connect(self._refresh)
        layout.addWidget(refresh_btn)
        self._refresh()

    def _refresh(self):
        forms = {r["id"]: r["number"] for r in self.db.forms_get_all()}
        rows = self.db.pupils_history_get_all()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            form_num = forms.get(r["form_id"], str(r["form_id"]))
            cells = [
                str(r["id"]), form_num, r["surname"] or "", r["name"] or "", r["patronymic"] or "",
                r["transfer_date"] or "", r["transfer_reason"] or "",
            ]
            for j, val in enumerate(cells):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()


# --- Настройки ---
class SettingsDialog(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Настройки")
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Ключ", "Значение"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить / изменить")
        add_btn.clicked.connect(self._add_or_edit)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setToolTip("Обновить данные из базы (не сохраняет введённую информацию)")
        refresh_btn.clicked.connect(self._refresh)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        self._refresh()

    def _refresh(self):
        rows = self.db.settings_get_all()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["key"] or ""))
            self.table.setItem(i, 1, QTableWidgetItem(r["value"] or ""))

    def _add_or_edit(self):
        key = ""
        value = ""
        row = self.table.currentRow()
        if row >= 0:
            key = self.table.item(row, 0).text()
            value = self.table.item(row, 1).text()
        d = SettingEditDialog(key, value, self)
        if d.exec_() == QDialog.Accepted and d.key:
            try:
                self.db.settings_set(d.key, d.value)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))


class SettingEditDialog(QDialog):
    def __init__(self, key: str, value: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка")
        layout = QFormLayout(self)
        self.key_edit = QLineEdit()
        self.key_edit.setText(key)
        self.key_edit.setPlaceholderText("Например: db_path, window_geometry")
        layout.addRow("Ключ:", self.key_edit)
        self.value_edit = QLineEdit()
        self.value_edit.setText(value)
        layout.addRow("Значение:", self.value_edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addRow(bb)

    @property
    def key(self):
        return self.key_edit.text().strip()

    @property
    def value(self):
        return self.value_edit.text().strip()
