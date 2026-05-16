import sqlite3
import os

db_path = os.path.join("backend", "inventory.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("CATEGORIES:")
for row in conn.execute("SELECT * FROM categories").fetchall():
    print(dict(row))

print("\nITEMS (first 5):")
for row in conn.execute("SELECT inventory_number, name, category FROM items LIMIT 5").fetchall():
    print(dict(row))

conn.close()
