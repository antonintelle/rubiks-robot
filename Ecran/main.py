from screens.home import HomeScreen
from screens.debug import DebugScreen

from tools.network import NetworkTools
from tools.system import SystemTools

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
        
        self.net = NetworkTools()
        self.sys = SystemTools()
        
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
