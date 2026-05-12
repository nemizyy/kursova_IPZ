"""
service.py — Сервісний шар (Service Layer / Facade).

Це головний API бекенду, який використовує frontend (Flet).
Об'єднує всі патерни та модулі в єдиний, зручний інтерфейс:
  - Factory  → створення об'єктів Item
  - Command  → виконання операцій з підтримкою Undo/Redo
  - Strategy → фільтрація та генерація звітів
  - Observer → сповіщення GUI про зміни

Приклад використання (у frontend):
    svc = InventoryService()
    svc.on(EventType.ITEM_ADDED, lambda e, d: table.update())

    svc.add_item("МЕБ-001", "Стіл письмовий", "furniture", 2500.0, "Кімната 101")
    svc.move_item("МЕБ-001", "Кімната 205")
    svc.undo()
"""

from typing import List, Optional, Callable

from .database import init_db, DB_PATH
from .models import Item, HistoryRecord, ItemStatus
from .repository import ItemRepository, HistoryRepository
from .factory import FactoryProvider
from .commands import (
    CommandManager,
    AddItemCommand,
    EditItemCommand,
    DeleteItemCommand,
    MoveItemCommand,
    WriteOffItemCommand,
)
from .strategies import (
    FilterStrategy,
    PriceFilterStrategy,
    DateFilterStrategy,
    StatusFilterStrategy,
    CategoryFilterStrategy,
    LocationFilterStrategy,
    CompositeFilterStrategy,
    ReportStrategy,
    SummaryReportStrategy,
    CategoryReportStrategy,
    WrittenOffReportStrategy,
    CSVReportStrategy,
)
from .observer import InventorySubject, EventType


