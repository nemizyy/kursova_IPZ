import flet as ft
from controllers.inventory_controller import InventoryController


def build_dashboard_content(controller: InventoryController):
    """Builds and returns the dashboard content (Column with stats cards)."""
    stats = controller.get_statistics()

    return ft.Container(
        padding=30,
        expand=True,
        content=ft.Column(
            controls=[
                ft.Text("Статистика", style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Icon("category", size=40, color=ft.Colors.BLUE_400),
                                    ft.Text("Категорій", size=16),
                                    ft.Text(str(stats["total_categories"]), size=30, weight=ft.FontWeight.BOLD),
                                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=200, height=150, padding=20,
                            )
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Icon("inventory", size=40, color=ft.Colors.GREEN_400),
                                    ft.Text("Унікальних об'єктів", size=16),
                                    ft.Text(str(stats["total_items"]), size=30, weight=ft.FontWeight.BOLD),
                                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=200, height=150, padding=20,
                            )
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Icon("format_list_numbered", size=40, color=ft.Colors.ORANGE_400),
                                    ft.Text("Загальна кількість", size=16),
                                    ft.Text(str(stats["total_quantity"]), size=30, weight=ft.FontWeight.BOLD),
                                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=200, height=150, padding=20,
                            )
                        ),
                    ],
                    spacing=20,
                ),
            ],
            expand=True,
        ),
    )
