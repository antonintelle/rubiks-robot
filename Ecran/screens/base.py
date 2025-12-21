# base.py
from abc import ABC, abstractmethod
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

HEADER_HEIGHT = 15
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

class Screen(ABC):
    def __init__(self, gui, title: str):
        self.gui = gui
        self.title = title
        # fonte par défaut (Pillow)
        self.default_font = self.gui.font_small  # déjà créé dans RubikGUI [file:24]

    # ---------- POSITION ----------
    def get_position(self, pos: str, obj_size: tuple=(0,0), margin: int=5) -> tuple:
        if len(pos) != 2:
            raise ValueError("pos doit avoir 2 caractères (ex: 'lr', 'dc')")
        
        pos_h, pos_v = pos.lower()
        obj_w, obj_h = obj_size

        x = margin if pos_h == 'l' \
            else (self.gui.device.width - obj_w)//2 if pos_h == 'c' \
            else self.gui.device.width - margin - obj_w

        y = margin if pos_v == 'u' \
            else (self.gui.device.height - obj_h)//2 if pos_v == 'c' \
            else self.gui.device.height - margin - obj_h
        return (x, y)

    # ---------- HELPERS DE DESSIN ----------

    def _get_font(self, font_path=None, size=11):
        """Retourne une fonte Pillow (ou la fonte par défaut)."""
        if font_path is None:
            return self.default_font
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            return self.default_font

    def set_title(self, draw: ImageDraw.ImageDraw, text: str,
                  color=WHITE, font_path=None, size=11):
        """Change le titre affiché dans la barre haute."""
        self.title = text
        font = self._get_font(font_path, size)
        # Fond bandeau
        draw.rectangle(
            [(0, 0), (self.gui.device.width, HEADER_HEIGHT)],
            fill=(10, 14, 39)
        )
        # Titre
        x, y = self.get_position('lu', margin=1)
        draw.text((x, y), self.title, fill=color, font=font)

    def write_text(self, draw: ImageDraw.ImageDraw,
               x1: int, y1: int, x2: int, y2: int,
               text: str, color=BLACK, font_path=None, size=11,
               align: str = "left", line_spacing: int = 0):
        """
        Affiche du texte dans le rectangle [x1,y1,x2,y2].
        - align: 'left' (défaut), 'center', 'right'
        - line_spacing: pixels ajoutés entre deux lignes
        Dessine un cadre noir autour de la zone (debug).
        """
        font = self._get_font(font_path, size)

        # DEBUG : rectangle de la zone
        draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 0, 0), width=1)

        max_width = x2 - x1
        lines = []

        # Découpe simple par mots
        for paragraph in text.split("\n"):
            words = paragraph.split(" ")
            current = ""
            for w in words:
                test = (current + " " + w).strip()
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = w
            if current:
                lines.append(current)

        # Dessin ligne par ligne
        y = y1
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            if y + h > y2:
                break  # plus de place

            if align == "center":
                x = x1 + (max_width - w)//2
            elif align == "right":
                x = x2 - w
            else:  # 'left'
                x = x1

            draw.text((x, y), line, fill=color, font=font)
            y += h + line_spacing

    def write_image(self, draw: ImageDraw.ImageDraw,
                    x1: int, y1: int, path: str, size: tuple=None):
        """Affiche une image au point (x1,y1), optionnellement redimensionnée."""
        try:
            img = Image.open(path).convert("RGBA")
        except FileNotFoundError:
            return

        if size is not None:
            img = img.resize(size)

        draw._image.paste(img, (x1, y1), img)

    # ---------- RENDU GLOBAL ----------

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

        # contenu spécifique
        self.render_body(draw, HEADER_HEIGHT)

        return img

    @abstractmethod
    def render_body(self, draw: ImageDraw.ImageDraw, header_h: int):
        ...
