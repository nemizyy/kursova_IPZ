from models.database import db

class InventoryController:
    def __init__(self):
        self.observers = []

    def add_observer(self, observer_callback):
        self.observers.append(observer_callback)

    def notify_observers(self):
        for observer in self.observers:
            observer()

    def get_items(self):
        return db.get_items()

    def add_item(self, name, category, quantity, photo_source_path=None):
        db.add_item(name, category, quantity, photo_source_path)
        self.notify_observers()

    def get_statistics(self):
        return db.get_statistics()
