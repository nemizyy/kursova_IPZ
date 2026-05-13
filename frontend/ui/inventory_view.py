import flet as ft
from backend import InventoryService, EventType, ItemCategory


# Map backend category keys to Ukrainian labels
CATEGORY_LABELS = {
    ItemCategory.FURNITURE: "Меблі",
    ItemCategory.ELECTRONICS: "Електроніка",
    ItemCategory.VEHICLE: "Транспорт",
    ItemCategory.EQUIPMENT: "Обладнання",
    ItemCategory.OTHER: "Інше",
}


def build_inventory_content(page: ft.Page, service: InventoryService):
    """Builds and returns the inventory content (form + table), connected to backend."""

    # ── Data Table ──
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Інв. номер")),
            ft.DataColumn(ft.Text("Назва")),
            ft.DataColumn(ft.Text("Категорія")),
            ft.DataColumn(ft.Text("Вартість (грн)")),
            ft.DataColumn(ft.Text("Статус")),
            ft.DataColumn(ft.Text("Локація")),
            ft.DataColumn(ft.Text("Фото")),
        ],
        rows=[],
    )

    def refresh_table(*args):
        """Reload all items from DB and redraw the table."""
        table.rows.clear()
        for item in service.get_all_items():
            status_color = ft.Colors.GREEN_400 if item.status == "active" else ft.Colors.RED_400
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.inventory_number)),
                        ft.DataCell(ft.Text(item.name)),
                        ft.DataCell(ft.Text(CATEGORY_LABELS.get(item.category, item.category))),
                        ft.DataCell(ft.Text(f"{item.cost:,.2f}")),
                        ft.DataCell(ft.Text(item.status, color=status_color)),
                        ft.DataCell(ft.Text(item.location or "—")),
                        ft.DataCell(ft.Icon("image" if item.photo_path else "image_not_supported")),
                    ]
                )
            )
        page.update()

    # Subscribe to backend events via Observer pattern
    service.on(EventType.ITEM_ADDED, lambda et, d: refresh_table())
    service.on(EventType.ITEM_UPDATED, lambda et, d: refresh_table())
    service.on(EventType.ITEM_DELETED, lambda et, d: refresh_table())
    service.on(EventType.ITEM_MOVED, lambda et, d: refresh_table())
    service.on(EventType.ITEM_WRITTEN_OFF, lambda et, d: refresh_table())

    # ── Add Item Form ──
    inv_input = ft.TextField(label="Інвентарний номер", width=180)
    name_input = ft.TextField(label="Назва майна", width=250)
    
    # Category dropdown with backend categories
    categories = service.available_categories()
    category_dropdown = ft.Dropdown(
        label="Категорія",
        width=200,
        options=[ft.dropdown.Option(key=cat, text=CATEGORY_LABELS.get(cat, cat)) for cat in categories],
        value=categories[0] if categories else None,
    )
    
    cost_input = ft.TextField(label="Вартість (грн)", width=150, keyboard_type=ft.KeyboardType.NUMBER)
    location_input = ft.TextField(label="Локація", width=200)
    description_input = ft.TextField(label="Опис", width=300)

    # File picker for photo
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    photo_path_var = {"path": ""}

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            photo_path_var["path"] = e.files[0].path
            photo_label.value = f"Фото: {e.files[0].name}"
        else:
            photo_path_var["path"] = ""
            photo_label.value = "Без фото"
        photo_label.update()

    file_picker.on_result = on_file_picked

    photo_label = ft.Text("Без фото", size=14, color=ft.Colors.GREY_400)
    photo_btn = ft.ElevatedButton(
        "Прикріпити фото", 
        icon="upload_file", 
        on_click=lambda _: file_picker.pick_files(allow_multiple=False)
    )
    
    error_text = ft.Text("", color=ft.Colors.RED_400, size=14)

    def on_add_click(e):
        inv = inv_input.value
        name = name_input.value
        cat = category_dropdown.value
        cost_str = cost_input.value
        location = location_input.value
        description = description_input.value

        if not inv or not name or not cat or not cost_str:
            error_text.value = "Заповніть обов'язкові поля: номер, назва, категорія, вартість."
            page.update()
            return

        try:
            cost = float(cost_str)
        except ValueError:
            error_text.value = "Вартість повинна бути числом."
            page.update()
            return

        try:
            service.add_item(
                inventory_number=inv,
                name=name,
                category=cat,
                cost=cost,
                location=location or "",
                description=description or "",
                photo_path=photo_path_var["path"],
            )
            # Clear inputs on success
            inv_input.value = ""
            name_input.value = ""
            cost_input.value = ""
            location_input.value = ""
            description_input.value = ""
            photo_path_var["path"] = ""
            photo_label.value = "Без фото"
            error_text.value = ""
            page.update()
        except ValueError as ex:
            error_text.value = str(ex)
            page.update()

    add_form = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Додати нове майно", style=ft.TextThemeStyle.TITLE_LARGE),
                ft.Row([inv_input, name_input, category_dropdown], wrap=True),
                ft.Row([cost_input, location_input, description_input], wrap=True),
                ft.Row([photo_btn, photo_label], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                error_text,
                ft.ElevatedButton(
                    "Додати майно",
                    icon="add",
                    on_click=on_add_click,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO, color=ft.Colors.WHITE),
                ),
            ]),
        )
    )

    # Initial table population
    refresh_table()

    return ft.Column(
        controls=[
            ft.Text("Інвентар", style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            add_form,
            ft.Container(height=20),
            ft.ListView(controls=[table], expand=True),
        ],
        expand=True,
    )
