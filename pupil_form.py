"""
Форма ввода сведений об ученике и временная таблица (этап 4).
Макет по PROJECT.md п. 4.3.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QMenu, QDialog, QListWidget, QDialogButtonBox, QMessageBox,
    QGroupBox, QListWidgetItem,
)
from PyQt5.QtCore import pyqtSignal

from db import Database


def _pad_specialists(specialists: list, size: int = 5) -> list:
    """Добить список специалистов до size (для отображения 5 слотов)."""
    return (specialists + ["—"] * size)[:size]


class RecommendationSelectDialog(QDialog):
    """Диалог мультивыбора рекомендаций для одного специалиста."""
    def __init__(self, specialist_name: str, current_text: str, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.specialist_name = specialist_name
        self.setWindowTitle(f"Рекомендации: {specialist_name}")
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        recs = db.recommendations_get_by_specialist(specialist_name)
        for r in recs:
            item = QListWidgetItem(r["recommendation_name"])
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)
        # Предвыбор: current_text содержит рекомендации через ";"
        if current_text and current_text != "нет":
            for name in [s.strip() for s in current_text.split(";") if s.strip()]:
                for i in range(self.list_widget.count()):
                    if self.list_widget.item(i).text() == name:
                        self.list_widget.item(i).setSelected(True)
                        break
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def selected_as_text(self) -> str:
        """Выбранные рекомендации через «;» или «нет»."""
        names = [self.list_widget.item(i).text() for i in range(self.list_widget.count())
                 if self.list_widget.item(i).isSelected()]
        return "; ".join(names) if names else "нет"


class PupilEntryWidget(QWidget):
    """Форма ввода данных ученика: поля, выбор класса/программы, блок рекомендаций."""
    data_changed = pyqtSignal()

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._form_id = None   # id выбранного класса
        self._program_id = None # id выбранной программы
        self._rec_specs = ["нет"] * 5

        layout = QVBoxLayout(self)

        # 1-й ряд: Класс, Фамилия, Имя, Отчество, Дата рождения
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Класс:"))
        self.class_edit = QLineEdit()
        self.class_edit.setReadOnly(True)
        self.class_edit.setPlaceholderText("выберите из списка")
        row1.addWidget(self.class_edit)
        self.btn_class = QPushButton("…")
        self.btn_class.setMaximumWidth(36)
        self.btn_class.clicked.connect(self._on_select_class)
        row1.addWidget(self.btn_class)
        row1.addWidget(QLabel("Фамилия:"))
        self.surname_edit = QLineEdit()
        row1.addWidget(self.surname_edit)
        row1.addWidget(QLabel("Имя:"))
        self.name_edit = QLineEdit()
        row1.addWidget(self.name_edit)
        row1.addWidget(QLabel("Отчество:"))
        self.patronymic_edit = QLineEdit()
        row1.addWidget(self.patronymic_edit)
        row1.addWidget(QLabel("Дата рождения:"))
        self.birth_date_edit = QLineEdit()
        self.birth_date_edit.setPlaceholderText("дд.мм.гггг")
        row1.addWidget(self.birth_date_edit)
        layout.addLayout(row1)

        # 2-й ряд: Дата заключения ПМПК, Номер заключения ПМПК, Номер приказа, Дата приказа
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Дата заключения ПМПК:"))
        self.pmpk_date_edit = QLineEdit()
        self.pmpk_date_edit.setPlaceholderText("дд.мм.гггг")
        row2.addWidget(self.pmpk_date_edit)
        row2.addWidget(QLabel("Номер заключения ПМПК:"))
        self.pmpk_number_edit = QLineEdit()
        row2.addWidget(self.pmpk_number_edit)
        row2.addWidget(QLabel("Номер приказа:"))
        self.order_number_edit = QLineEdit()
        row2.addWidget(self.order_number_edit)
        row2.addWidget(QLabel("Дата приказа:"))
        self.order_date_edit = QLineEdit()
        self.order_date_edit.setPlaceholderText("дд.мм.гггг")
        row2.addWidget(self.order_date_edit)
        layout.addLayout(row2)

        # 3-й ряд: Программа, Версия
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Программа:"))
        self.program_edit = QLineEdit()
        self.program_edit.setReadOnly(True)
        self.program_edit.setPlaceholderText("выберите из списка")
        row3.addWidget(self.program_edit)
        row3.addWidget(QLabel("Версия:"))
        self.version_edit = QLineEdit()
        self.version_edit.setReadOnly(True)
        row3.addWidget(self.version_edit)
        self.btn_program = QPushButton("…")
        self.btn_program.setMaximumWidth(36)
        self.btn_program.clicked.connect(self._on_select_program)
        row3.addWidget(self.btn_program)
        layout.addLayout(row3)

        # Блок «Рекомендации специалистам»: 5 специалистов
        grp = QGroupBox("Рекомендации специалистам")
        rec_layout = QVBoxLayout(grp)
        specialists = _pad_specialists(self.db.recommendations_get_specialists())
        self.rec_edits = []
        self.rec_buttons = []
        for i, spec_name in enumerate(specialists):
            h = QHBoxLayout()
            h.addWidget(QLabel(spec_name or "—"))
            rec_edit = QLineEdit()
            rec_edit.setReadOnly(True)
            rec_edit.setPlaceholderText("нет")
            rec_edit.setText("нет")
            btn = QPushButton("…")
            btn.setMaximumWidth(36)
            idx = i
            btn.clicked.connect(lambda checked, index=idx: self._on_select_recommendations(index))
            h.addWidget(rec_edit)
            h.addWidget(btn)
            rec_layout.addLayout(h)
            self.rec_edits.append(rec_edit)
            self.rec_buttons.append(btn)
        layout.addWidget(grp)

        for edit in [self.surname_edit, self.name_edit, self.patronymic_edit, self.birth_date_edit,
                     self.pmpk_date_edit, self.pmpk_number_edit, self.order_number_edit, self.order_date_edit]:
            edit.textChanged.connect(self._emit_changed)

    def _emit_changed(self):
        self.data_changed.emit()

    def _on_select_class(self):
        forms = self.db.forms_get_all()
        if not forms:
            QMessageBox.information(self, "Классы", "Сначала добавьте классы в разделе «Таблицы» → «Классы».")
            return
        menu = QMenu(self)
        for r in forms:
            a = menu.addAction(r["number"])
            a.triggered.connect(lambda checked, fid=r["id"], num=r["number"]: self._set_class(fid, num))
        menu.exec_(self.btn_class.mapToGlobal(self.btn_class.rect().bottomLeft()))

    def _set_class(self, form_id: int, number: str):
        self._form_id = form_id
        self.class_edit.setText(number)
        self.data_changed.emit()

    def _on_select_program(self):
        programs = self.db.programs_get_all()
        if not programs:
            QMessageBox.information(self, "Программа", "Сначала добавьте программы в разделе «Таблицы» → «Программы».")
            return
        menu = QMenu(self)
        for r in programs:
            label = f"{r['name']} ({r['version']})"
            a = menu.addAction(label)
            a.triggered.connect(lambda checked, pid=r["id"], name=r["name"], ver=r["version"]: self._set_program(pid, name, ver))
        menu.exec_(self.btn_program.mapToGlobal(self.btn_program.rect().bottomLeft()))

    def _set_program(self, program_id: int, name: str, version: str):
        self._program_id = program_id
        self.program_edit.setText(name)
        self.version_edit.setText(version)
        self.data_changed.emit()

    def _on_select_recommendations(self, index: int):
        specialists = _pad_specialists(self.db.recommendations_get_specialists())
        spec_name = specialists[index] if index < len(specialists) else ""
        if spec_name == "—" or not spec_name:
            QMessageBox.information(self, "Рекомендации", "Для этого слота нет специалиста. Добавьте рекомендации в разделе «Таблицы» → «Рекомендации».")
            return
        current = self.rec_edits[index].text() if self.rec_edits[index].text() else "нет"
        d = RecommendationSelectDialog(spec_name, current, self.db, self)
        if d.exec_() == QDialog.Accepted:
            text = d.selected_as_text()
            self._rec_specs[index] = text
            self.rec_edits[index].setText(text)
            self.data_changed.emit()

    def get_current_row(self) -> dict:
        """Текущие данные формы в виде словаря для db.pupils_insert."""
        return {
            "form_id": self._form_id,
            "surname": self.surname_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "patronymic": self.patronymic_edit.text().strip(),
            "birth_date": self.birth_date_edit.text().strip(),
            "pmpk_date": self.pmpk_date_edit.text().strip(),
            "pmpk_number": self.pmpk_number_edit.text().strip(),
            "program_id": self._program_id,
            "order_number": self.order_number_edit.text().strip(),
            "order_date": self.order_date_edit.text().strip(),
            "rec_spec_1": self._rec_specs[0],
            "rec_spec_2": self._rec_specs[1],
            "rec_spec_3": self._rec_specs[2],
            "rec_spec_4": self._rec_specs[3],
            "rec_spec_5": self._rec_specs[4],
        }

    def clear_form(self):
        self._form_id = None
        self._program_id = None
        self._rec_specs = ["нет"] * 5
        self.class_edit.clear()
        self.surname_edit.clear()
        self.name_edit.clear()
        self.patronymic_edit.clear()
        self.birth_date_edit.clear()
        self.pmpk_date_edit.clear()
        self.pmpk_number_edit.clear()
        self.program_edit.clear()
        self.version_edit.clear()
        self.order_number_edit.clear()
        self.order_date_edit.clear()
        for i, e in enumerate(self.rec_edits):
            e.setText("нет")
            self._rec_specs[i] = "нет"
        self.data_changed.emit()

    def is_valid_for_save(self) -> tuple[bool, str]:
        """Проверка: можно ли сохранить. Возвращает (ok, сообщение об ошибке)."""
        row = self.get_current_row()
        if not row["form_id"]:
            return False, "Выберите класс."
        if not row["surname"]:
            return False, "Укажите фамилию."
        if not row["name"]:
            return False, "Укажите имя."
        return True, ""


class PupilEntryTab(QWidget):
    """Вкладка «Добавить ученика»: форма + временная таблица (одна строка) + кнопка Сохранить."""
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        layout = QVBoxLayout(self)

        self.form = PupilEntryWidget(db, self)
        self.form.data_changed.connect(self._update_temp_table)
        layout.addWidget(self.form)

        layout.addWidget(QLabel("Текущая запись (временная таблица):"))
        self.temp_table = QTableWidget()
        self._temp_headers = [
            "Класс", "Фамилия", "Имя", "Отчество", "Дата рожд.", "ПМПК дата", "ПМПК №",
            "Программа", "Версия", "Приказ №", "Дата приказа", "Рек.1", "Рек.2", "Рек.3", "Рек.4", "Рек.5"
        ]
        self.temp_table.setColumnCount(len(self._temp_headers))
        self.temp_table.setHorizontalHeaderLabels(self._temp_headers)
        self.temp_table.setRowCount(1)
        self.temp_table.setMaximumHeight(80)
        layout.addWidget(self.temp_table)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        self._update_temp_table()

    def _update_temp_table(self):
        """Обновить единственную строку временной таблицы из формы."""
        row = self.form.get_current_row()
        forms = {r["id"]: r["number"] for r in self.db.forms_get_all()}
        programs = {r["id"]: (r["name"], r["version"]) for r in self.db.programs_get_all()}
        form_num = forms.get(row["form_id"], "") if row["form_id"] else ""
        prog = programs.get(row["program_id"], ("", "")) if row["program_id"] else ("", "")
        cells = [
            form_num, row["surname"], row["name"], row["patronymic"], row.get("birth_date", ""),
            row.get("pmpk_date", ""), row.get("pmpk_number", ""), prog[0], prog[1],
            row.get("order_number", ""), row.get("order_date", ""),
            row.get("rec_spec_1", "нет"), row.get("rec_spec_2", "нет"), row.get("rec_spec_3", "нет"),
            row.get("rec_spec_4", "нет"), row.get("rec_spec_5", "нет"),
        ]
        for j, val in enumerate(cells):
            self.temp_table.setItem(0, j, QTableWidgetItem(str(val or "")))

    def _save(self):
        ok, msg = self.form.is_valid_for_save()
        if not ok:
            QMessageBox.warning(self, "Нельзя сохранить", msg)
            return
        row = self.form.get_current_row()
        try:
            self.db.pupils_insert(row)
            QMessageBox.information(self, "Сохранено", "Сведения об ученике внесены в таблицу pupils.")
            self.form.clear_form()
            self._update_temp_table()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
