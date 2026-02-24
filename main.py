"""
SvedUch — учёт сведений об учениках школы.
Главное окно: Таблицы, Выборки, Перевод. Настройки (геометрия окна) загружаются
и сохраняются в БД при закрытии (этап 7).
"""
import sys
import logging
import shutil
import sqlite3
from datetime import datetime
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox,
)
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QIcon, QFont

from version import __version__
from app_icon import get_icon_path
from db import Database, DEFAULT_DB_PATH
from table_windows import TablesWindow
from queries_window import QueriesWindow
from transfer_window import TransferWindow
from settings_dialog import SettingsDialog, AboutDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"SvedUch {__version__}")
        
        # Установка иконки приложения
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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
        
        # Применение темы и размера шрифта уже выполнено в main() до создания окна

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

        # Резервная копия и восстановление БД
        btn_backup = QPushButton("Резервная копия БД")
        btn_backup.setToolTip("Сохранить копию базы данных в выбранное место (другой диск, флешка, облако)")
        btn_backup.clicked.connect(self._backup_database)
        layout.addWidget(btn_backup)
        btn_restore = QPushButton("Восстановить из копии")
        btn_restore.setToolTip("Заменить текущую базу выбранной резервной копией (например, после порчи БД)")
        btn_restore.clicked.connect(self._restore_database)
        layout.addWidget(btn_restore)

        layout.addStretch()
        
        # Кнопки настроек и информации
        info_layout = QHBoxLayout()
        btn_settings = QPushButton("Настройки")
        btn_settings.clicked.connect(self._open_settings)
        info_layout.addWidget(btn_settings)
        
        btn_about = QPushButton("О программе")
        btn_about.clicked.connect(self._open_about)
        info_layout.addWidget(btn_about)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)

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
    
    def _open_settings(self):
        """Открывает диалог настроек."""
        from PyQt5.QtWidgets import QDialog
        dialog = SettingsDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            # Перезагружаем тему и шрифт
            apply_app_theme_and_font(self.db)
    
    def _open_about(self):
        """Открывает диалог "О программе"."""
        dialog = AboutDialog(self)
        dialog.exec_()

    def _backup_database(self):
        """Сохраняет резервную копию БД в выбранный пользователем файл."""
        default_name = "SvedUch_backup_%s.db" % datetime.now().strftime("%Y-%m-%d_%H-%M")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Резервная копия базы данных",
            default_name,
            "База SQLite (*.db);;Все файлы (*)",
        )
        if not path:
            return
        try:
            self.db.backup_to(path)
            QMessageBox.information(
                self,
                "Резервная копия",
                "Копия базы данных сохранена:\n%s\n\nРекомендуется хранить копии на другом диске, флешке или в облаке." % path,
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось создать резервную копию:\n%s" % e,
            )

    def _restore_database(self):
        """Восстанавливает БД из выбранной резервной копии; после этого требуется перезапуск приложения."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Восстановить базу из резервной копии",
            "",
            "База SQLite (*.db);;Все файлы (*)",
        )
        if not path:
            return
        db_path = self.db.path
        reply = QMessageBox.question(
            self,
            "Восстановление БД",
            "Текущая база данных будет заменена выбранной копией.\n\n"
            "Путь к текущей БД:\n%s\n\n"
            "Копия:\n%s\n\nПродолжить? После восстановления нужно перезапустить программу."
            % (db_path, path),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.db.close()
            shutil.copy2(path, db_path)
            QMessageBox.information(
                self,
                "Восстановлено",
                "База данных восстановлена из выбранной копии.\nПерезапустите приложение.",
            )
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Не удалось восстановить базу:\n%s" % e,
            )
            # Пытаемся снова подключиться к текущей БД
            try:
                self.db = Database(DEFAULT_DB_PATH)
                self.db.create_tables()
            except Exception:
                pass

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


def apply_app_theme_and_font(db: Database):
    """Применяет тему и размер шрифта ко всему приложению."""
    app = QApplication.instance()
    
    # Применение темы
    theme = db.settings_get("theme") or "Светлая"
    if theme == "Тёмная":
        # Темная тема через QStyleSheet
        dark_stylesheet = """
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox, QLineEdit, QSpinBox, QPlainTextEdit, QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 3px;
            }
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #555555;
            }
            QTableWidget::item {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555555;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 5px 15px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #0066cc;
            }
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """
        app.setStyleSheet(dark_stylesheet)
    else:
        # Светлая тема (сброс стилей)
        app.setStyleSheet("")
    
    # Применение размера шрифта
    font_size_str = db.settings_get("font_size")
    if font_size_str:
        try:
            font_size = int(font_size_str)
            if 8 <= font_size <= 24:
                font = QFont()
                font.setPointSize(font_size)
                app.setFont(font)
        except ValueError:
            pass


def _try_restore_on_corrupt(app: QApplication) -> bool:
    """
    Если БД повреждена при запуске — предлагает выбрать резервную копию и восстановить.
    Возвращает True, если восстановление выполнено (можно повторить запуск), False — отмена.
    """
    path, _ = QFileDialog.getOpenFileName(
        None,
        "База данных повреждена — выберите резервную копию для восстановления",
        "",
        "База SQLite (*.db);;Все файлы (*)",
    )
    if not path:
        return False
    try:
        shutil.copy2(path, DEFAULT_DB_PATH)
        QMessageBox.information(
            None,
            "Восстановлено",
            "База данных восстановлена из выбранной копии.\nПерезапустите приложение.",
        )
        return True
    except Exception as e:
        QMessageBox.critical(
            None,
            "Ошибка",
            "Не удалось восстановить базу:\n%s" % e,
        )
        return False


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info("SvedUch %s", __version__)

    app = QApplication(sys.argv)

    # Установка иконки приложения глобально
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Подключение к БД для загрузки настроек темы и шрифта
    temp_db = Database(DEFAULT_DB_PATH)
    try:
        temp_db.create_tables()
        apply_app_theme_and_font(temp_db)
    except (sqlite3.Error, OSError) as e:
        temp_db.close()
        QMessageBox.warning(
            None,
            "Ошибка базы данных",
            "Не удалось открыть базу данных (возможно, файл повреждён):\n%s\n\n"
            "Выберите резервную копию (.db) для восстановления." % e,
        )
        if _try_restore_on_corrupt(app):
            # Перезапуск: выходим с кодом 0, чтобы лаунчер/пользователь мог перезапустить
            sys.exit(0)
        sys.exit(1)
    finally:
        try:
            temp_db.close()
        except Exception:
            pass

    try:
        window = MainWindow()
    except (sqlite3.Error, OSError) as e:
        QMessageBox.warning(
            None,
            "Ошибка базы данных",
            "Не удалось открыть базу данных:\n%s\n\n"
            "Выберите резервную копию (.db) для восстановления." % e,
        )
        if _try_restore_on_corrupt(app):
            sys.exit(0)
        sys.exit(1)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
