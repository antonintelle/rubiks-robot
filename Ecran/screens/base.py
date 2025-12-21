from abc import ABC, abstractmethod
from datetime import datetime
from PIL import Image
import pygame

HEADER_HEIGHT = 15

class Screen(ABC):
    def __init__(self, gui, title: str):
        self.gui = gui
        self.title = title

        pygame.init()
        w, h = self.gui.device.width, self.gui.device.height
        self.surface = pygame.Surface((w, h))
        try:
            self.font_small = pygame.font.Font(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
            )
        except:
            self.font_small = pygame.font.Font(None, 11) 

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
        # fond + header, texte, etc.
        self.surface.fill((255, 255, 255))
        pygame.draw.rect(self.surface, (10, 14, 39),
                        (0, 0, self.gui.device.width, HEADER_HEIGHT))

        title_surf = self.font_small.render(self.title, True, (255, 255, 255))
        self.surface.blit(title_surf,
                        self.get_position('lu', title_surf.get_size(), margin=1))

        from datetime import datetime
        now = datetime.now().strftime("%H:%M")
        time_surf = self.font_small.render(now, True, (0, 200, 160))
        self.surface.blit(time_surf,
                        self.get_position('ru', time_surf.get_size(), margin=1))

        # contenu spécifique de l’écran (Home, Debug, etc.)
        self.render_body()

        # conversion surface → PIL pour Luma
        w, h = self.gui.device.width, self.gui.device.height
        data = pygame.image.tostring(self.surface, "RGB")
        img = Image.frombytes("RGB", (w, h), data)
        if img.mode != self.gui.device.mode:
            img = img.convert(self.gui.device.mode)
        return img

    @abstractmethod
    def render_body(self):
        ...
