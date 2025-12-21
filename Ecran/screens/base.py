from abc import ABC, abstractmethod
from datetime import datetime
from PIL import Image, ImageDraw

HEADER_HEIGHT = 15

class Screen(ABC):
    def __init__(self, gui, title: str):
        self.gui = gui          # accès à device, font, get_position, etc.
        self.title = title

    def get_position(self, pos :str, obj_size: tuple=(0,0), margin: int=5) -> tuple:
        """
        Donne la position d'un objet sur l'écran.
        
        Args:
            pos: String 2 caractères [l/r/c][u/d/c]
                - 1er char: 'l'=left, 'r'=right, 'c'=center (horizontal)
                - 2e char: 'u'=up, 'd'=down, 'c'=center (vertical)
            obj_size: Taille de l'objet (pour ajuster x et y)
            margin: Marge depuis les bords
        
        Returns:
            (x, y) - Coin supérieur gauche de l'objet
        """
        if len(pos) != 2:
            raise ValueError("pos doit avoir 2 caractères (ex: 'lr', 'dc')")
        
        pos_h, pos_v = pos.lower()
        obj_w, obj_h = obj_size

        x = margin if pos_h == 'l' \
            else (self.gui.device.width - obj_w)//2 if pos_h == 'c' \
            else self.gui.device.width - margin - obj_w

        y = margin if pos_v == 'u' \
            else (self.gui.device.height - obj_h)//2 if pos_v == 'c' \
            else self.gui.device.height-margin - obj_h
        
        return (x, y)

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
        x, y = self.get_position('lu', margin=1)
        draw.text((x, y), self.title, fill=(255, 255, 255), font=self.gui.font_small)

        # heure
        now = datetime.now().strftime("%H:%M")
        bbox = draw.textbbox((0, 0), now, font=self.gui.font_small)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self.get_position('ru', obj_size=(w, h), margin=1)
        draw.text((x, y), now, fill=(0, 200, 160), font=self.gui.font_small)

        # contenu spécifique de l’écran
        self.render_body(draw, HEADER_HEIGHT)

        return img

    @abstractmethod
    def render_body(self, draw: ImageDraw.ImageDraw, header_h: int):
        ...
