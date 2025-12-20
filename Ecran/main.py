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
        img = Image.new('RGB', self.device.size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Header
        header_height = 25
        draw.rectangle([(0, 0), (self.device.width, header_height)], fill=(10, 14, 39))
        
        # Home
        x, y = self.get_position('lu', margin=5)
        draw.text((x, y), "Home", fill=(255, 255, 255), font=self.font_small)

        # Heure
        now = datetime.now().strftime("%H:%M")
        bbox = draw.textbbox((0, 0), now, font=self.font_small)

        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x, y = self.get_position('ru', obj_size=(text_w, text_h), margin=5)
        draw.text((x, y), now, fill=(0, 200, 160), font=self.font_small)
        
        # POWER SYMBOL
        power_icon = Image.open('icons/power-btn.png').convert("RGBA")
        power_icon = power_icon.resize((16, 16))
        x, y = self.get_position('ld', obj_size=(16, 16), margin=5)
        img.paste(power_icon, (x, y), power_icon)
        
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
