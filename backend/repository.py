"""
repository.py — Рівень доступу до даних (Data Access Layer).
Всі прямі SQL-запити зосереджені тут.
"""

import sqlite3
from typing import List, Optional

from .database import get_connection, DB_PATH
from .models import Item, HistoryRecord


# ─────────────────────────── ITEMS ───────────────────────────

class ItemRepository:
    """CRUD-операції для таблиці items."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    # ── Запис ──────────────────────────────────────────────────

    def add(self, item: Item) -> Item:
        """Додає новий запис. Повертає item із заповненим id."""
        sql = """
            INSERT INTO items
                (inventory_number, name, category, cost, status, added_at, location, description, photo_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._conn() as conn:
            cursor = conn.execute(sql, (
                item.inventory_number, item.name, item.category,
                item.cost, item.status, item.added_at,
                item.location, item.description, item.photo_path,
            ))
            item.id = cursor.lastrowid
        return item

    def update(self, item: Item) -> None:
        """Оновлює існуючий запис за inventory_number."""
        sql = """
            UPDATE items
            SET name=?, category=?, cost=?, status=?, location=?, description=?, photo_path=?
            WHERE inventory_number=?
        """
        with self._conn() as conn:
            conn.execute(sql, (
                item.name, item.category, item.cost,
                item.status, item.location, item.description, item.photo_path,
                item.inventory_number,
            ))

    def delete(self, inventory_number: str) -> None:
        """Видаляє запис за інвентарним номером."""
        try:
            with self._conn() as conn:
                conn.execute("DELETE FROM items WHERE inventory_number=?", (inventory_number,))
        except sqlite3.IntegrityError:
            raise ValueError(
                f"Неможливо видалити майно «{inventory_number}», оскільки існують пов'язані записи в історії (Обмеження зовнішнього ключа)."
            )

    # ── Читання ────────────────────────────────────────────────

    def get_by_inventory(self, inventory_number: str) -> Optional[Item]:
        """Повертає одиницю майна за інвентарним номером або None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM items WHERE inventory_number=?", (inventory_number,)
            ).fetchone()
        return Item.from_dict(dict(row)) if row else None

    def get_all(self) -> List[Item]:
        """Повертає всі записи."""
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM items ORDER BY added_at DESC").fetchall()
        return [Item.from_dict(dict(r)) for r in rows]

    def get_by_status(self, status: str) -> List[Item]:
        """Повертає майно з певним статусом."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM items WHERE status=? ORDER BY added_at DESC", (status,)
            ).fetchall()
        return [Item.from_dict(dict(r)) for r in rows]

    def get_by_category(self, category: str) -> List[Item]:
        """Повертає майно за категорією."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM items WHERE category=? ORDER BY name", (category,)
            ).fetchall()
        return [Item.from_dict(dict(r)) for r in rows]

    def exists(self, inventory_number: str) -> bool:
        """Перевіряє, чи існує майно з таким інвентарним номером."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM items WHERE inventory_number=?", (inventory_number,)
            ).fetchone()
        return row is not None

    def search(self, query: str) -> List[Item]:
        """Пошук за назвою або інвентарним номером (часткове співпадіння)."""
        pattern = f"%{query}%"
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM items
                   WHERE name LIKE ? OR inventory_number LIKE ?
                   ORDER BY name""",
                (pattern, pattern),
            ).fetchall()
        return [Item.from_dict(dict(r)) for r in rows]


# ─────────────────────────── HISTORY ─────────────────────────

class HistoryRepository:
    """CRUD-операції для таблиці history."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def add(self, record: HistoryRecord) -> HistoryRecord:
        """Зберігає запис в журналі."""
        sql = """
            INSERT INTO history (item_inventory_number, operation, details, performed_at)
            VALUES (?, ?, ?, ?)
        """
        with self._conn() as conn:
            cursor = conn.execute(sql, (
                record.item_inventory_number, record.operation,
                record.details, record.performed_at,
            ))
            record.id = cursor.lastrowid
        return record

    def get_for_item(self, inventory_number: str) -> List[HistoryRecord]:
        """Повертає всю історію для конкретного майна."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM history WHERE item_inventory_number=? ORDER BY performed_at DESC",
                (inventory_number,),
            ).fetchall()
        return [HistoryRecord.from_dict(dict(r)) for r in rows]

    def get_all(self, limit: int = 500) -> List[HistoryRecord]:
        """Повертає останні `limit` записів журналу."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY performed_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [HistoryRecord.from_dict(dict(r)) for r in rows]

    def get_by_operation(self, operation: str) -> List[HistoryRecord]:
        """Фільтрує журнал за типом операції."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM history WHERE operation=? ORDER BY performed_at DESC",
                (operation,),
            ).fetchall()
        return [HistoryRecord.from_dict(dict(r)) for r in rows]

    def delete_all_for_item(self, inventory_number: str) -> None:
        """Видаляє всю історію для конкретного майна."""
        with self._conn() as conn:
            conn.execute("DELETE FROM history WHERE item_inventory_number=?", (inventory_number,))
