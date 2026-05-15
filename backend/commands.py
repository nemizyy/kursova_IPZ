"""
commands.py — Патерн Command (Команда) (GoF).

РОЛЬ ПАТЕРНА В СИСТЕМІ:
Інкапсулює запит на операцію (додавання, редагування, видалення, списання) як окремий об'єкт.
Це дозволяє параметризувати клієнтів (Service/GUI) різними запитами, ставити їх у чергу 
та найголовніше — реалізувати механізм скасування (Undo) і повторення (Redo) операцій.

Кожна команда має методи execute() та undo().
Invoker (CommandManager) зберігає стек виконаних команд для можливості їх скасування.

Структура:
    BaseCommand (Abstract)
        ├── AddItemCommand
        ├── EditItemCommand
        ├── DeleteItemCommand
        ├── MoveItemCommand
        └── WriteOffItemCommand

    CommandManager — виконавець + стек undo/redo
"""

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List, Optional

from .models import Item, HistoryRecord, ItemStatus, Category
from .repository import ItemRepository, HistoryRepository, CategoryRepository
from .observer import InventorySubject, EventType


# ─── Базова команда ───────────────────────────────────────────

class BaseCommand(ABC):
    """Абстрактна команда операції над майном."""

    @abstractmethod
    def execute(self) -> None:
        """Виконати команду."""
        ...

    @abstractmethod
    def undo(self) -> None:
        """Скасувати команду."""
        ...

    @property
    def description(self) -> str:
        """Людськочитний опис команди (для журналу)."""
        return self.__class__.__name__


# ─── Конкретні команди ────────────────────────────────────────

class AddItemCommand(BaseCommand):
    """Додати нову одиницю майна."""

    def __init__(
        self,
        item: Item,
        item_repo: ItemRepository,
        history_repo: HistoryRepository,
        subject: Optional[InventorySubject] = None,
    ):
        self._item = deepcopy(item)
        self._item_repo = item_repo
        self._history_repo = history_repo
        self._subject = subject
        self._saved_id: Optional[int] = None

    def execute(self) -> None:
        saved = self._item_repo.add(self._item)
        self._saved_id = saved.id
        self._item.id = saved.id

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._item.inventory_number,
            operation="add",
            details=f"Додано: {self._item.name}, вартість {self._item.cost} грн",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_ADDED, self._item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    def undo(self) -> None:
        self._item_repo.delete(self._item.inventory_number)

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._item.inventory_number,
            operation="undo_add",
            details=f"Скасовано додавання: {self._item.name}",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_DELETED, self._item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    @property
    def description(self) -> str:
        return f"Додати «{self._item.name}» [{self._item.inventory_number}]"


class EditItemCommand(BaseCommand):
    """Редагувати дані існуючої одиниці майна."""

    def __init__(
        self,
        inventory_number: str,
        new_data: dict,
        item_repo: ItemRepository,
        history_repo: HistoryRepository,
        subject: Optional[InventorySubject] = None,
    ):
        self._inv_num = inventory_number
        self._new_data = new_data
        self._item_repo = item_repo
        self._history_repo = history_repo
        self._subject = subject
        self._old_item: Optional[Item] = None

    def execute(self) -> None:
        self._old_item = deepcopy(self._item_repo.get_by_inventory(self._inv_num))
        if self._old_item is None:
            raise ValueError(f"Майно {self._inv_num} не знайдено")

        updated = deepcopy(self._old_item)
        detailed_changes = []
        for key, value in self._new_data.items():
            if hasattr(updated, key):
                old_val = getattr(updated, key)
                if old_val != value:
                    detailed_changes.append(f"{key}: «{old_val}» -> «{value}»")
                    setattr(updated, key, value)

        if not detailed_changes:
            return # Нічого не змінилось

        self._item_repo.update(updated)

        changes_str = "; ".join(detailed_changes)
        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._inv_num,
            operation="edit",
            details=f"Змінено: {changes_str}",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_UPDATED, updated)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    def undo(self) -> None:
        if self._old_item is None:
            return
        self._item_repo.update(self._old_item)

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._inv_num,
            operation="undo_edit",
            details="Відновлено попередній стан",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_UPDATED, self._old_item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    @property
    def description(self) -> str:
        return f"Редагувати [{self._inv_num}]"


