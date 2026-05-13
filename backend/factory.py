"""
factory.py — Патерн Factory Method / Abstract Factory (GoF).

РОЛЬ ПАТЕРНА В СИСТЕМІ:
Використовується для гнучкого створення об'єктів Item різних категорій (меблі, електроніка тощо).
Замість прямого створення екземплярів через конструктор, клієнт (Service) звертається 
до фабрики, яка ініціалізує об'єкт з дефолтними значеннями, специфічними для його категорії.
Це спрощує додавання нових типів майна без зміни існуючого коду (Open/Closed Principle).

Ієрархія:
    ItemFactory (Abstract Factory Method)
        ├── FurnitureFactory
        ├── ElectronicsFactory
        ├── VehicleFactory
        └── EquipmentFactory

Також є FactoryProvider — реєстр фабрик, що дозволяє отримати
потрібну фабрику за назвою категорії (розширюване).
"""

from abc import ABC, abstractmethod
from datetime import datetime

from .models import Item, ItemCategory, ItemStatus


# ─── Абстрактна фабрика ───────────────────────────────────────

class ItemFactory(ABC):
    """Абстрактний Factory Method для створення майна."""

    @abstractmethod
    def create(
        self,
        inventory_number: str,
        name: str,
        cost: float,
        location: str = "",
        description: str = "",
        photo_path: str = "",
    ) -> Item:
        """Створює об'єкт Item з категорією, характерною для фабрики."""
        ...

    @property
    @abstractmethod
    def category(self) -> str:
        """Категорія майна, яку обслуговує ця фабрика."""
        ...

    def _base_item(
        self,
        inventory_number: str,
        name: str,
        cost: float,
        location: str,
        description: str,
        photo_path: str,
    ) -> Item:
        """Допоміжний метод: будує Item із заданими та дефолтними значеннями."""
        return Item(
            inventory_number=inventory_number,
            name=name,
            category=self.category,
            cost=cost,
            status=ItemStatus.ACTIVE,
            added_at=datetime.now().isoformat(),
            location=location,
            description=description,
            photo_path=photo_path,
        )


# ─── Конкретні фабрики ────────────────────────────────────────

class FurnitureFactory(ItemFactory):
    """Фабрика для меблів (столи, стільці, шафи тощо)."""

    @property
    def category(self) -> str:
        return ItemCategory.FURNITURE

    def create(self, inventory_number, name, cost, location="", description="", photo_path="") -> Item:
        desc = description or f"Меблі: {name}"
        return self._base_item(inventory_number, name, cost, location, desc, photo_path)


class ElectronicsFactory(ItemFactory):
    """Фабрика для електронної техніки (комп'ютери, принтери тощо)."""

    @property
    def category(self) -> str:
        return ItemCategory.ELECTRONICS

    def create(self, inventory_number, name, cost, location="", description="", photo_path="") -> Item:
        desc = description or f"Електроніка: {name}"
        return self._base_item(inventory_number, name, cost, location, desc, photo_path)


class VehicleFactory(ItemFactory):
    """Фабрика для транспортних засобів."""

    @property
    def category(self) -> str:
        return ItemCategory.VEHICLE

    def create(self, inventory_number, name, cost, location="", description="", photo_path="") -> Item:
        desc = description or f"Транспорт: {name}"
        return self._base_item(inventory_number, name, cost, location, desc, photo_path)


class EquipmentFactory(ItemFactory):
    """Фабрика для виробничого / офісного обладнання."""

    @property
    def category(self) -> str:
        return ItemCategory.EQUIPMENT

    def create(self, inventory_number, name, cost, location="", description="", photo_path="") -> Item:
        desc = description or f"Обладнання: {name}"
        return self._base_item(inventory_number, name, cost, location, desc, photo_path)


class OtherItemFactory(ItemFactory):
    """Універсальна фабрика для нестандартних категорій."""

    @property
    def category(self) -> str:
        return ItemCategory.OTHER

    def create(self, inventory_number, name, cost, location="", description="", photo_path="") -> Item:
        return self._base_item(inventory_number, name, cost, location, description, photo_path)


# ─── Реєстр фабрик (Factory Provider) ────────────────────────

class FactoryProvider:
    """
    Повертає потрібну фабрику за назвою категорії.
    Нові фабрики можна зареєструвати через register().
    """

    _registry: dict = {}

    @classmethod
    def _ensure_defaults(cls) -> None:
        if not cls._registry:
            cls.register(ItemCategory.FURNITURE,   FurnitureFactory())
            cls.register(ItemCategory.ELECTRONICS, ElectronicsFactory())
            cls.register(ItemCategory.VEHICLE,     VehicleFactory())
            cls.register(ItemCategory.EQUIPMENT,   EquipmentFactory())
            cls.register(ItemCategory.OTHER,       OtherItemFactory())

    @classmethod
    def register(cls, category: str, factory: ItemFactory) -> None:
        """Зареєструвати нову фабрику для категорії."""
        cls._registry[category.lower()] = factory

    @classmethod
    def get(cls, category: str) -> ItemFactory:
        """
        Повернути фабрику за категорією.
        Якщо категорія невідома — повертається OtherItemFactory.
        """
        cls._ensure_defaults()
        return cls._registry.get(category.lower(), OtherItemFactory())

    @classmethod
    def available_categories(cls) -> list:
        """Список зареєстрованих категорій."""
        cls._ensure_defaults()
        return list(cls._registry.keys())
