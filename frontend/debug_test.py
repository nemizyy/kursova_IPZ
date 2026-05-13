import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear old log
with open(LOG, "w", encoding="utf-8") as f:
    f.write("")

log("=== START ===")

try:
    import flet as ft
    log("flet imported OK")
except Exception as e:
    log(f"flet import FAIL: {e}")
    sys.exit(1)

try:
    from backend import InventoryService, EventType, ItemCategory
    log("backend imported OK")
except Exception as e:
    log(f"backend import FAIL: {e}\n{traceback.format_exc()}")
    sys.exit(1)

try:
    from components.sidebar import SideBar
    from ui.dashboard_view import build_dashboard_content
    from ui.inventory_view import build_inventory_content
    log("UI components imported OK")
except Exception as e:
    log(f"UI import FAIL: {e}\n{traceback.format_exc()}")
    sys.exit(1)

def main(page: ft.Page):
    log("main() called!")
    try:
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed="indigo")
        page.title = "DEBUG TEST"
        page.padding = 0
        log("theme set OK")

        service = InventoryService()
        log(f"service created OK, items: {len(service.get_all_items())}")

        content_area = ft.Container(expand=True)
        log("content_area created OK")

        def navigate(index):
            log(f"navigate({index}) called")
            try:
                if index == 0:
                    content_area.content = build_dashboard_content(service)
                elif index == 1:
                    content_area.content = build_inventory_content(page, service)
                page.update()
                log(f"navigate({index}) OK")
            except Exception as e:
                log(f"navigate({index}) FAIL: {e}\n{traceback.format_exc()}")

        sidebar = SideBar(on_nav_change=lambda e: navigate(e.control.selected_index), selected_index=0)
        layout = ft.Row(controls=[sidebar, ft.VerticalDivider(width=1), content_area], expand=True)
        log("layout built OK")

        page.add(layout)
        log("page.add() OK")

        navigate(0)
        log("navigate(0) done")

    except Exception as e:
        log(f"main() EXCEPTION: {e}\n{traceback.format_exc()}")

log("Calling ft.run...")
ft.run(main)
log("ft.run returned")