class DeleteItemCommand(BaseCommand):
    """Видалити одиницю майна."""

    def __init__(
        self,
        inventory_number: str,
        item_repo: ItemRepository,
        history_repo: HistoryRepository,
        subject: Optional[InventorySubject] = None,
    ):
        self._inv_num = inventory_number
        self._item_repo = item_repo
        self._history_repo = history_repo
        self._subject = subject
        self._deleted_item: Optional[Item] = None

    def execute(self) -> None:
        self._deleted_item = deepcopy(self._item_repo.get_by_inventory(self._inv_num))
        if self._deleted_item is None:
            raise ValueError(f"Майно {self._inv_num} не знайдено")

        # Зберігаємо історію для можливості скасування (undo) і видаляємо її з БД, 
        # щоб обійти обмеження ON DELETE RESTRICT
        self._saved_history = self._history_repo.get_for_item(self._inv_num)
        self._history_repo.delete_all_for_item(self._inv_num)

        self._item_repo.delete(self._inv_num)

        if self._subject:
            self._subject.notify(EventType.ITEM_DELETED, self._deleted_item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    def undo(self) -> None:
        if self._deleted_item is None:
            return
        self._deleted_item.id = None
        self._item_repo.add(self._deleted_item)

        # Відновлюємо попередню історію у правильному порядку
        if hasattr(self, '_saved_history'):
            for record in reversed(self._saved_history):
                record.id = None
                self._history_repo.add(record)

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._inv_num,
            operation="undo_delete",
            details=f"Відновлено після видалення: {self._deleted_item.name}",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_ADDED, self._deleted_item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    @property
    def description(self) -> str:
        return f"Видалити [{self._inv_num}]"


class MoveItemCommand(BaseCommand):
    """Перемістити майно до іншого місця."""

    def __init__(
        self,
        inventory_number: str,
        new_location: str,
        item_repo: ItemRepository,
        history_repo: HistoryRepository,
        subject: Optional[InventorySubject] = None,
    ):
        self._inv_num = inventory_number
        self._new_location = new_location
        self._item_repo = item_repo
        self._history_repo = history_repo
        self._subject = subject
        self._old_location: Optional[str] = None

    def execute(self) -> None:
        item = self._item_repo.get_by_inventory(self._inv_num)
        if item is None:
            raise ValueError(f"Майно {self._inv_num} не знайдено")

        self._old_location = item.location
        item.location = self._new_location
        item.status = ItemStatus.MOVED
        self._item_repo.update(item)

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._inv_num,
            operation="move",
            details=f"Переміщено: «{self._old_location}» → «{self._new_location}»",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_MOVED, item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    def undo(self) -> None:
        item = self._item_repo.get_by_inventory(self._inv_num)
        if item is None:
            return
        item.location = self._old_location or ""
        item.status = ItemStatus.ACTIVE
        self._item_repo.update(item)

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._inv_num,
            operation="undo_move",
            details=f"Скасовано переміщення, повернуто до «{self._old_location}»",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_UPDATED, item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    @property
    def description(self) -> str:
        return f"Перемістити [{self._inv_num}] → «{self._new_location}»"


class WriteOffItemCommand(BaseCommand):
    """Списати одиницю майна."""

    def __init__(
        self,
        inventory_number: str,
        reason: str,
        item_repo: ItemRepository,
        history_repo: HistoryRepository,
        subject: Optional[InventorySubject] = None,
    ):
        self._inv_num = inventory_number
        self._reason = reason
        self._item_repo = item_repo
        self._history_repo = history_repo
        self._subject = subject
        self._old_status: Optional[str] = None

    def execute(self) -> None:
        item = self._item_repo.get_by_inventory(self._inv_num)
        if item is None:
            raise ValueError(f"Майно {self._inv_num} не знайдено")

        self._old_status = item.status
        item.status = ItemStatus.WRITTEN_OFF
        self._item_repo.update(item)

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._inv_num,
            operation="write_off",
            details=f"Списано. Причина: {self._reason}",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_WRITTEN_OFF, item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    def undo(self) -> None:
        item = self._item_repo.get_by_inventory(self._inv_num)
        if item is None:
            return
        item.status = self._old_status or ItemStatus.ACTIVE
        self._item_repo.update(item)

        self._history_repo.add(HistoryRecord(
            item_inventory_number=self._inv_num,
            operation="undo_write_off",
            details="Скасовано списання",
        ))

        if self._subject:
            self._subject.notify(EventType.ITEM_UPDATED, item)
            self._subject.notify(EventType.HISTORY_CHANGED, None)

    @property
    def description(self) -> str:
        return f"Списати [{self._inv_num}]"


# ────────────────────────── CATEGORY COMMANDS ────────────────

class AddCategoryCommand(BaseCommand):
    def __init__(self, category: Category, repo: CategoryRepository, subject: Optional[InventorySubject] = None):
        self._cat = category
        self._repo = repo
        self._subject = subject

    def execute(self) -> None:
        self._repo.add(self._cat)
        if self._subject:
            self._subject.notify("category_added", self._cat)

    def undo(self) -> None:
        self._repo.delete(self._cat.name)
        if self._subject:
            self._subject.notify("category_deleted", self._cat)

    @property
    def description(self) -> str:
        return f"Додати категорію «{self._cat.label}»"


class EditCategoryCommand(BaseCommand):
    def __init__(self, name: str, new_label: str, new_parent: Optional[str], repo: CategoryRepository, subject: Optional[InventorySubject] = None):
        self._name = name
        self._new_label = new_label
        self._new_parent = new_parent
        self._repo = repo
        self._subject = subject
        self._old_cat: Optional[Category] = None

    def execute(self) -> None:
        self._old_cat = deepcopy(self._repo.get_by_name(self._name))
        updated = Category(name=self._name, label=self._new_label, parent_name=self._new_parent)
        self._repo.update(updated)
        if self._subject:
            self._subject.notify("category_updated", updated)

    def undo(self) -> None:
        if self._old_cat:
            self._repo.update(self._old_cat)
            if self._subject:
                self._subject.notify("category_updated", self._old_cat)

    @property
    def description(self) -> str:
        return f"Редагувати категорію «{self._name}»"


class DeleteCategoryCommand(BaseCommand):
    def __init__(self, name: str, repo: CategoryRepository, subject: Optional[InventorySubject] = None):
        self._name = name
        self._repo = repo
        self._subject = subject
        self._deleted_cat: Optional[Category] = None

    def execute(self) -> None:
        self._deleted_cat = self._repo.get_by_name(self._name)
        self._repo.delete(self._name)
        if self._subject:
            self._subject.notify("category_deleted", self._deleted_cat)

    def undo(self) -> None:
        if self._deleted_cat:
            self._repo.add(self._deleted_cat)
            if self._subject:
                self._subject.notify("category_added", self._deleted_cat)

    @property
    def description(self) -> str:
        return f"Видалити категорію «{self._name}»"


# ─── Invoker (менеджер команд) ────────────────────────────────

class CommandManager:
    """
    Invoker: виконує команди та зберігає стек для Undo/Redo.
    """

    def __init__(self, max_history: int = 50):
        self._undo_stack: List[BaseCommand] = []
        self._redo_stack: List[BaseCommand] = []
        self._max_history = max_history

    def execute(self, command: BaseCommand) -> None:
        """Виконати команду та додати до стеку скасування."""
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()           # Нова операція скидає redo
        # Обмежуємо розмір стеку
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)

    def undo(self) -> Optional[str]:
        """Скасувати останню операцію. Повертає опис або None."""
        if not self._undo_stack:
            return None
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return command.description

    def redo(self) -> Optional[str]:
        """Повторити скасовану операцію. Повертає опис або None."""
        if not self._redo_stack:
            return None
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        return command.description

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo_history(self) -> List[str]:
        """Список описів команд у стеку скасування (від останньої до першої)."""
        return [c.description for c in reversed(self._undo_stack)]

    def clear(self) -> None:
        """Очистити стеки."""
        self._undo_stack.clear()
        self._redo_stack.clear()
