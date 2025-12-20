#!/usr/bin/python3

from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time

GPIO_DC = 25
GPIO_RST = 24

class RubikGUI:
    def __init__(self):
        self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
        self.device = st7735(self.serial)
        self.running = True
        self.font_small = ImageFont.load_default()
        self.render_home_screen()
    
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
            else (self.device.width - obj_w)//2 if pos_h == 'c' \
            else self.device.width - margin - obj_w

        y = margin if pos_v == 'u' \
            else (self.device.height - obj_h)//2 if pos_v == 'c' \
            else self.device.height-margin - obj_h
        
        return (x, y)
    
    def render_home_screen(self):
        img = Image.new('RGB', self.device.size, color=SECONDARY_COLOR)
        draw = ImageDraw.Draw(img)
        
        # En-tête
        draw.rectangle([(0, 0), (self.device.width, 20)], fill=PRIMARY_COLOR)
        draw.text((10, 4), "Home", fill=SECONDARY_COLOR, font=self.font_small)
        
        # HEURE HAUT DROITE
        now = datetime.now().strftime("%H:%M")
        bbox = draw.textbbox((0, 0), now, font=self.font_small)
        text_width = bbox[2] - bbox[0]
        draw.text((self.device.width - text_width - 5, 4), now, fill=SECONDARY_COLOR, font=self.font_small)
        
        self.device.display(img)

    def run(self):
        while self.running:
            time.sleep(0.1)
            self.render_home_screen()

if __name__ == "__main__":
    try:
        app = RubikGUI()
        app.run()
    except KeyboardInterrupt:
        pass
