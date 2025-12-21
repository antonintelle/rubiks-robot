#!/usr/bin/python3
from screens.home import HomeScreen
from screens.debug import DebugScreen

import signal
import sys
import threading

from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time

import errno

GPIO_DC = 25
GPIO_RST = 24

class RubikGUI:
    def __init__(self):
        self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
        self.device = st7735(self.serial)
        self._stop_event = threading.Event()
        #self.font_small = ImageFont.load_default()
        self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=11)
        self.current_screen_name = "debug"
        self.screens = {
            "home":  HomeScreen(self),
            "debug": DebugScreen(self),
        }
    
    def signal_handler(self, sig, frame):
        """Gère SIGTERM de systemd"""
        print("Arrêt demandé (SIGTERM/SIGINT)...")
        # Arrête la boucle proprement
        self._stop_event.set()

    def set_screen(self, name: str):
        if name in self.screens:
            self.current_screen_name = name

    def render(self):
        screen = self.screens[self.current_screen_name]
        img = screen.render()
        self.device.display(img)

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

    def cleanup(self):
        """Nettoyage GPIO/écran"""
        print("Nettoyage LCD/GPIO...")
        try:
            self.device.clear()
        except:
            pass
        self.serial.cleanup()

    def run(self):
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            while not self._stop_event.is_set():
                time.sleep(0.1)
                self.render()
        finally:
            self.cleanup()

if __name__ == "__main__":
    app = None
    try:
        app = RubikGUI()
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        if app:
            app.cleanup()
