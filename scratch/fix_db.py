import sqlite3
import os

db_path = os.path.join("backend", "inventory.db")
if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = OFF;") # Disable FK for migration

try:
    print("Normalizing categories...")
    # 1. Lowercase all categories names
    conn.execute("UPDATE categories SET name = LOWER(name)")
    
    # 2. Lowercase all item categories to match
    conn.execute("UPDATE items SET category = LOWER(category)")
    
    # 3. Lowercase all parent names in categories
    conn.execute("UPDATE categories SET parent_name = LOWER(parent_name) WHERE parent_name IS NOT NULL")
    
    conn.commit()
    print("Database normalized successfully!")
except Exception as e:
    conn.rollback()
    print(f"Error during normalization: {e}")
finally:
    conn.close()
