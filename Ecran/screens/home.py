# home.py
from .base import Screen, HEADER_HEIGHT, BLACK

class HomeScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Home")

    def render_body(self, draw, header_h: int):
        # Icône power en bas gauche
        x, y = self.get_position('ld', obj_size=(16, 16), margin=5)
        self.write_image(draw, x, y, "icons/power-btn.png", size=(16, 16))

        # Icône settings en bas droite
        x, y = self.get_position('rd', obj_size=(16, 16), margin=5)
        self.write_image(draw, x, y, "icons/settings-btn.png", size=(16, 16))

        # Texte centré au milieu
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
