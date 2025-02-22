import flet as ft
import asyncio
from utils import fetch_rendered_html
import logging


logging.basicConfig(level=logging.INFO)


def main(page: ft.Page):
    page.title = "MultiLoad"

    target_website_url = ft.TextField(
        helper_text="Add an URL",
        expand=True,
    )

    def fetcher_button_pressed(e):
        url = target_website_url.value
        if url and "https:/" in url:
            pass

    website_fetcher_button = ft.Button(
        text="Download source HTML",
        height=50,
        width=200,
        on_click=fetcher_button_pressed,
    )

    find_links_button = ft.Button(
        text="Find links",
        height=50,
        width=200,
    )

    simultaneus_downloads_option_text = ft.Text(
        "Simultaneus downloads",
        size=18,
        text_align=ft.TextAlign.CENTER,
    )

    simultaneus_downloads_option_slider = ft.Slider(
        value=4, max=10, min=1, divisions=10, label="Selected: {value}"
    )

    settings_option_container = ft.Container(
        ft.Column(
            [simultaneus_downloads_option_text, simultaneus_downloads_option_slider],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.BLUE_GREY_800,
        alignment=ft.alignment.center,
        border_radius=10,
        padding=30,
        margin=10,
    )

    def nav_bar_change(e):
        index = e.control.selected_index
        if index == 0:
            page.go("/")
        elif index == 1:
            page.go("/download")
        elif index == 2:
            page.go("/settings")

    main_nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME_ROUNDED,
                label="Home",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.DOWNLOAD_OUTLINED,
                selected_icon=ft.Icons.DOWNLOAD_ROUNDED,
                label="Download",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS_ROUNDED,
                label="Settings",
            ),
        ],
        on_change=nav_bar_change,
    )

    def switch_route(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.SafeArea(
                            ft.Container(
                                ft.Column(
                                    [target_website_url, website_fetcher_button],
                                    spacing=40,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                bgcolor=ft.Colors.BLUE_GREY_800,
                                alignment=ft.alignment.center,
                                border_radius=20,
                                padding=30,
                                margin=10,
                            ),
                        ),
                    ],
                    navigation_bar=main_nav_bar,
                )
            )
        elif page.route == "/download":
            page.views.append(
                ft.View(
                    "/download",
                    [
                        ft.SafeArea(
                            ft.Container(
                                ft.Column(
                                    [find_links_button],
                                    spacing=40,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                bgcolor=ft.Colors.BLUE_GREY_800,
                                alignment=ft.alignment.center,
                                border_radius=20,
                                padding=30,
                                margin=10,
                            ),
                        ),
                    ],
                    navigation_bar=main_nav_bar,
                )
            )
        elif page.route == "/settings":
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.SafeArea(
                            ft.Container(
                                ft.Column(
                                    [settings_option_container],
                                    spacing=40,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                bgcolor=ft.Colors.BLUE_GREY_900,
                                alignment=ft.alignment.center,
                                border_radius=20,
                                padding=10,
                                margin=10,
                            ),
                        ),
                    ],
                    navigation_bar=main_nav_bar,
                )
            )

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = switch_route
    page.on_view_pop = view_pop
    page.go(page.route)


ft.app(main, assets_dir="assets")
