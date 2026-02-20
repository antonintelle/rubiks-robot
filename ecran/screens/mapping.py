from .base import Screen, HEADER_HEIGHT, BLACK

class MappingScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui)

    def render_body(self, draw, header_h: int):
        """Dessine avec feedback automatique"""

        WHITE = (255, 255, 255)
        RED = (200, 0, 0)
        BLUE = (0, 50, 200)
        ORANGE = (255, 100, 0)
        GREEN = (0, 200, 0)
        YELLOW = (255, 255, 0)
        BLACK = (0, 0, 0)

        face_size = 78
        x, y = 3, 2

        state = self.get_init_colors()

        self.draw_cube_pattern(draw, x, y, face_size, state["U"], state["L"], state["F"], state["R"], state["D"], state["B"])

        current_step = "c"

        draw.text((174, 7),  "Scan       : 01:05:14", font=self.gui.font_small,
                  fill= RED if "s" in current_step else BLACK)

        draw.text((174, 17),  "Calcul     : 00:02:34", font=self.gui.font_small,
                  fill= RED if "c" in current_step else BLACK)

        draw.text((174, 27),  "Résolution : --:--:--", font=self.gui.font_small,
                  fill= RED if "r" in current_step else BLACK)

        draw.text((174, 37),  "────────────", font=self.gui.font_small, fill=BLACK)
        draw.text((174, 47),  "Total      : 00:07:48", font=self.gui.font_small, fill=BLACK)


    def get_init_colors(self):
        """
        Simmule la récupération des couleurs depuis la caméra

        Returns
        -------
        dict
            DESCRIPTION.

        """
        WHITE = (255, 255, 255)
        RED = (200, 0, 0)
        BLUE = (0, 50, 200)
        ORANGE = (255, 100, 0)
        GREEN = (0, 200, 0)
        YELLOW = (255, 255, 0)
        BLACK = (0, 0, 0)

        return {
            "U" : (ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE, ORANGE),
            "D" : (RED, RED, RED, RED, RED, RED, RED, RED, RED),
            "F" : (GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN, GREEN),
            "B" : (BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE, BLUE),
            "L" : (YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW, YELLOW),
            "R" : (WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE),
            }
