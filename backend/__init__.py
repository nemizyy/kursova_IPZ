"""
__init__.py — Публічний API пакету backend.

Frontend (Flet) імпортує лише звідси:
    from backend import InventoryService, EventType
"""

from .service import InventoryService
from .observer import EventType
from .models import Item, HistoryRecord, ItemStatus, ItemCategory
from .factory import FactoryProvider

__all__ = [
    "InventoryService",
    "EventType",
    "Item",
    "HistoryRecord",
    "ItemStatus",
    "ItemCategory",
    "FactoryProvider",
]
