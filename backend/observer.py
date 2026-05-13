"""
observer.py — Патерн Observer (Спостерігач) (GoF).

РОЛЬ ПАТЕРНА В СИСТЕМІ:
Забезпечує слабку зв'язність (loose coupling) між бізнес-логікою (backend) та графічним інтерфейсом (frontend).
Бекенд виступає як Subject (видавець подій), не знаючи нічого про конкретну реалізацію GUI.
GUI (Flet) підписується як Observer на події (наприклад, додавання або видалення майна) 
і автоматично оновлює відображення (таблиці, списки) при настанні події.

Використання:
    subject = InventorySubject()
    subject.subscribe(EventType.ITEM_ADDED, my_callback)
    subject.notify(EventType.ITEM_ADDED, item)
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Any


# ─── Типи подій ──────────────────────────────────────────────

class EventType:
    """Константи подій, що генерує бекенд."""
    ITEM_ADDED     = "item_added"
    ITEM_UPDATED   = "item_updated"
    ITEM_DELETED   = "item_deleted"
    ITEM_MOVED     = "item_moved"
    ITEM_WRITTEN_OFF = "item_written_off"
    HISTORY_CHANGED = "history_changed"
    ERROR_OCCURRED  = "error_occurred"


# ─── Базові абстракції ────────────────────────────────────────

class Observer(ABC):
    """Абстрактний спостерігач."""

    @abstractmethod
    def update(self, event_type: str, data: Any) -> None:
        """Викликається при настанні події."""
        ...


class Subject(ABC):
    """Абстрактний видавець (Subject)."""

    @abstractmethod
    def subscribe(self, event_type: str, observer: "Observer") -> None: ...

    @abstractmethod
    def unsubscribe(self, event_type: str, observer: "Observer") -> None: ...

    @abstractmethod
    def notify(self, event_type: str, data: Any) -> None: ...


# ─── Конкретний Subject ───────────────────────────────────────

class InventorySubject(Subject):
    """
    Центральний видавець подій системи обліку майна.
    Підтримує підписку як на Observer-об'єкти, так і на callable.
    """

    def __init__(self):
        # event_type -> список обробників (Observer або callable)
        self._listeners: Dict[str, List] = {}

    def subscribe(self, event_type: str, observer) -> None:
        """Підписати спостерігача на подію."""
        self._listeners.setdefault(event_type, [])
        if observer not in self._listeners[event_type]:
            self._listeners[event_type].append(observer)

    def unsubscribe(self, event_type: str, observer) -> None:
        """Відписати спостерігача від події."""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                o for o in self._listeners[event_type] if o != observer
            ]

    def notify(self, event_type: str, data: Any = None) -> None:
        """Сповістити всіх підписників про подію."""
        for handler in self._listeners.get(event_type, []):
            if isinstance(handler, Observer):
                handler.update(event_type, data)
            elif callable(handler):
                handler(event_type, data)

    def subscribe_all(self, observer) -> None:
        """Підписати спостерігача на всі типи подій одразу."""
        for event in vars(EventType).values():
            if isinstance(event, str) and not event.startswith("_"):
                self.subscribe(event, observer)


# ─── Приклади конкретних Observer-ів ─────────────────────────

class LogObserver(Observer):
    """Простий спостерігач, що виводить події у консоль (для відлагодження)."""

    def update(self, event_type: str, data: Any) -> None:
        print(f"[Observer/Log] Подія: {event_type} | Дані: {data}")


class GUIObserver(Observer):
    """
    Заглушка для GUI-спостерігача (Flet).
    Frontend підмінить цей клас своєю реалізацією.
    """

    def __init__(self, refresh_callback: Callable):
        """
        :param refresh_callback: функція оновлення таблиці у GUI,
                                 наприклад page.update() або table.update()
        """
        self._callback = refresh_callback

    def update(self, event_type: str, data: Any) -> None:
        self._callback(event_type, data)
