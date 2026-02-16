from .base import Screen, HEADER_HEIGHT, BLACK

class HomeScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui)

        self.icons_size = (24, 24)

        # Calcul positions
        x_power, y_power = 5,187
        x_settings, y_settings = 265,187

        # Déclaration boutons (1 ligne chacun !)
        self.btn_power = self.add_button(
            rect=(x_power, y_power, x_power + 24, y_power + 24),
            on_click=lambda: self.gui.sys.shutdown()
        )

        self.btn_settings = self.add_button(
            rect=(x_settings, y_settings, x_settings + 24, y_settings + 24),
            on_click=lambda: self.gui.set_screen("parameters")
        )

    def render_body(self, draw, header_h: int):
        """Dessine avec feedback automatique"""

        if self.is_button_pressed(self.btn_power):
            draw.rectangle([
                (3, 185),
                (31, 213)
            ], fill=(255, 100, 100))

        draw.rounded_rectangle((5, 187, 55, 235), radius=3, fill=(24, 28, 32))
        self.write_image(draw, 22, 203, "icons/power.png")

        # Settings
        x_settings, y_settings = 265,187

        if self.is_button_pressed(self.btn_settings):
            draw.rectangle([
                (x_settings-2, y_settings-2),
                (x_settings+26, y_settings+26)
            ], fill=(100, 255, 100))

        draw.rounded_rectangle((265, 187, 315, 235), radius=3, fill=(24, 28, 32))
        self.write_image(draw, 282, 203, "icons/settings.png")

        # Texte
        self.write_text(
            draw,
            10, header_h + 5,
            self.gui.device.width - 50, header_h + 25,
            "Bienvenue sur RubikGUI",
            color=BLACK,
            size=11,
            align="left",
            line_spacing=2
        )
