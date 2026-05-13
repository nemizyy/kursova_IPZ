import flet as ft
from backend import InventoryService, ItemStatus


def build_dashboard_content(service: InventoryService):
    """Builds and returns the dashboard content with real stats from the DB."""
    items = service.get_all_items()
    
    total_items = len(items)
    total_cost = sum(item.cost for item in items)
    categories = set(item.category for item in items)
    active_items = sum(1 for item in items if item.status == ItemStatus.ACTIVE)
    written_off = sum(1 for item in items if item.status == ItemStatus.WRITTEN_OFF)

    return ft.Column(
        controls=[
            ft.Text("Дашборд — Статистика", style=ft.TextThemeStyle.HEADLINE_MEDIUM, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row(
                controls=[
                    _stat_card("category", ft.Colors.BLUE_400, "Категорій", str(len(categories))),
                    _stat_card("inventory", ft.Colors.GREEN_400, "Всього об'єктів", str(total_items)),
                    _stat_card("check_circle", ft.Colors.TEAL_400, "Активних", str(active_items)),
                    _stat_card("delete_outline", ft.Colors.RED_400, "Списано", str(written_off)),
                ],
                spacing=20,
                wrap=True,
            ),
            ft.Container(height=20),
            ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text("Загальна вартість майна", size=16),
                        ft.Text(f"{total_cost:,.2f} грн", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                    ]),
                )
            ),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )


def _stat_card(icon_name: str, color, label: str, value: str):
    """Helper to build a stat card."""
    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Icon(icon_name, size=40, color=color),
                ft.Text(label, size=14),
                ft.Text(value, size=30, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=180, height=140, padding=20,
        )
    )
