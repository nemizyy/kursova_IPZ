import os
import shutil

class Item:
    def __init__(self, item_id, name, category, quantity, photo_path=None):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.quantity = quantity
        self.photo_path = photo_path

class Database:
    def __init__(self):
        self.items = [
            Item(1, "Стіл офісний", "Меблі", 5),
            Item(2, "Ноутбук Dell", "Електроніка", 2),
            Item(3, "Крісло", "Меблі", 10),
        ]
        self.next_id = 4
        
        # Ensure image directory exists
        self.image_dir = "assets/images"
        os.makedirs(self.image_dir, exist_ok=True)

    def get_items(self):
        return self.items

    def add_item(self, name, category, quantity, photo_source_path=None):
        photo_path = None
        if photo_source_path and os.path.exists(photo_source_path):
            filename = os.path.basename(photo_source_path)
            photo_path = os.path.join(self.image_dir, filename)
            shutil.copy(photo_source_path, photo_path)

        new_item = Item(self.next_id, name, category, quantity, photo_path)
        self.items.append(new_item)
        self.next_id += 1
        return new_item

    def get_statistics(self):
        total_items = len(self.items)
        total_quantity = sum(item.quantity for item in self.items)
        categories = set(item.category for item in self.items)
        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "total_categories": len(categories)
        }

# Global instance for simplicity
db = Database()
