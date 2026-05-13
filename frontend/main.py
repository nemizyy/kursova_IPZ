# pyrefly: ignore [missing-import]
import sys
import os

# Add project root to path so we can import backend package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
from backend import InventoryService, EventType, ItemCategory
from components.sidebar import SideBar
from ui.dashboard_view import build_dashboard_content
from ui.inventory_view import build_inventory_content


def main(page: ft.Page):
    # Theme configuration
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="indigo")

    page.title = "Система обліку майна"
    page.padding = 0

    # Initialize the backend service
    service = InventoryService()

    # Create a wrapper for content
    content_area = ft.Container(expand=True, padding=20)

    def navigate(index):
        if index == 0:
            content_area.content = build_dashboard_content(service)
        elif index == 1:
            content_area.content = build_inventory_content(page, service)
        page.update()

    def on_nav_change(e):
        navigate(e.control.selected_index)

    sidebar = SideBar(on_nav_change=on_nav_change, selected_index=0)

    page.add(
        ft.Row(
            controls=[
                sidebar,
                ft.VerticalDivider(width=1),
                content_area,
            ],
            expand=True,
        )
    )

    navigate(0)


if __name__ == "__main__":
    ft.run(main)
