"""
Тестовая программа для просмотра и редактирования SQLite базы данных.
Отображает список таблиц, позволяет открыть таблицу с пагинацией и выполнять CRUD операции.
"""
import sys
import sqlite3
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QListWidget, QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt


class DatabaseViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Просмотр SQLite базы данных")
        self.setGeometry(100, 100, 1000, 700)
        self.db_path = None
        self.conn = None
        self.current_table = None
        self.current_page = 0
        self.page_size = 50

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Выбор файла БД
        file_layout = QHBoxLayout()
        self.file_label = QLabel("База данных не выбрана")
        file_layout.addWidget(self.file_label)
        btn_open_db = QPushButton("Выбрать файл БД")
        btn_open_db.clicked.connect(self._open_database)
        file_layout.addWidget(btn_open_db)
        layout.addLayout(file_layout)

        # Список таблиц
        layout.addWidget(QLabel("Таблицы:"))
        self.tables_list = QListWidget()
        self.tables_list.itemDoubleClicked.connect(self._open_table)
        layout.addWidget(self.tables_list)

        btn_open = QPushButton("Открыть")
        btn_open.clicked.connect(self._open_table_from_button)
        layout.addWidget(btn_open)

        # Таблица данных
        layout.addWidget(QLabel("Данные таблицы:"))
        self.data_table = QTableWidget()
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.data_table)

        # Пагинация и CRUD
        controls_layout = QHBoxLayout()
        self.page_label = QLabel("Страница: 0")
        controls_layout.addWidget(self.page_label)
        btn_prev = QPushButton("◄ Предыдущая")
        btn_prev.clicked.connect(self._prev_page)
        controls_layout.addWidget(btn_prev)
        btn_next = QPushButton("Следующая ►")
        btn_next.clicked.connect(self._next_page)
        controls_layout.addWidget(btn_next)
        controls_layout.addStretch()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add_row)
        controls_layout.addWidget(btn_add)
        btn_edit = QPushButton("Изменить")
        btn_edit.clicked.connect(self._edit_row)
        controls_layout.addWidget(btn_edit)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete_row)
        controls_layout.addWidget(btn_delete)
        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self._refresh_table)
        controls_layout.addWidget(btn_refresh)
        layout.addLayout(controls_layout)

    def _open_database(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл SQLite", "", "SQLite (*.db *.sqlite *.sqlite3);;Все файлы (*)"
        )
        if not path:
            return
        self.db_path = path
        self.file_label.setText(f"БД: {Path(path).name}")
        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            self._load_tables()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть БД:\n{e}")

    def _load_tables(self):
        if not self.conn:
            return
        self.tables_list.clear()
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        for row in cursor:
            self.tables_list.addItem(row[0])

    def _open_table_from_button(self):
        item = self.tables_list.currentItem()
        if not item:
            QMessageBox.information(self, "Выбор", "Выберите таблицу из списка.")
            return
        self._open_table(item)

    def _open_table(self, item):
        if not item:
            return
        table_name = item.text()
        self.current_table = table_name
        self.current_page = 0
        self._refresh_table()

    def _refresh_table(self):
        if not self.conn or not self.current_table:
            return
        try:
            cursor = self.conn.execute(f"SELECT * FROM {self.current_table}")
            columns = [desc[0] for desc in cursor.description]
            all_rows = cursor.fetchall()
            total_rows = len(all_rows)
            start = self.current_page * self.page_size
            end = start + self.page_size
            page_rows = all_rows[start:end]

            self.data_table.setColumnCount(len(columns))
            self.data_table.setHorizontalHeaderLabels(columns)
            self.data_table.setRowCount(len(page_rows))
            for i, row in enumerate(page_rows):
                for j, col in enumerate(columns):
                    val = row[col] if col in row.keys() else ""
                    self.data_table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

            self.page_label.setText(
                f"Страница: {self.current_page + 1} "
                f"(строки {start + 1}-{min(end, total_rows)} из {total_rows})"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить таблицу:\n{e}")

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_table()

    def _next_page(self):
        if not self.conn or not self.current_table:
            return
        cursor = self.conn.execute(f"SELECT COUNT(*) FROM {self.current_table}")
        total = cursor.fetchone()[0]
        if (self.current_page + 1) * self.page_size < total:
            self.current_page += 1
            self._refresh_table()

    def _add_row(self):
        if not self.conn or not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте таблицу.")
            return
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({self.current_table})")
            columns = [(row[1], row[2], row[3], row[5]) for row in cursor]
            d = EditRowDialog(columns, None, self)
            if d.exec_() == QDialog.Accepted:
                values = d.get_values()
                col_names = [col[0] for col in columns if col[0] not in values or values[col[0]]]
                vals = [values.get(col[0], None) for col in columns if col[0] in col_names]
                placeholders = ", ".join(["?" for _ in col_names])
                self.conn.execute(
                    f"INSERT INTO {self.current_table} ({', '.join(col_names)}) VALUES ({placeholders})",
                    vals
                )
                self.conn.commit()
                self._refresh_table()
                QMessageBox.information(self, "Успех", "Запись добавлена.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись:\n{e}")

    def _edit_row(self):
        if not self.conn or not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте таблицу.")
            return
        row_idx = self.data_table.currentRow()
        if row_idx < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для редактирования.")
            return
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({self.current_table})")
            columns = [(row[1], row[2], row[3], row[5]) for row in cursor]
            pk_col = next((col[0] for col in columns if col[3]), None)
            if not pk_col:
                QMessageBox.warning(self, "Ошибка", "Таблица не имеет первичного ключа.")
                return
            pk_val = self.data_table.item(row_idx, 0).text()
            cursor = self.conn.execute(f"SELECT * FROM {self.current_table} WHERE {pk_col} = ?", (pk_val,))
            row_data = cursor.fetchone()
            if not row_data:
                QMessageBox.warning(self, "Ошибка", "Запись не найдена.")
                return
            d = EditRowDialog(columns, row_data, self)
            if d.exec_() == QDialog.Accepted:
                values = d.get_values()
                col_names = [col[0] for col in columns if col[0] != pk_col]
                vals = [values.get(col[0]) for col in columns if col[0] in col_names]
                vals.append(pk_val)
                updates = ", ".join([f"{col} = ?" for col in col_names])
                self.conn.execute(
                    f"UPDATE {self.current_table} SET {updates} WHERE {pk_col} = ?",
                    vals
                )
                self.conn.commit()
                self._refresh_table()
                QMessageBox.information(self, "Успех", "Запись обновлена.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить запись:\n{e}")

    def _delete_row(self):
        if not self.conn or not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Сначала откройте таблицу.")
            return
        row_idx = self.data_table.currentRow()
        if row_idx < 0:
            QMessageBox.information(self, "Выбор", "Выберите строку для удаления.")
            return
        if QMessageBox.question(
            self, "Подтверждение", "Удалить выбранную запись?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({self.current_table})")
            columns = [(row[1], row[2], row[3], row[5]) for row in cursor]
            pk_col = next((col[0] for col in columns if col[3]), None)
            if not pk_col:
                QMessageBox.warning(self, "Ошибка", "Таблица не имеет первичного ключа.")
                return
            pk_val = self.data_table.item(row_idx, 0).text()
            self.conn.execute(f"DELETE FROM {self.current_table} WHERE {pk_col} = ?", (pk_val,))
            self.conn.commit()
            self._refresh_table()
            QMessageBox.information(self, "Успех", "Запись удалена.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись:\n{e}")

    def closeEvent(self, event):
        if self.conn:
            self.conn.close()
        event.accept()


class EditRowDialog(QDialog):
    def __init__(self, columns, row_data, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.row_data = row_data
        self.edits = {}
        self.setWindowTitle("Редактирование записи" if row_data else "Новая запись")
        layout = QFormLayout(self)
        for col_name, col_type, not_null, is_pk in columns:
            edit = QLineEdit()
            if row_data:
                val = row_data[col_name] if col_name in row_data.keys() else ""
                edit.setText(str(val) if val is not None else "")
            if is_pk:
                edit.setReadOnly(True)
                edit.setStyleSheet("background-color: #f0f0f0;")
            layout.addRow(f"{col_name} ({col_type}){' [PK]' if is_pk else ''}:", edit)
            self.edits[col_name] = edit
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addRow(bb)

    def get_values(self):
        return {col[0]: self.edits[col[0]].text().strip() or None for col in self.columns}


def main():
    app = QApplication(sys.argv)
    window = DatabaseViewer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
