# pyrefly: ignore [missing-import]
import flet as ft
from controllers.inventory_controller import InventoryController
from components.sidebar import SideBar
from ui.dashboard_view import build_dashboard_content
from ui.inventory_view import build_inventory_content


def main(page: ft.Page):
    # Theme configuration
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="indigo")

    page.title = "Система обліку майна"
    page.padding = 0

    controller = InventoryController()

    # Content area that gets swapped on navigation
    content_area = ft.Container(expand=True)

    def navigate(index):
        """Switch the content area based on selected nav index."""
        if index == 0:
            content_area.content = build_dashboard_content(controller)
        elif index == 1:
            content_area.content = build_inventory_content(page, controller)
        page.update()

    def on_nav_change(e):
        navigate(e.control.selected_index)

    sidebar = SideBar(on_nav_change=on_nav_change, selected_index=0)

    # Build the main layout: sidebar + divider + content area
    layout = ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1),
            content_area,
        ],
        expand=True,
    )

    # Add layout to page and show dashboard
    page.add(layout)
    navigate(0)


if __name__ == "__main__":
    ft.run(main)
