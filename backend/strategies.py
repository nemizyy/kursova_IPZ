"""
strategies.py — Патерн Strategy (Стратегія).

Використовується для:
  1. Алгоритмів фільтрації списку майна.
  2. Алгоритмів генерації звітів.

Структура:
    FilterStrategy (Abstract)
        ├── PriceFilterStrategy       — фільтр за вартістю
        ├── DateFilterStrategy        — фільтр за датою додавання
        ├── StatusFilterStrategy      — фільтр за статусом
        ├── CategoryFilterStrategy    — фільтр за категорією
        └── CompositeFilterStrategy   — комбінований фільтр (AND)

    ReportStrategy (Abstract)
        ├── SummaryReportStrategy     — зведений звіт
        ├── CategoryReportStrategy    — звіт по категоріях
        └── WrittenOffReportStrategy  — звіт про списане майно
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from .models import Item, ItemStatus


# ══════════════════════════════════════════════════════════════
#  ФІЛЬТРАЦІЯ
# ══════════════════════════════════════════════════════════════

class FilterStrategy(ABC):
    """Абстрактна стратегія фільтрації."""

    @abstractmethod
    def apply(self, items: List[Item]) -> List[Item]:
        """Повертає відфільтрований список."""
        ...


class PriceFilterStrategy(FilterStrategy):
    """Фільтрує майно за діапазоном вартості."""

    def __init__(self, min_cost: float = 0.0, max_cost: float = float("inf")):
        self.min_cost = min_cost
        self.max_cost = max_cost

    def apply(self, items: List[Item]) -> List[Item]:
        return [i for i in items if self.min_cost <= i.cost <= self.max_cost]


class DateFilterStrategy(FilterStrategy):
    """Фільтрує майно за датою додавання."""

    def __init__(self, date_from: Optional[str] = None, date_to: Optional[str] = None):
        """
        :param date_from: ISO-рядок дати початку (включно), напр. '2024-01-01'
        :param date_to:   ISO-рядок дати кінця (включно),   напр. '2024-12-31'
        """
        self.date_from = date_from
        self.date_to   = date_to

    def apply(self, items: List[Item]) -> List[Item]:
        result = []
        for item in items:
            added = item.added_at[:10]  # беремо лише YYYY-MM-DD
            if self.date_from and added < self.date_from:
                continue
            if self.date_to and added > self.date_to:
                continue
            result.append(item)
        return result


class StatusFilterStrategy(FilterStrategy):
    """Фільтрує майно за статусом."""

    def __init__(self, status: str):
        self.status = status

    def apply(self, items: List[Item]) -> List[Item]:
        return [i for i in items if i.status == self.status]


class CategoryFilterStrategy(FilterStrategy):
    """Фільтрує майно за категорією."""

    def __init__(self, category: str):
        self.category = category.lower()

    def apply(self, items: List[Item]) -> List[Item]:
        return [i for i in items if i.category.lower() == self.category]


class LocationFilterStrategy(FilterStrategy):
    """Фільтрує майно за місцем знаходження (часткове співпадіння)."""

    def __init__(self, location_query: str):
        self.query = location_query.lower()

    def apply(self, items: List[Item]) -> List[Item]:
        return [i for i in items if self.query in i.location.lower()]


class CompositeFilterStrategy(FilterStrategy):
    """Застосовує кілька стратегій послідовно (логічне AND)."""

    def __init__(self, *strategies: FilterStrategy):
        self.strategies = list(strategies)

    def add(self, strategy: FilterStrategy) -> "CompositeFilterStrategy":
        self.strategies.append(strategy)
        return self

    def apply(self, items: List[Item]) -> List[Item]:
        result = items
        for strategy in self.strategies:
            result = strategy.apply(result)
        return result


# ══════════════════════════════════════════════════════════════
#  ЗВІТИ
# ══════════════════════════════════════════════════════════════

class ReportStrategy(ABC):
    """Абстрактна стратегія генерації звіту."""

    @abstractmethod
    def generate(self, items: List[Item]) -> str:
        """Повертає звіт у вигляді рядка (текст / CSV / JSON)."""
        ...


class SummaryReportStrategy(ReportStrategy):
    """Зведений звіт: загальна кількість та вартість майна."""

    def generate(self, items: List[Item]) -> str:
        total = len(items)
        total_cost = sum(i.cost for i in items)
        active = sum(1 for i in items if i.status == ItemStatus.ACTIVE)
        written_off = sum(1 for i in items if i.status == ItemStatus.WRITTEN_OFF)
        moved = sum(1 for i in items if i.status == ItemStatus.MOVED)

        lines = [
            "=" * 40,
            "       ЗВЕДЕНИЙ ЗВІТ ПО МАЙНУ",
            "=" * 40,
            f"Дата формування : {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            f"Усього позицій  : {total}",
            f"  - Активне     : {active}",
            f"  - Переміщене  : {moved}",
            f"  - Списане     : {written_off}",
            f"Загальна вартість: {total_cost:,.2f} грн",
            "=" * 40,
        ]
        return "\n".join(lines)


class CategoryReportStrategy(ReportStrategy):
    """Звіт із розбивкою за категоріями."""

    def generate(self, items: List[Item]) -> str:
        categories: dict = {}
        for item in items:
            cat = item.category
            if cat not in categories:
                categories[cat] = {"count": 0, "total_cost": 0.0}
            categories[cat]["count"] += 1
            categories[cat]["total_cost"] += item.cost

        lines = [
            "=" * 40,
            "    ЗВІТ ЗА КАТЕГОРІЯМИ МАЙНА",
            "=" * 40,
        ]
        for cat, data in sorted(categories.items()):
            lines.append(
                f"{cat.upper():20s}: {data['count']:4d} од. | "
                f"{data['total_cost']:>12,.2f} грн"
            )
        lines.append("=" * 40)
        return "\n".join(lines)


class WrittenOffReportStrategy(ReportStrategy):
    """Звіт лише про списане майно."""

    def generate(self, items: List[Item]) -> str:
        written = [i for i in items if i.status == ItemStatus.WRITTEN_OFF]
        lines = [
            "=" * 50,
            "          ЗВІТ ПРО СПИСАНЕ МАЙНО",
            "=" * 50,
            f"{'Інв. №':<15} {'Назва':<20} {'Вартість':>10}",
            "-" * 50,
        ]
        total = 0.0
        for item in written:
            lines.append(
                f"{item.inventory_number:<15} {item.name:<20} {item.cost:>10,.2f}"
            )
            total += item.cost
        lines += [
            "-" * 50,
            f"{'Усього списано:':>37} {total:>10,.2f} грн",
            "=" * 50,
        ]
        return "\n".join(lines)


class CSVReportStrategy(ReportStrategy):
    """Генерує звіт у форматі CSV."""

    HEADER = "inventory_number,name,category,cost,status,added_at,location"

    def generate(self, items: List[Item]) -> str:
        rows = [self.HEADER]
        for i in items:
            rows.append(
                f"{i.inventory_number},{i.name},{i.category},"
                f"{i.cost},{i.status},{i.added_at},{i.location}"
            )
        return "\n".join(rows)