class InventoryService:
    """
    Фасад над усіма модулями бекенду.
    Єдина точка входу для frontend.
    """

    def __init__(self, db_path: str = DB_PATH):
        # Ініціалізація БД
        init_db(db_path)

        # Репозиторії
        self._item_repo    = ItemRepository(db_path)
        self._history_repo = HistoryRepository(db_path)

        # Invoker для Command-патерну (з підтримкою Undo/Redo)
        self._cmd_manager  = CommandManager(max_history=100)

        # Subject для Observer-патерну
        self._subject      = InventorySubject()

    # ══════════════════════════════════════════════════════════
    #  Observer — підписка на події
    # ══════════════════════════════════════════════════════════

    def on(self, event_type: str, callback: Callable) -> None:
        """Підписати callable на подію (для GUI)."""
        self._subject.subscribe(event_type, callback)

    def off(self, event_type: str, callback: Callable) -> None:
        """Відписати callable від події."""
        self._subject.unsubscribe(event_type, callback)

    # ══════════════════════════════════════════════════════════
    #  Factory + Command: операції з майном
    # ══════════════════════════════════════════════════════════

    def add_item(
        self,
        inventory_number: str,
        name: str,
        category: str,
        cost: float,
        location: str = "",
        description: str = "",
    ) -> Item:
        """
        Додати нову одиницю майна.
        Використовує Factory для створення та Command для збереження.

        :raises ValueError: якщо інвентарний номер вже існує або дані невалідні.
        """
        self._validate_inventory_number(inventory_number)
        self._validate_cost(cost)

        if self._item_repo.exists(inventory_number):
            raise ValueError(
                f"Майно з інвентарним номером «{inventory_number}» вже існує."
            )

        factory = FactoryProvider.get(category)
        item = factory.create(
            inventory_number=inventory_number,
            name=name,
            cost=cost,
            location=location,
            description=description,
        )

        cmd = AddItemCommand(item, self._item_repo, self._history_repo, self._subject)
        self._cmd_manager.execute(cmd)
        return item

    def edit_item(self, inventory_number: str, **fields) -> None:
        """
        Оновити поля існуючої одиниці майна.
        Приклад: edit_item("МЕБ-001", name="Стіл круглий", cost=3000.0)
        """
        if not self._item_repo.exists(inventory_number):
            raise ValueError(f"Майно «{inventory_number}» не знайдено.")

        allowed = {"name", "category", "cost", "location", "description"}
        invalid = set(fields) - allowed
        if invalid:
            raise ValueError(f"Недозволені поля для редагування: {invalid}")

        if "cost" in fields:
            self._validate_cost(fields["cost"])

        cmd = EditItemCommand(
            inventory_number, fields,
            self._item_repo, self._history_repo, self._subject
        )
        self._cmd_manager.execute(cmd)

    def delete_item(self, inventory_number: str) -> None:
        """Видалити одиницю майна з бази."""
        if not self._item_repo.exists(inventory_number):
            raise ValueError(f"Майно «{inventory_number}» не знайдено.")

        cmd = DeleteItemCommand(
            inventory_number,
            self._item_repo, self._history_repo, self._subject
        )
        self._cmd_manager.execute(cmd)

    def move_item(self, inventory_number: str, new_location: str) -> None:
        """Перемістити майно до нового місця; статус стане 'moved'."""
        if not new_location.strip():
            raise ValueError("Місце призначення не може бути порожнім.")
        if not self._item_repo.exists(inventory_number):
            raise ValueError(f"Майно «{inventory_number}» не знайдено.")

        cmd = MoveItemCommand(
            inventory_number, new_location,
            self._item_repo, self._history_repo, self._subject
        )
        self._cmd_manager.execute(cmd)

    def write_off_item(self, inventory_number: str, reason: str = "Не придатне") -> None:
        """Списати майно; статус стане 'written_off'."""
        item = self._item_repo.get_by_inventory(inventory_number)
        if item is None:
            raise ValueError(f"Майно «{inventory_number}» не знайдено.")
        if item.status == ItemStatus.WRITTEN_OFF:
            raise ValueError(f"Майно «{inventory_number}» вже списано.")

        cmd = WriteOffItemCommand(
            inventory_number, reason,
            self._item_repo, self._history_repo, self._subject
        )
        self._cmd_manager.execute(cmd)

    # ══════════════════════════════════════════════════════════
    #  Undo / Redo
    # ══════════════════════════════════════════════════════════

    def undo(self) -> Optional[str]:
        """Скасувати останню операцію. Повертає опис або None."""
        if not self._cmd_manager.can_undo():
            return None
        return self._cmd_manager.undo()

    def redo(self) -> Optional[str]:
        """Повторити скасовану операцію. Повертає опис або None."""
        if not self._cmd_manager.can_redo():
            return None
        return self._cmd_manager.redo()

    def can_undo(self) -> bool:
        return self._cmd_manager.can_undo()

    def can_redo(self) -> bool:
        return self._cmd_manager.can_redo()

    def undo_history(self) -> List[str]:
        """Список операцій, які можна скасувати."""
        return self._cmd_manager.undo_history()

    # ══════════════════════════════════════════════════════════
    #  Читання даних
    # ══════════════════════════════════════════════════════════

    def get_all_items(self) -> List[Item]:
        """Повернути всі одиниці майна."""
        return self._item_repo.get_all()

    def get_item(self, inventory_number: str) -> Optional[Item]:
        """Повернути майно за інвентарним номером."""
        return self._item_repo.get_by_inventory(inventory_number)

    def search_items(self, query: str) -> List[Item]:
        """Пошук за назвою або інвентарним номером."""
        return self._item_repo.search(query)

    def get_history(self, inventory_number: Optional[str] = None) -> List[HistoryRecord]:
        """
        Повернути журнал операцій.
        :param inventory_number: якщо задано — лише для цього майна.
        """
        if inventory_number:
            return self._history_repo.get_for_item(inventory_number)
        return self._history_repo.get_all()

    def available_categories(self) -> List[str]:
        """Список зареєстрованих категорій майна."""
        return FactoryProvider.available_categories()

    # ══════════════════════════════════════════════════════════
    #  Strategy: фільтрація
    # ══════════════════════════════════════════════════════════

    def filter_items(
        self,
        *,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Item]:
        """
        Фільтрує майно за будь-якою комбінацією умов.
        Всі умови об'єднуються логічним AND.
        """
        strategies: List[FilterStrategy] = []

        if min_cost is not None or max_cost is not None:
            strategies.append(PriceFilterStrategy(
                min_cost=min_cost or 0.0,
                max_cost=max_cost or float("inf"),
            ))
        if date_from or date_to:
            strategies.append(DateFilterStrategy(date_from, date_to))
        if status:
            strategies.append(StatusFilterStrategy(status))
        if category:
            strategies.append(CategoryFilterStrategy(category))
        if location:
            strategies.append(LocationFilterStrategy(location))

        all_items = self._item_repo.get_all()

        if not strategies:
            return all_items

        composite = CompositeFilterStrategy(*strategies)
        return composite.apply(all_items)

    # ══════════════════════════════════════════════════════════
    #  Strategy: звіти
    # ══════════════════════════════════════════════════════════

    def generate_report(self, report_type: str = "summary", items: Optional[List[Item]] = None) -> str:
        """
        Згенерувати текстовий звіт.
        :param report_type: 'summary' | 'category' | 'written_off' | 'csv'
        :param items: якщо None — використовуються всі записи з БД.
        """
        if items is None:
            items = self._item_repo.get_all()

        strategies_map: dict[str, ReportStrategy] = {
            "summary":    SummaryReportStrategy(),
            "category":   CategoryReportStrategy(),
            "written_off": WrittenOffReportStrategy(),
            "csv":        CSVReportStrategy(),
        }

        strategy = strategies_map.get(report_type)
        if strategy is None:
            raise ValueError(
                f"Невідомий тип звіту «{report_type}». "
                f"Доступні: {list(strategies_map.keys())}"
            )

        return strategy.generate(items)

    # ══════════════════════════════════════════════════════════
    #  Валідація (приватні методи)
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _validate_inventory_number(inv: str) -> None:
        if not inv or not inv.strip():
            raise ValueError("Інвентарний номер не може бути порожнім.")
        if len(inv) > 50:
            raise ValueError("Інвентарний номер занадто довгий (максимум 50 символів).")

    @staticmethod
    def _validate_cost(cost: float) -> None:
        if cost < 0:
            raise ValueError("Вартість не може бути від'ємною.")
