from .base import Screen, HEADER_HEIGHT
from PIL import Image

class HomeScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Home")

    def render_body(self, draw, header_h: int):
        # icônes
        try:
            power_icon = Image.open('icons/power-btn.png').convert("RGBA").resize((16, 16))
            x, y = self.get_position('ld', obj_size=(16, 16), margin=5)
            draw._image.paste(power_icon, (x, y), power_icon)
        except FileNotFoundError:
            pass

        try:
            settings_icon = Image.open('icons/settings-btn.png').convert("RGBA").resize((16, 16))
            x, y = self.get_position('rd', obj_size=(16, 16), margin=5)
            draw._image.paste(settings_icon, (x, y), settings_icon)
        except FileNotFoundError:
            pass
