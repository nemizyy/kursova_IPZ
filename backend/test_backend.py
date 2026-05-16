"""
test_backend.py - Smoke-test for all backend modules.
Run: python test_backend.py
"""

import gc
import os
import sys

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Щоб Python знайшов модулі бекенду
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from backend.database import init_db
    from backend.service import InventoryService
    from backend.observer import EventType
except ImportError:
    from database import init_db
    from service import InventoryService
    from observer import EventType

# ─── Тимчасова БД для тестів ─────────────────────────────────
TEST_DB = os.path.join(os.path.dirname(__file__), "_test_inventory.db")

# Чистий старт
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

events_received = []

def on_event(event_type, data):
    events_received.append(event_type)
    print(f"  [EVENT] {event_type}")

print("=" * 55)
print("  SMOKE-ТЕСТ БЕКЕНДУ — Облік майна")
print("=" * 55)

svc = InventoryService(db_path=TEST_DB)
svc.on(EventType.ITEM_ADDED,     on_event)
svc.on(EventType.ITEM_UPDATED,   on_event)
svc.on(EventType.ITEM_DELETED,   on_event)
svc.on(EventType.ITEM_MOVED,     on_event)
svc.on(EventType.ITEM_WRITTEN_OFF, on_event)

# ── 1. Додавання ──────────────────────────────────────────────
print("\n[1] Додавання майна через Factory...")
svc.add_item("МЕБ-001", "Стіл письмовий",     "furniture",   2500.0, "Кімната 101")
svc.add_item("ЕЛ-001",  "Ноутбук HP",          "electronics", 35000.0, "Кімната 202")
svc.add_item("ЕЛ-002",  "Принтер Canon",       "electronics", 8000.0,  "Кімната 101")
svc.add_item("МЕБ-002", "Стілець офісний",     "furniture",   1200.0, "Кімната 303")
svc.add_item("ТРП-001", "Автомобіль Skoda",    "vehicle",    450000.0, "Гараж")

items = svc.get_all_items()
print(f"  Додано: {len(items)} позицій — OK ✓")
assert len(items) == 5

# ── 2. Унікальність інв. номеру ───────────────────────────────
print("\n[2] Перевірка унікальності інвентарного номеру...")
try:
    svc.add_item("МЕБ-001", "Дублікат", "furniture", 100.0)
    print("  ПОМИЛКА: дублікат не викинув виключення!")
except ValueError as e:
    print(f"  ValueError піднято — OK ✓ ({e})")

# ── 3. Редагування ────────────────────────────────────────────
print("\n[3] Редагування майна...")
svc.edit_item("МЕБ-001", name="Стіл керівника", cost=4500.0)
item = svc.get_item("МЕБ-001")
assert item.name == "Стіл керівника"
assert item.cost == 4500.0
print(f"  Оновлено: {item.name}, {item.cost} грн — OK ✓")

# ── 4. Переміщення ────────────────────────────────────────────
print("\n[4] Переміщення майна...")
svc.move_item("ЕЛ-001", "Кімната 305")
item = svc.get_item("ЕЛ-001")
assert item.location == "Кімната 305"
assert item.status == "moved"
print(f"  Переміщено до: {item.location}, статус: {item.status} — OK ✓")

# ── 5. Списання ───────────────────────────────────────────────
print("\n[5] Списання майна...")
svc.write_off_item("МЕБ-002", reason="Фізичний знос")
item = svc.get_item("МЕБ-002")
assert item.status == "written_off"
print(f"  Статус: {item.status} — OK ✓")

# ── 6. Undo / Redo ────────────────────────────────────────────
print("\n[6] Undo / Redo...")
desc = svc.undo()
print(f"  Undo: {desc}")
item = svc.get_item("МЕБ-002")
assert item.status != "written_off", "Undo не відновив статус"
print(f"  Статус після Undo: {item.status} — OK ✓")

desc = svc.redo()
print(f"  Redo: {desc}")
item = svc.get_item("МЕБ-002")
assert item.status == "written_off"
print(f"  Статус після Redo: {item.status} — OK ✓")

# ── 7. Фільтрація (Strategy) ──────────────────────────────────
print("\n[7] Фільтрація майна (Strategy)...")
cheap = svc.filter_items(max_cost=5000.0)
print(f"  До 5000 грн: {len(cheap)} позиції — {[i.name for i in cheap]}")

electronics = svc.filter_items(category="electronics")
print(f"  Тільки електроніка: {len(electronics)} позиції — OK ✓")
assert len(electronics) == 2

active = svc.filter_items(status="active")
print(f"  Активні: {len(active)} позиції — OK ✓")

# ── 8. Пошук ─────────────────────────────────────────────────
print("\n[8] Пошук...")
results = svc.search_items("Стіл")
print(f"  «Стіл»: знайдено {len(results)} — {[i.name for i in results]}")
assert len(results) >= 1

# ── 9. Звіти (Strategy) ───────────────────────────────────────
print("\n[9] Генерація звітів (Strategy)...")
for rtype in ["summary", "category", "written_off", "csv"]:
    report = svc.generate_report(rtype)
    print(f"\n  --- {rtype.upper()} ---")
    print(report[:300])

# ── 10. Журнал операцій ──────────────────────────────────────
print("\n[10] Журнал операцій...")
history = svc.get_history()
print(f"  Усього записів у журналі: {len(history)}")
for rec in history[:5]:
    print(f"   • [{rec.operation}] {rec.item_inventory_number}: {rec.details}")

# ── 11. Observer events ───────────────────────────────────────
print(f"\n[11] Observer — отримано подій: {len(events_received)}")
assert len(events_received) > 0
print(f"  Events: {events_received}")

print("\n" + "=" * 55)
print("  USI TESTY PROJSHLY USPISHNO [OK]")
print("=" * 55)

# ── Прибирання ──────────────────────────────────────────────
del svc
gc.collect()  # Закриваємо SQLite-з'єднання перед видаленням
try:
    os.remove(TEST_DB)
    print("[cleanup] Тестову БД видалено.")
except PermissionError:
    print("[cleanup] Тестова БД буде видалена при наступному запуску.")
