from abc import ABC, abstractmethod
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

HEADER_HEIGHT = 26
BLACK = (24, 28, 32)
WHITE = (255, 255, 255)
DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

class Button:
    """Bouton tactile déclaratif"""

    def __init__(self, rect, on_click=None, on_press=None, on_release=None):
        """
        Args:
            rect: (x1, y1, x2, y2) ou (x, y, width, height)
            on_click: Callback appelÃ© au clic validÃ© (press + release sur zone)
            on_press: Callback appelÃ© au press
            on_release: Callback appelÃ© au release (mÃªme si hors zone)
        """
        if len(rect) == 4:
            self.x1, self.y1, self.x2, self.y2 = rect
        else:
            raise ValueError("rect doit Ãªtre (x1, y1, x2, y2)")

        self.on_click = on_click
        self.on_press = on_press
        self.on_release = on_release
        self.is_pressed = False

    def contains(self, x, y):
        """VÃ©rifie si (x,y) est dans le bouton"""
        if x is None or y is None:
            return False
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def _handle_press(self, x, y):
        """GÃ¨re le press"""
        if self.contains(x, y):
            self.is_pressed = True
            if self.on_press:
                self.on_press()
            return True
        return False

    def _handle_release(self, x, y):
        """GÃ¨re le release"""
        was_pressed = self.is_pressed
        self.is_pressed = False

        if was_pressed:
            if self.on_release:
                self.on_release()

            # Clic validÃ© si release sur zone
            if self.contains(x, y) and self.on_click:
                self.on_click()
                return True

        return False

    def _handle_move(self, x, y):
        """GÃ¨re le move (annule si sort)"""
        if self.is_pressed and not self.contains(x, y):
            self.is_pressed = False


