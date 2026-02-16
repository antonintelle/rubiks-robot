# home.py

from .base import Screen, HEADER_HEIGHT, BLACK

class MappingOldScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Mapping")

        # Bouton annuler
        self.btn_cancel = self.add_button(
            rect=(265, 187, 315, 235),
            on_click=lambda: self.gui.set_screen("home")
        )

    def render_body(self, draw, header_h: int):
        """Dessine avec feedback automatique"""

        WHITE = (255, 255, 255)
        RED = (200, 0, 0)
        BLUE = (0, 50, 200)
        ORANGE = (255, 100, 0)
        GREEN = (0, 200, 0)
        YELLOW = (255, 255, 0)

        face_size = 66
        x, y = 30, 35

        # Exemple état cube
        U = (ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE)
        D = (RED, RED, RED, RED, RED, RED, RED, RED, RED)
        F = (GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN)
        B = (BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE)
        L = (YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW)
        R = (WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE)

        self.draw_cube_pattern(draw, x, y, face_size, U, L, F, R, D, B)

        draw.rounded_rectangle((265, 187, 315, 235), radius=3, fill=BLACK)
        self.write_image(draw, 284, 203, "icons/crossed.png")
