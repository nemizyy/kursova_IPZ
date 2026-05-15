"""
database.py — Ініціалізація SQLite бази даних та схема таблиць.
"""

import sqlite3
import os
from typing import Optional

# Шлях до файлу бази даних (поряд із цим модулем)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "inventory.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Повертає з'єднання з БД із підтримкою Row-об'єктів."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")  # Включаємо FK-контроль
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """
    Створює таблиці у базі даних, якщо вони ще не існують.
    Викликати один раз при старті програми.
    """
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                name                TEXT    PRIMARY KEY,
                label               TEXT    NOT NULL,
                parent_name         TEXT,
                FOREIGN KEY(parent_name) REFERENCES categories(name) ON DELETE SET NULL
            );

            INSERT OR IGNORE INTO categories (name, label, parent_name) VALUES
                ('furniture', 'Меблі', NULL),
                ('electronics', 'Електроніка', NULL),
                ('vehicle', 'Транспорт', NULL),
                ('equipment', 'Обладнання', NULL),
                ('other', 'Інше', NULL);

            CREATE TABLE IF NOT EXISTS items (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_number    TEXT    NOT NULL UNIQUE,
                name                TEXT    NOT NULL,
                category            TEXT    NOT NULL,
                cost                REAL    NOT NULL CHECK(cost >= 0),
                status              TEXT    NOT NULL DEFAULT 'active'
                                            CHECK(status IN ('active', 'written_off', 'moved')),
                added_at            TEXT    NOT NULL,
                location            TEXT    NOT NULL DEFAULT '',
                description         TEXT    NOT NULL DEFAULT '',
                photo_path          TEXT    NOT NULL DEFAULT '',
                FOREIGN KEY(category) REFERENCES categories(name) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS history (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                item_inventory_number   TEXT    NOT NULL,
                operation               TEXT    NOT NULL,
                details                 TEXT    NOT NULL DEFAULT '',
                performed_at            TEXT    NOT NULL,
                FOREIGN KEY(item_inventory_number) REFERENCES items(inventory_number) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_items_inventory ON items(inventory_number);
            CREATE INDEX IF NOT EXISTS idx_history_inv    ON history(item_inventory_number);
            CREATE INDEX IF NOT EXISTS idx_history_op     ON history(operation);
        """)
    print(f"[DB] База даних ініціалізована: {db_path}")


def drop_all_tables(db_path: str = DB_PATH) -> None:
    """Видаляє всі таблиці (для тестування / скидання стану)."""
    with get_connection(db_path) as conn:
        conn.executescript("""
            DROP TABLE IF EXISTS history;
            DROP TABLE IF EXISTS items;
            DROP TABLE IF EXISTS categories;
        """)
    print("[DB] Всі таблиці видалено.")
