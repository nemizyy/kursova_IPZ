import flet as ft

class SideBar(ft.NavigationRail):
    def __init__(self, on_nav_change, selected_index=0):
        super().__init__(
            selected_index=selected_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon="dashboard_outlined",
                    selected_icon="dashboard",
                    label="Дашборд",
                ),
                ft.NavigationRailDestination(
                    icon="inventory_2_outlined",
                    selected_icon="inventory_2",
                    label="Майно",
                ),
            ],
            on_change=on_nav_change,
        )
