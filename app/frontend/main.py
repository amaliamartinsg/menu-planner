"""Flet entry point for PyPlanner frontend."""

import flet as ft


def main(page: ft.Page) -> None:
    """Initialize the PyPlanner application window."""
    page.title = "PyPlanner"
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.theme_mode = ft.ThemeMode.LIGHT

    page.add(
        ft.Column(
            controls=[
                ft.Text(
                    "PyPlanner",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Gestión de recetas y menús semanales",
                    size=16,
                    color=ft.colors.GREY_600,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
