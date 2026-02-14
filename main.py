"""
SvedUch — учёт сведений об учениках школы.
Главное окно: Таблицы, Выборки, Перевод. Настройки (геометрия окна) загружаются
и сохраняются в БД при закрытии (этап 7).
"""
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
)
from PyQt5.QtCore import QByteArray, Qt

from db import Database, DEFAULT_DB_PATH
from table_windows import TablesWindow
from queries_window import QueriesWindow
from transfer_window import TransferWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SvedUch")

        # Подключение к БД: по умолчанию в каталоге приложения
        self.db = Database(DEFAULT_DB_PATH)
        try:
            self.db.create_tables()
        except Exception:
            self.db.close()
            raise

        # Восстановление геометрии и состояния окна из настроек
        geom = self.db.settings_get("window_geometry")
        state = self.db.settings_get("window_state")
        try:
            if geom:
                self.restoreGeometry(QByteArray.fromBase64(geom.encode("utf-8")))
            else:
                self.setGeometry(100, 100, 400, 300)
            if state:
                self.restoreState(QByteArray.fromBase64(state.encode("utf-8")))
        except Exception:
            self.setGeometry(100, 100, 400, 300)

        # Тема (опционально)
        style = self.db.settings_get("style")
        if style and style in ("Fusion", "Windows", "WindowsVista", "macOS"):
            QApplication.setStyle(style)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel("Выберите раздел:"))
        btn_row = QHBoxLayout()
        btn_tables = QPushButton("Таблицы")
        btn_tables.clicked.connect(self._open_tables)
        btn_row.addWidget(btn_tables)
        btn_queries = QPushButton("Выборки")
        btn_queries.clicked.connect(self._open_queries)
        btn_row.addWidget(btn_queries)
        btn_transfer = QPushButton("Перевод")
        btn_transfer.clicked.connect(self._open_transfer)
        btn_row.addWidget(btn_transfer)
        layout.addLayout(btn_row)

        layout.addStretch()

        btn_exit = QPushButton("Выход")
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

        self._tables_window = None
        self._queries_window = None
        self._transfer_window = None

    def _open_tables(self):
        if self._tables_window is None or not self._tables_window.isVisible():
            self._tables_window = TablesWindow(self.db, self)
            self._tables_window.setWindowFlags(self._tables_window.windowFlags() | Qt.Window)
        self._tables_window.show()
        self._tables_window.raise_()
        self._tables_window.activateWindow()

    def _open_queries(self):
        if self._queries_window is None or not self._queries_window.isVisible():
            self._queries_window = QueriesWindow(self.db, self)
            self._queries_window.setWindowFlags(self._queries_window.windowFlags() | Qt.Window)
        self._queries_window.show()
        self._queries_window.raise_()
        self._queries_window.activateWindow()

    def _open_transfer(self):
        if self._transfer_window is None or not self._transfer_window.isVisible():
            self._transfer_window = TransferWindow(self.db, self)
            self._transfer_window.setWindowFlags(self._transfer_window.windowFlags() | Qt.Window)
        self._transfer_window.show()
        self._transfer_window.raise_()
        self._transfer_window.activateWindow()

    def closeEvent(self, event):
        try:
            geom = self.saveGeometry().toBase64().data().decode("utf-8")
            state = self.saveState().toBase64().data().decode("utf-8")
            self.db.settings_set("window_geometry", geom)
            self.db.settings_set("window_state", state)
        except Exception:
            pass
        self.db.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