class Screen(ABC):
    def __init__(self, gui):
        self.gui = gui

        # Fonte par dÃ©faut
        self.default_font = self.gui.font_small

        # Gestion tactile
        self.buttons = []

    # ---------- GESTION TACTILE ----------

    def add_button(self, rect, on_click=None, on_press=None, on_release=None):
        """
        Ajoute un bouton dÃ©claratif

        Args:
            rect: (x1, y1, x2, y2)
            on_click: Callback au clic validÃ©
            on_press: Callback au press
            on_release: Callback au release

        Returns:
            Button instance (pour rÃ©fÃ©rence ultÃ©rieure)
        """
        btn = Button(rect, on_click, on_press, on_release)
        self.buttons.append(btn)
        return btn

    # Gestion automatique des callbacks tactiles

    def on_touch_press(self, x, y):
        """Dispatche aux boutons"""
        for btn in self.buttons:
            if btn._handle_press(x, y):
                break  # Un seul bouton Ã  la fois

    def on_touch_release(self, x, y):
        """Dispatche aux boutons"""
        for btn in self.buttons:
            btn._handle_release(x, y)

    def on_touch_move(self, x, y):
        """Dispatche aux boutons"""
        for btn in self.buttons:
            btn._handle_move(x, y)

    # Helper pour vÃ©rifier si bouton pressÃ© (pour rendering)

    def is_button_pressed(self, button):
        """Retourne True si le bouton est actuellement pressÃ©"""
        return button.is_pressed

    def is_point_in_rect(self, x, y, x1, y1, x2, y2):
        """
        VÃ©rifie si le point (x,y) est dans le rectangle [x1,y1,x2,y2]

        Returns:
            bool: True si dans le rectangle
        """
        if x is None or y is None:
            return False
        return x1 <= x <= x2 and y1 <= y <= y2

    # ---------- HELPERS DE DESSIN ----------

    def _get_font(self, font_path=None, size=11):
        """Retourne une fonte Pillow (ou la fonte par dÃ©faut)."""
        if font_path is None:
            return self.default_font
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            return self.default_font

    def write_text(self, draw: ImageDraw.ImageDraw,
                   x1: int, y1: int, x2: int, y2: int,
                   text: str, color=BLACK, font_path=None, size=11,
                   align: str = "left", line_spacing: int = 0):
        """
        Affiche du texte dans le rectangle [x1,y1,x2,y2].
        - align: 'left' (dÃ©faut), 'center', 'right'
        - line_spacing: pixels ajoutÃ©s entre deux lignes
        Dessine un cadre noir autour de la zone (debug).
        """
        font = self._get_font(font_path, size)

        max_width = x2 - x1
        lines = []

        # DÃ©coupe simple par mots
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
        """Affiche une image au point (x1,y1), optionnellement redimensionnÃ©e."""
        try:
            img = Image.open(path).convert("RGBA")
        except FileNotFoundError:
            return

        if size is not None:
            img = img.resize(size)

        draw._image.paste(img, (x1, y1), img)

    def draw_face(self, draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], colors: tuple[tuple[int, int, int], ...]):
        """
        Dessine une face de Rubik's Cube (grille 3x3) : fond noir + 9 carrés colorés.
        Args:
            draw: ImageDraw pour dessiner.
            rect: (x1, y1, x2, y2) du rectangle englobant.
            colors: Tuple de 9 tuples RGB (haut-gauche vers bas-droite).
        """
        x1, y1, x2, y2 = rect
        cell_w = (x2 - x1) // 3
        cell_h = (y2 - y1) // 3
        BLACK = (0, 0, 0)

        # Fond noir complet
        draw.rounded_rectangle([x1, y1, x2, y2], radius=2, fill=BLACK)

        # 9 carrés colorés par-dessus
        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                color = colors[idx]
                cell_x = x1 + i * cell_w + 1  # Petit décalage pour "jointure" noir
                cell_y = y1 + j * cell_h + 1
                cell_w_adj = cell_w - 2
                cell_h_adj = cell_h - 2

                draw.rounded_rectangle(
                    [cell_x, cell_y, cell_x + cell_w_adj, cell_y + cell_h_adj],
                    radius=2, fill=color
                )

    def draw_cube_pattern(self, draw: ImageDraw.ImageDraw, x: int, y: int, face_size: int,
                     U: tuple[tuple[int,int,int],...],  # Up
                     L: tuple[tuple[int,int,int],...],  # Left
                     F: tuple[tuple[int,int,int],...],  # Front
                     R: tuple[tuple[int,int,int],...],  # Right
                     D: tuple[tuple[int,int,int],...],  # Down
                     B: tuple[tuple[int,int,int],...]): # Back
        """
        Pattern Rubik's UFRBLD : U haut, LFRB centre, D bas.
        """
        # U (haut)
        self.draw_face(draw, (x + face_size, y, x + face_size*2, y + face_size), U)

        # L F R B (centre ligne)
        self.draw_face(draw, (x, y + face_size, x + face_size, y + face_size*2), L)
        self.draw_face(draw, (x + face_size, y + face_size, x + face_size*2, y + face_size*2), F)
        self.draw_face(draw, (x + face_size*2, y + face_size, x + face_size*3, y + face_size*2), R)
        self.draw_face(draw, (x + face_size*3, y + face_size, x + face_size*4, y + face_size*2), B)

        # D (bas)
        self.draw_face(draw, (x + face_size, y + face_size*2, x + face_size*2, y + face_size*3), D)

    def draw_touch_indicator(self, draw: ImageDraw.ImageDraw):
        """
        Dessine un indicateur visuel au point touchÃ© (debug)
        Appelez cette mÃ©thode dans render_body() pour debug tactile
        """
        x, y = self.last_touch
        if x is not None:
            # Croix rouge
            draw.line([(x-10, y), (x+10, y)], fill=(255, 0, 0), width=2)
            draw.line([(x, y-10), (x, y+10)], fill=(255, 0, 0), width=2)
            # Point central
            draw.ellipse([(x-3, y-3), (x+3, y+3)], fill=(255, 0, 0))

    # ---------- RENDU GLOBAL ----------

    def render(self):
        """Rendu complet de l'Ã©cran (header + body)"""
        # Fond blanc
        img = Image.new('RGB', self.gui.device.size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Contenu spÃ©cifique de l'Ã©cran
        self.render_body(draw, HEADER_HEIGHT)

        return img

    @abstractmethod
    def render_body(self, draw: ImageDraw.ImageDraw, header_h: int):
        """
        MÃ©thode abstraite Ã  implÃ©menter dans les Ã©crans enfants

        Args:
            draw: ImageDraw pour dessiner
            header_h: Hauteur du header (commencer Ã  y=header_h)
        """
        ...
