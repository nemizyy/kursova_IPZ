"""
models.py — Моделі даних (dataclasses) для майна та історії операцій.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class ItemStatus:
    """Допустимі статуси майна."""
    ACTIVE = "active"           # Активне (в наявності)
    WRITTEN_OFF = "written_off" # Списане
    MOVED = "moved"             # Переміщене


class ItemCategory:
    """Базові категорії майна."""
    FURNITURE = "furniture"         # Меблі
    ELECTRONICS = "electronics"     # Техніка / Електроніка
    VEHICLE = "vehicle"             # Транспорт
    EQUIPMENT = "equipment"         # Обладнання
    OTHER = "other"                 # Інше


@dataclass
class Category:
    """Модель категорії майна."""
    name: str                       # Технічна назва (ID), напр. 'laptops'
    label: str                      # Відображувана назва, напр. 'Ноутбуки'
    parent_name: Optional[str] = None # Батьківська категорія

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "parent_name": self.parent_name,
        }

    @staticmethod
    def from_dict(data: dict) -> "Category":
        return Category(
            name=data["name"],
            label=data["label"],
            parent_name=data.get("parent_name"),
        )


@dataclass
class Item:
    """Модель одиниці майна."""
    inventory_number: str           # Унікальний інвентарний номер
    name: str                       # Назва майна
    category: str                   # Категорія (з ItemCategory)
    cost: float                     # Вартість (грн)
    status: str = ItemStatus.ACTIVE # Поточний статус
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    location: str = ""              # Місце знаходження (кімната/відділ)
    description: str = ""          # Додатковий опис
    photo_path: str = ""           # Шлях до прикріпленої фотографії
    id: Optional[int] = None        # Primary key у БД (заповнюється після запису)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "inventory_number": self.inventory_number,
            "name": self.name,
            "category": self.category,
            "cost": self.cost,
            "status": self.status,
            "added_at": self.added_at,
            "location": self.location,
            "description": self.description,
            "photo_path": self.photo_path,
        }

    @staticmethod
    def from_dict(data: dict) -> "Item":
        return Item(
            id=data.get("id"),
            inventory_number=data["inventory_number"],
            name=data["name"],
            category=data["category"],
            cost=float(data["cost"]),
            status=data.get("status", ItemStatus.ACTIVE),
            added_at=data.get("added_at", datetime.now().isoformat()),
            location=data.get("location", ""),
            description=data.get("description", ""),
            photo_path=data.get("photo_path", ""),
        )


@dataclass
class HistoryRecord:
    """Запис в журналі операцій."""
    item_inventory_number: str      # Інвентарний номер майна
    operation: str                  # Тип операції: 'add', 'edit', 'delete', 'move', 'write_off'
    details: str                    # Деталі операції (що змінилось)
    performed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "item_inventory_number": self.item_inventory_number,
            "operation": self.operation,
            "details": self.details,
            "performed_at": self.performed_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "HistoryRecord":
        return HistoryRecord(
            id=data.get("id"),
            item_inventory_number=data["item_inventory_number"],
            operation=data["operation"],
            details=data.get("details", ""),
            performed_at=data.get("performed_at", datetime.now().isoformat()),
        )
