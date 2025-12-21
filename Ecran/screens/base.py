# screens/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from PIL import Image, ImageDraw

HEADER_HEIGHT = 15

class Screen(ABC):
    def __init__(self, gui, title: str):
        self.gui = gui          # accès à device, font, get_position, etc.
        self.title = title

    def render(self):
        # fond + dessin générique
        img = Image.new('RGB', self.gui.device.size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # bandeau du haut
        draw.rectangle(
            [(0, 0), (self.gui.device.width, HEADER_HEIGHT)],
            fill=(10, 14, 39)
        )

        # titre
        x, y = self.gui.get_position('lu', margin=1)
        draw.text((x, y), self.title, fill=(255, 255, 255), font=self.gui.font_small)

        # heure
        now = datetime.now().strftime("%H:%M")
        bbox = draw.textbbox((0, 0), now, font=self.gui.font_small)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self.gui.get_position('ru', obj_size=(w, h), margin=1)
        draw.text((x, y), now, fill=(0, 200, 160), font=self.gui.font_small)

        # contenu spécifique de l’écran
        self.render_body(draw, HEADER_HEIGHT)

        return img

    @abstractmethod
    def render_body(self, draw: ImageDraw.ImageDraw, header_h: int):
        ...
