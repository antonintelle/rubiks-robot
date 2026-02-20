from .base import Screen, HEADER_HEIGHT, BLACK

class DebugScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui)

        # Bouton retour en bas gauche (même position que power dans home)
        x, y = 5,187
        self.btn_back = self.add_button(
            rect=(x, y, x + 60, y + 30),
            on_click=lambda: self.gui.set_screen("home")
        )

    def render_body(self, draw, header_h: int):
        """Affiche les infos de debug"""

        # Grille de fond
        for i in range(0, 320, 40):
            draw.line([(i, 30), (i, 230)], fill=(230, 230, 230))
        for i in range(0, 240, 40):
            draw.line([(0, i), (320, i)], fill=(230, 230, 230))

        y_offset = header_h + 10

        # Info réseau
        try:
            ip = self.gui.net.get_wifi_ip()
        except:
            ip = "N/A"
        draw.text((10, y_offset), f"IP: {ip}",
                  fill=BLACK, font=self.gui.font_small)
        y_offset += 20

        # CPU (simulé pour l'instant)
        draw.text((10, y_offset), f"CPU: Simulé",
                  fill=BLACK, font=self.gui.font_small)
        y_offset += 20

        # Touch handler status
        touch_pos = self.gui.touch.get_touch()
        if touch_pos[0] is not None:
            draw.text((10, y_offset), f"Touch: ({touch_pos[0]}, {touch_pos[1]})",
                      fill=(0, 200, 0), font=self.gui.font_small)

            # Croix rouge au point touché
            x, y = touch_pos
            draw.line([(x-10, y), (x+10, y)], fill=(255, 0, 0), width=2)
            draw.line([(x, y-10), (x, y+10)], fill=(255, 0, 0), width=2)
            draw.ellipse([(x-3, y-3), (x+3, y+3)], fill=(255, 0, 0))
        else:
            draw.text((10, y_offset), "Touch: -",
                      fill=(100, 100, 100), font=self.gui.font_small)

        # Bouton Retour (bas gauche)
        x, y = 5,187

        # Fond si pressé
        if self.is_button_pressed(self.btn_back):
            draw.rectangle([
                (x, y), (x + 60, y + 30)
            ], fill=(200, 200, 200), outline=BLACK, width=2)
        else:
            draw.rectangle([
                (x, y), (x + 60, y + 30)
            ], fill=(255, 255, 255), outline=BLACK, width=2)

        # Texte centré
        bbox = draw.textbbox((0, 0), "Retour", font=self.gui.font_small)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = x + (60 - text_w) // 2
        text_y = y + (30 - text_h) // 2
        draw.text((text_x, text_y), "Retour", fill=BLACK, font=self.gui.font_small)
