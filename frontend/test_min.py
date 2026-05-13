import flet as ft

def main(page: ft.Page):
    page.title = "Minimal Test"
    page.add(ft.Text("Hello World!", size=30, color=ft.Colors.WHITE))
    print("Page added!")

ft.run(main)
