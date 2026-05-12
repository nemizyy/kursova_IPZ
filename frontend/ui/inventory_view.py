import flet as ft
import os
from controllers.inventory_controller import InventoryController


def build_inventory_content(page: ft.Page, controller: InventoryController):
    """Builds and returns the inventory content (form + table)."""
    
    # Data Table
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Фото")),
            ft.DataColumn(ft.Text("Назва")),
            ft.DataColumn(ft.Text("Категорія")),
            ft.DataColumn(ft.Text("Кількість")),
        ],
        rows=[],
    )

    selected_photo_path = [None]
    selected_photo_text = ft.Text("Фото не вибрано", italic=True)

    def update_table():
        table.rows.clear()
        for item in controller.get_items():
            photo_cell = ft.Text("-")
            if item.photo_path and os.path.exists(item.photo_path):
                photo_cell = ft.Image(src=item.photo_path, width=50, height=50, fit=ft.BoxFit.COVER)

            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(item.item_id))),
                        ft.DataCell(photo_cell),
                        ft.DataCell(ft.Text(item.name)),
                        ft.DataCell(ft.Text(item.category)),
                        ft.DataCell(ft.Text(str(item.quantity))),
                    ]
                )
            )
        page.update()

    # Register observer to update table
    controller.add_observer(update_table)

    def on_file_picked(e):
        if e.files and len(e.files) > 0:
            selected_photo_path[0] = e.files[0].path
            selected_photo_text.value = f"Вибрано: {e.files[0].name}"
        else:
            selected_photo_path[0] = None
            selected_photo_text.value = "Фото не вибрано"
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    name_input = ft.TextField(label="Назва майна", width=300)
    category_input = ft.TextField(label="Категорія", width=200)
    quantity_input = ft.TextField(label="Кількість", width=100, keyboard_type=ft.KeyboardType.NUMBER)

    def on_add_click(e):
        name = name_input.value
        category = category_input.value
        quantity = quantity_input.value

        if not name or not category or not quantity:
            return

        try:
            quantity = int(quantity)
        except ValueError:
            return

        controller.add_item(name, category, quantity, selected_photo_path[0])

        # Clear inputs
        name_input.value = ""
        category_input.value = ""
        quantity_input.value = ""
        selected_photo_path[0] = None
        selected_photo_text.value = "Фото не вибрано"
        page.update()

    add_form = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Додати нове майно", style=ft.TextThemeStyle.TITLE_LARGE),
                ft.Row([name_input, category_input, quantity_input]),
                ft.Row([
                    ft.ElevatedButton(
                        "Вибрати фото",
                        icon="upload_file",
                        on_click=lambda _: file_picker.pick_files(allow_multiple=False),
                    ),
                    selected_photo_text,
                ]),
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
    update_table()

    return ft.Container(
        padding=30,
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Інвентар", style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                add_form,
                ft.Container(height=20),
                ft.ListView(controls=[table], expand=True),
            ],
            expand=True,
        ),
    )
