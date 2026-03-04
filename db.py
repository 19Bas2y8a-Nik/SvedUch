"""
Модуль доступа к базе данных SvedUch (SQLite).
Инкапсулирует все операции с БД. Схема — см. DATABASE.md.
"""
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional


def _default_db_dir() -> Path:
    """Каталог для БД по умолчанию: рядом с exe при установке, иначе рядом с db.py."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


# Путь к БД по умолчанию (рядом с exe при установке, иначе рядом с проектом)
DEFAULT_DB_PATH = _default_db_dir() / "sveduch.db"


class Database:
    def __init__(self, db_path: Optional[str | Path] = None):
        self._path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def path(self) -> Path:
        """Путь к файлу БД (для восстановления из копии)."""
        return self._path

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._path)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def backup_to(self, dest_path: str | Path) -> None:
        """
        Создаёт резервную копию БД в указанный файл (согласованная копия без закрытия соединения).
        Сохраняйте копии на другой диск или в облако для защиты от порчи.
        """
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_conn()
        dest_conn = sqlite3.connect(dest)
        try:
            conn.backup(dest_conn)
            dest_conn.commit()
        finally:
            dest_conn.close()

    def create_tables(self) -> None:
        """Создаёт все таблицы при первом запуске."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                specialist_name TEXT NOT NULL,
                recommendation_name TEXT NOT NULL,
                UNIQUE(specialist_name, recommendation_name)
            );
            CREATE INDEX IF NOT EXISTS idx_recommendations_specialist
                ON recommendations(specialist_name);

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS pupils (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL REFERENCES forms(id),
                surname TEXT NOT NULL,
                name TEXT NOT NULL,
                patronymic TEXT,
                birth_date TEXT,
                address TEXT,
                gender TEXT,
                pmpk_date TEXT,
                pmpk_number TEXT,
                program_id INTEGER REFERENCES programs(id),
                order_number TEXT,
                order_date TEXT,
                rec_spec_1 TEXT,
                rec_spec_2 TEXT,
                rec_spec_3 TEXT,
                rec_spec_4 TEXT,
                rec_spec_5 TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_pupils_form ON pupils(form_id);
            CREATE INDEX IF NOT EXISTS idx_pupils_program ON pupils(program_id);

            CREATE TABLE IF NOT EXISTS pupils_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_id INTEGER NOT NULL,
                surname TEXT NOT NULL,
                name TEXT NOT NULL,
                patronymic TEXT,
                birth_date TEXT,
                address TEXT,
                gender TEXT,
                pmpk_date TEXT,
                pmpk_number TEXT,
                program_id INTEGER,
                order_number TEXT,
                order_date TEXT,
                rec_spec_1 TEXT,
                rec_spec_2 TEXT,
                rec_spec_3 TEXT,
                rec_spec_4 TEXT,
                rec_spec_5 TEXT,
                transfer_date TEXT NOT NULL,
                transfer_reason TEXT
            );

            CREATE TABLE IF NOT EXISTS experts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS criterions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL,
                UNIQUE(name, code)
            );

            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_number TEXT NOT NULL,
                surname TEXT NOT NULL,
                name TEXT NOT NULL,
                patronymic TEXT,
                specialist TEXT NOT NULL,
                criterion TEXT NOT NULL
                -- Поля результатов за периоды добавляются динамически (ALTER TABLE)
            );
        """)
        conn.commit()
        self._migrate_pupils_address_gender()

    def _migrate_pupils_address_gender(self) -> None:
        """Добавить поля address и gender в pupils и pupils_history, если их ещё нет (миграция)."""
        conn = self._get_conn()
        for table in ("pupils", "pupils_history"):
            info = conn.execute(f"PRAGMA table_info({table})").fetchall()
            names = [row[1] for row in info]
            if "address" not in names:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN address TEXT")
            if "gender" not in names:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN gender TEXT")
        conn.commit()

    # --- experts ---
    def experts_get_all(self) -> list[sqlite3.Row]:
        """Список всех специалистов (experts)."""
        return self._get_conn().execute(
            "SELECT id, name FROM experts ORDER BY name"
        ).fetchall()

    def experts_add(self, name: str) -> int:
        """Добавить специалиста. Возвращает id."""
        cur = self._get_conn().execute(
            "INSERT INTO experts (name) VALUES (?)",
            (name.strip(),),
        )
        self._get_conn().commit()
        return cur.lastrowid

    def experts_update(self, id: int, name: str) -> None:
        """Обновить имя специалиста."""
        self._get_conn().execute(
            "UPDATE experts SET name = ? WHERE id = ?",
            (name.strip(), id),
        )
        self._get_conn().commit()

    def experts_delete(self, id: int) -> None:
        """Удалить специалиста."""
        self._get_conn().execute("DELETE FROM experts WHERE id = ?", (id,))
        self._get_conn().commit()

    # --- criterions ---
    def criterions_get_all(self) -> list[sqlite3.Row]:
        """Список всех критериев (criterions)."""
        return self._get_conn().execute(
            "SELECT id, name FROM criterions ORDER BY name"
        ).fetchall()

    def criterions_add(self, name: str) -> int:
        """Добавить критерий. Возвращает id."""
        cur = self._get_conn().execute(
            "INSERT INTO criterions (name) VALUES (?)",
            (name.strip(),),
        )
        self._get_conn().commit()
        return cur.lastrowid

    def criterions_update(self, id: int, name: str) -> None:
        """Обновить критерий."""
        self._get_conn().execute(
            "UPDATE criterions SET name = ? WHERE id = ?",
            (name.strip(), id),
        )
        self._get_conn().commit()

    def criterions_delete(self, id: int) -> None:
        """Удалить критерий."""
        self._get_conn().execute("DELETE FROM criterions WHERE id = ?", (id,))
        self._get_conn().commit()

    # --- standards ---
    def standards_get_all(self) -> list[sqlite3.Row]:
        """Список всех уровней (standards)."""
        return self._get_conn().execute(
            "SELECT id, name, code FROM standards ORDER BY name, code"
        ).fetchall()

    def standards_add(self, name: str, code: str) -> int:
        """Добавить уровень. Возвращает id."""
        cur = self._get_conn().execute(
            "INSERT INTO standards (name, code) VALUES (?, ?)",
            (name.strip(), code.strip()),
        )
        self._get_conn().commit()
        return cur.lastrowid

    def standards_update(self, id: int, name: str, code: str) -> None:
        """Обновить уровень."""
        self._get_conn().execute(
            "UPDATE standards SET name = ?, code = ? WHERE id = ?",
            (name.strip(), code.strip(), id),
        )
        self._get_conn().commit()

    def standards_delete(self, id: int) -> None:
        """Удалить уровень."""
        self._get_conn().execute("DELETE FROM standards WHERE id = ?", (id,))
        self._get_conn().commit()

    # --- forms ---
    def forms_get_all(self) -> list[sqlite3.Row]:
        """Список всех классов."""
        return self._get_conn().execute(
            "SELECT id, number FROM forms ORDER BY number"
        ).fetchall()

    def forms_add(self, number: str) -> int:
        """Добавить класс. Возвращает id."""
        cur = self._get_conn().execute(
            "INSERT INTO forms (number) VALUES (?)", (number.strip(),)
        )
        self._get_conn().commit()
        return cur.lastrowid

    def forms_update(self, id: int, number: str) -> None:
        """Обновить номер класса."""
        self._get_conn().execute(
            "UPDATE forms SET number = ? WHERE id = ?", (number.strip(), id)
        )
        self._get_conn().commit()

    def forms_delete(self, id: int) -> None:
        """Удалить класс."""
        self._get_conn().execute("DELETE FROM forms WHERE id = ?", (id,))
        self._get_conn().commit()

    def forms_get_or_create_id(self, number: str) -> int:
        """Получить id класса по номеру; если такого нет — создать и вернуть id."""
        number = number.strip()
        if not number:
            raise ValueError("Номер класса не указан.")
        row = self._get_conn().execute(
            "SELECT id FROM forms WHERE number = ?", (number,)
        ).fetchone()
        if row is not None:
            return row["id"]
        return self.forms_add(number)

    # --- programs ---
    def programs_get_all(self) -> list[sqlite3.Row]:
        """Список всех программ."""
        return self._get_conn().execute(
            "SELECT id, name, version FROM programs ORDER BY name, version"
        ).fetchall()

    def programs_add(self, name: str, version: str) -> int:
        """Добавить программу. Возвращает id."""
        cur = self._get_conn().execute(
            "INSERT INTO programs (name, version) VALUES (?, ?)",
            (name.strip(), version.strip()),
        )
        self._get_conn().commit()
        return cur.lastrowid

    def programs_update(self, id: int, name: str, version: str) -> None:
        """Обновить программу."""
        self._get_conn().execute(
            "UPDATE programs SET name = ?, version = ? WHERE id = ?",
            (name.strip(), version.strip(), id),
        )
        self._get_conn().commit()

    def programs_delete(self, id: int) -> None:
        """Удалить программу."""
        self._get_conn().execute("DELETE FROM programs WHERE id = ?", (id,))
        self._get_conn().commit()

    # --- recommendations ---
    def recommendations_get_all(self) -> list[sqlite3.Row]:
        """Список всех рекомендаций."""
        return self._get_conn().execute(
            "SELECT id, specialist_name, recommendation_name FROM recommendations ORDER BY specialist_name, recommendation_name"
        ).fetchall()

    def recommendations_get_by_specialist(self, specialist_name: str) -> list[sqlite3.Row]:
        """Рекомендации по имени специалиста."""
        return self._get_conn().execute(
            "SELECT id, specialist_name, recommendation_name FROM recommendations WHERE specialist_name = ? ORDER BY recommendation_name",
            (specialist_name,),
        ).fetchall()

    def recommendations_get_specialists(self) -> list[str]:
        """Уникальные имена специалистов (порядок по первому появлению, до 5)."""
        rows = self._get_conn().execute(
            "SELECT DISTINCT specialist_name FROM recommendations ORDER BY id"
        ).fetchall()
        return [r["specialist_name"] for r in rows][:5]

    def recommendations_add(self, specialist_name: str, recommendation_name: str) -> int:
        """Добавить рекомендацию. Возвращает id. Игнорирует дубликат пары (специалист, рекомендация)."""
        conn = self._get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO recommendations (specialist_name, recommendation_name) VALUES (?, ?)",
                (specialist_name.strip(), recommendation_name.strip()),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            conn.rollback()
            row = conn.execute(
                "SELECT id FROM recommendations WHERE specialist_name = ? AND recommendation_name = ?",
                (specialist_name.strip(), recommendation_name.strip()),
            ).fetchone()
            return row["id"] if row else 0

    def recommendations_update(self, id: int, specialist_name: str, recommendation_name: str) -> None:
        """Изменить рекомендацию по id."""
        self._get_conn().execute(
            "UPDATE recommendations SET specialist_name = ?, recommendation_name = ? WHERE id = ?",
            (specialist_name.strip(), recommendation_name.strip(), id),
        )
        self._get_conn().commit()

    def recommendations_delete(self, id: int) -> None:
        """Удалить рекомендацию."""
        self._get_conn().execute("DELETE FROM recommendations WHERE id = ?", (id,))
        self._get_conn().commit()

    # --- pupils ---
    def pupils_insert(self, row: dict[str, Any]) -> int:
        """Вставить ученика. row: form_id, surname, name, patronymic, birth_date, address, gender, pmpk_date, pmpk_number, program_id, order_number, order_date, rec_spec_1..5. Возвращает id."""
        conn = self._get_conn()
        cur = conn.execute(
            """INSERT INTO pupils (
                form_id, surname, name, patronymic, birth_date, address, gender,
                pmpk_date, pmpk_number, program_id, order_number, order_date,
                rec_spec_1, rec_spec_2, rec_spec_3, rec_spec_4, rec_spec_5
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["form_id"],
                row["surname"],
                row["name"],
                row.get("patronymic") or "",
                row.get("birth_date") or "",
                row.get("address") or "",
                row.get("gender") or "",
                row.get("pmpk_date") or "",
                row.get("pmpk_number") or "",
                row.get("program_id"),
                row.get("order_number") or "",
                row.get("order_date") or "",
                row.get("rec_spec_1") or "нет",
                row.get("rec_spec_2") or "нет",
                row.get("rec_spec_3") or "нет",
                row.get("rec_spec_4") or "нет",
                row.get("rec_spec_5") or "нет",
            ),
        )
        conn.commit()
        return cur.lastrowid

    def pupils_update(self, id: int, row: dict[str, Any]) -> None:
        """Обновить ученика по id."""
        conn = self._get_conn()
        conn.execute(
            """UPDATE pupils SET
                form_id = ?, surname = ?, name = ?, patronymic = ?, birth_date = ?, address = ?, gender = ?,
                pmpk_date = ?, pmpk_number = ?, program_id = ?, order_number = ?, order_date = ?,
                rec_spec_1 = ?, rec_spec_2 = ?, rec_spec_3 = ?, rec_spec_4 = ?, rec_spec_5 = ?
            WHERE id = ?""",
            (
                row["form_id"],
                row["surname"],
                row["name"],
                row.get("patronymic") or "",
                row.get("birth_date") or "",
                row.get("address") or "",
                row.get("gender") or "",
                row.get("pmpk_date") or "",
                row.get("pmpk_number") or "",
                row.get("program_id"),
                row.get("order_number") or "",
                row.get("order_date") or "",
                row.get("rec_spec_1") or "нет",
                row.get("rec_spec_2") or "нет",
                row.get("rec_spec_3") or "нет",
                row.get("rec_spec_4") or "нет",
                row.get("rec_spec_5") or "нет",
                id,
            ),
        )
        conn.commit()

    def pupils_get_by_id(self, id: int) -> Optional[sqlite3.Row]:
        """Получить ученика по id."""
        return self._get_conn().execute(
            "SELECT * FROM pupils WHERE id = ?", (id,)
        ).fetchone()

    def pupils_get_by_form_id(self, form_id: int) -> list[sqlite3.Row]:
        """Список учеников класса."""
        return self._get_conn().execute(
            "SELECT * FROM pupils WHERE form_id = ? ORDER BY surname, name", (form_id,)
        ).fetchall()

    def pupils_get_by_program_id(self, program_id: int) -> list[sqlite3.Row]:
        """Список учеников по программе."""
        return self._get_conn().execute(
            "SELECT * FROM pupils WHERE program_id = ? ORDER BY form_id, surname, name",
            (program_id,),
        ).fetchall()

    def pupils_get_all(self) -> list[sqlite3.Row]:
        """Все ученики."""
        return self._get_conn().execute(
            "SELECT * FROM pupils ORDER BY form_id, surname, name"
        ).fetchall()

    def pupils_count_by_program(self) -> list[sqlite3.Row]:
        """Агрегация: программа (id, name, version) и количество учеников."""
        return self._get_conn().execute(
            """SELECT p.id AS program_id, p.name AS program_name, p.version AS program_version,
                      COUNT(pup.id) AS pupils_count
               FROM programs p
               LEFT JOIN pupils pup ON pup.program_id = p.id
               GROUP BY p.id
               ORDER BY p.name, p.version"""
        ).fetchall()

    def pupils_delete(self, id: int) -> None:
        """Удалить ученика (например, перед переносом в архив)."""
        self._get_conn().execute("DELETE FROM pupils WHERE id = ?", (id,))
        self._get_conn().commit()

    # --- pupils_history ---
    def pupils_history_insert(self, row: dict[str, Any], transfer_date: str, transfer_reason: str) -> int:
        """Вставить запись в архив. row — те же поля, что у pupils; добавляются transfer_date, transfer_reason. Возвращает id."""
        conn = self._get_conn()
        cur = conn.execute(
            """INSERT INTO pupils_history (
                form_id, surname, name, patronymic, birth_date, address, gender,
                pmpk_date, pmpk_number, program_id, order_number, order_date,
                rec_spec_1, rec_spec_2, rec_spec_3, rec_spec_4, rec_spec_5,
                transfer_date, transfer_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["form_id"],
                row["surname"],
                row["name"],
                row.get("patronymic") or "",
                row.get("birth_date") or "",
                row.get("address") or "",
                row.get("gender") or "",
                row.get("pmpk_date") or "",
                row.get("pmpk_number") or "",
                row.get("program_id"),
                row.get("order_number") or "",
                row.get("order_date") or "",
                row.get("rec_spec_1") or "нет",
                row.get("rec_spec_2") or "нет",
                row.get("rec_spec_3") or "нет",
                row.get("rec_spec_4") or "нет",
                row.get("rec_spec_5") or "нет",
                transfer_date,
                transfer_reason or "",
            ),
        )
        conn.commit()
        return cur.lastrowid

    def pupils_history_get_all(self) -> list[sqlite3.Row]:
        """Все записи архива."""
        return self._get_conn().execute(
            "SELECT * FROM pupils_history ORDER BY transfer_date DESC, surname, name"
        ).fetchall()

    # --- settings ---
    def settings_get(self, key: str) -> Optional[str]:
        """Значение настройки по ключу."""
        row = self._get_conn().execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def settings_set(self, key: str, value: str) -> None:
        """Записать настройку (ключ — значение)."""
        self._get_conn().execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._get_conn().commit()

    def settings_get_all(self) -> list[sqlite3.Row]:
        """Все настройки (ключ, значение)."""
        return self._get_conn().execute(
            "SELECT key, value FROM settings ORDER BY key"
        ).fetchall()

    # --- analysis (динамические поля результатов) ---
    def analysis_ensure_result_column(self, school_year: str, period: str) -> str:
        """
        Гарантирует наличие колонки результата для заданного учебного года и периода.
        Возвращает имя колонки (для дальнейших INSERT/UPDATE).
        """
        school_year = (school_year or "").strip()
        period = (period or "").strip()
        if not school_year or not period:
            raise ValueError("Учебный год и период должны быть заполнены.")

        # Нормализация периода: "I полугодие" / "II полугодие" → "I" / "II"
        period_key = period
        if period.startswith("I"):
            period_key = "I"
        elif period.startswith("II"):
            period_key = "II"

        # Формируем безопасное имя колонки
        base = f"result_{period_key}_{school_year.replace('-', '_')}"
        column_name = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in base)

        conn = self._get_conn()
        info = conn.execute("PRAGMA table_info(analysis)").fetchall()
        names = [row[1] for row in info]
        if column_name not in names:
            conn.execute(f"ALTER TABLE analysis ADD COLUMN {column_name} TEXT")
            conn.commit()
        return column_name

    def analysis_insert_row(
        self,
        class_number: str,
        surname: str,
        name: str,
        patronymic: str,
        specialist: str,
        criterion: str,
        result_column: str,
        result_value: str,
    ) -> int:
        """
        Вставляет одну запись в таблицу analysis с указанным столбцом результата.
        result_column должен быть получен из analysis_ensure_result_column.
        """
        conn = self._get_conn()
        sql = (
            f"INSERT INTO analysis (class_number, surname, name, patronymic, specialist, criterion, {result_column}) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        cur = conn.execute(
            sql,
            (
                class_number.strip(),
                surname.strip(),
                name.strip(),
                (patronymic or "").strip(),
                specialist.strip(),
                criterion.strip(),
                (result_value or "").strip(),
            ),
        )
        conn.commit()
        return cur.lastrowid

    def analysis_get_results_for_pupil(
        self,
        class_number: str,
        surname: str,
        name: str,
        patronymic: str,
        specialist: str,
    ) -> tuple[list[str], list[sqlite3.Row]]:
        """
        Возвращает (список имён колонок результатов, строки) для указанного ученика и специалиста.
        Колонки результатов — все поля таблицы analysis, начинающиеся с 'result_'.
        """
        conn = self._get_conn()
        info = conn.execute("PRAGMA table_info(analysis)").fetchall()
        result_cols = [row[1] for row in info if isinstance(row[1], str) and row[1].startswith("result_")]
        if not result_cols:
            return [], []

        # Строим SELECT с динамическими колонками
        cols_sql = ", ".join(result_cols)
        sql = (
            f"SELECT criterion, {cols_sql} FROM analysis "
            "WHERE class_number = ? AND surname = ? AND name = ? AND patronymic = ? AND specialist = ? "
            "ORDER BY criterion"
        )
        rows = conn.execute(
            sql,
            (
                (class_number or "").strip(),
                (surname or "").strip(),
                (name or "").strip(),
                (patronymic or "").strip(),
                (specialist or "").strip(),
            ),
        ).fetchall()
        return result_cols, rows
