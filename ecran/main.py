from screens.home import HomeScreen
from screens.mapping import MappingScreen
from screens.parameters import ParametersScreen
from screens.none import NoneScreen

from tools.network import NetworkTools
from tools.system import SystemTools

from hardware.touch import TouchHandler

import signal
import threading

from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from PIL import ImageFont

import time

GPIO_DC = 25
GPIO_RST = 24

class RubikGUI:
    def __init__(self):
        self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
        self.device = ili9341(self.serial)
        self._stop_event = threading.Event()
        
        self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=11)
        
        self.net = NetworkTools()
        self.sys = SystemTools()
        
        self.current_screen_name = "parameters"
        self.screens = {
            "home": HomeScreen(self),
            "debug": DebugScreen(self),
            "parameters": ParametersScreen(self),
            "none": NoneScreen(self),
        }
        
        # Init tactile avec callbacks séparés
        self.touch = TouchHandler(
            on_press=self.on_touch_press,
            on_release=self.on_touch_release,
            on_move=self.on_touch_move
        )
        self.touch.start()
    
    def on_touch_press(self, x, y):
        """Appelé au début du touch"""
        screen = self.screens[self.current_screen_name]
        if hasattr(screen, 'on_touch_press'):
            screen.on_touch_press(x, y)
    
    def on_touch_release(self, x, y):
        """Appelé au relâchement (x, y = dernière position)"""
        screen = self.screens[self.current_screen_name]
        if hasattr(screen, 'on_touch_release'):
            screen.on_touch_release(x, y)
    
    def on_touch_move(self, x, y):
        """Appelé pendant le mouvement"""
        screen = self.screens[self.current_screen_name]
        if hasattr(screen, 'on_touch_move'):
            screen.on_touch_move(x, y)
    
    def signal_handler(self, sig, frame):
        """Gère SIGTERM de systemd"""
        print("Arrêt demandé (SIGTERM/SIGINT)...")
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
        self.touch.cleanup()
        
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
