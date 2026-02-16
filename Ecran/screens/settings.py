# Généré automatiquement par lopaka_luma
from .base import Screen, HEADER_HEIGHT, BLACK, WHITE

GRAY = (65, 64, 65)
GREEN = (74, 182, 32)
BLUE = (0, 76, 205)
PURPLE = (98, 56, 180)
ORANGE = (255, 129, 0)

class SettingsScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Settings")

        # Bouton option 1
        self.btn_1 = self.add_button(
            rect=(11, 31, 256, 79),
            on_click=lambda: self.gui.set_screen("none")
        )

        # Bouton option 2
        self.btn_2 = self.add_button(
            rect=(11, 82, 256, 130),
            on_click=lambda: print("Browse toward option 2")
        )

        # Bouton option 3
        self.btn_3 = self.add_button(
            rect=(11, 133, 256, 181),
            on_click=lambda: print("Browse toward option 3")
        )

        # Bouton option 4
        self.btn_4 = self.add_button(
            rect=(11, 184, 256, 232),
            on_click=lambda: print("Browse toward option 4")
        )

        # Bouton haut
        self.btn_up = self.add_button(
            rect=(270, 85, 312, 127),
            on_click=lambda: print("Browse up")
        )

        # Bouton bas
        self.btn_down = self.add_button(
            rect=(270, 136, 312, 178),
            on_click=lambda: print("Browse down")
        )

        # Bouton retour
        self.btn_back = self.add_button(
            rect=(270, 187, 312, 229),
            on_click=lambda: self.gui.set_screen("home")
        )

    def render_body(self, draw, header_h: int):
        """Rendu du corps de l'écran"""

        # Section princiaple
        draw.rounded_rectangle((5, 30, 264, 234), radius=3, fill=BLACK)
        # Option 1
        draw.rounded_rectangle((16, 35, 56, 75), radius=3, fill=GREEN)
        self.write_image(draw, 20, 39, "icons/wifi_logo.png")
        draw.text((68, 41), "Wi-Fi", fill=WHITE, font=self.gui.font_small)
        draw.text((240, 48), ">", fill=GRAY, font=self.gui.font_small)
        if self.is_button_pressed(self.btn_1):
            draw.rounded_rectangle((11, 31, 256, 79), radius=6, outline=WHITE, width=1)
        draw.line((68, 80, 245, 80), fill=GRAY, width=1)

        # Option 2
        draw.rounded_rectangle((16, 86, 56, 126), radius=3, fill=BLUE)
        self.write_image(draw, 19, 90, "icons/bt_logo.png")
        draw.text((68, 92), "Bluetooth", fill=WHITE, font=self.gui.font_small)
        draw.text((240, 99), ">", fill=GRAY, font=self.gui.font_small)
        if self.is_button_pressed(self.btn_2):
            draw.rounded_rectangle((11, 82, 256, 130), radius=6, outline=WHITE, width=1)
        draw.line((68, 131, 245, 131), fill=GRAY, width=1)

        # Option 3
        draw.rounded_rectangle((16, 137, 56, 177), radius=3, fill=PURPLE)
        self.write_image(draw, 20, 141, "icons/nrf_logo.png")
        draw.text((68, 143), "NRF24", fill=WHITE, font=self.gui.font_small)
        draw.text((240, 150), ">", fill=GRAY, font=self.gui.font_small)
        if self.is_button_pressed(self.btn_3):
            draw.rounded_rectangle((11, 133, 256, 181), radius=6, outline=WHITE, width=1)
        draw.line((68, 182, 245, 182), fill=GRAY, width=1)

        # Option 4
        draw.rounded_rectangle((16, 188, 56, 228), radius=3, fill=ORANGE)
        self.write_image(draw, 20, 192, "icons/subhz_logo.png")
        draw.text((69, 194), "SubHZ", fill=WHITE, font=self.gui.font_small)
        draw.text((240, 201), ">", fill=GRAY, font=self.gui.font_small)
        if self.is_button_pressed(self.btn_4):
            draw.rounded_rectangle((11, 184, 256, 232), radius=6, outline=WHITE, width=1)

        # Section numéro de page
        draw.rounded_rectangle((267, 30, 315, 79), radius=3, fill=BLACK)
        draw.text((283, 49), "1/3", fill=WHITE, font=self.gui.font_small)

        # Section navigation
        draw.rounded_rectangle((267, 81, 315, 233), radius=3, fill=BLACK)
        # Haut
        self.write_image(draw, 283, 101, "icons/up_arrow.png")
        if self.is_button_pressed(self.btn_up):
            draw.rounded_rectangle((270, 85, 312, 127), radius=6, outline=WHITE, width=1)
        draw.line((285, 131, 297, 131), fill=GRAY, width=1)

        # Bas
        self.write_image(draw, 283, 152, "icons/down_arrow.png")
        if self.is_button_pressed(self.btn_down):
            draw.rounded_rectangle((270, 136, 312, 178), radius=6, outline=WHITE, width=1)
        draw.line((285, 182, 297, 182), fill=GRAY, width=1)

        # Retour
        self.write_image(draw, 283, 203, "icons/back.png")
        if self.is_button_pressed(self.btn_back):
            draw.rounded_rectangle((270, 187, 312, 229), radius=6, outline=WHITE, width=1)
