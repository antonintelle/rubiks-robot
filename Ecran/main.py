#!/usr/bin/python3

import signal
import sys
import threading

from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time

import subprocess
import socket
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
        self.render_home_screen()
    
    def signal_handler(self, sig, frame):
        """Gère SIGTERM de systemd"""
        print("Arrêt demandé (SIGTERM/SIGINT)...")
        # Arrête la boucle proprement
        self._stop_event.set()

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
    
    def get_wifi_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Utilise la route par défaut (chez toi -> wlan0)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]  # ex: "192.168.1.122"
        except OSError:
            return None
        finally:
            s.close()

    def get_wifi_ssid(self) -> str | None:
        try:
            result = subprocess.run(
                ["iwgetid", "-r"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                # Pas connecté ou iwgetid indisponible
                return None
            ssid = result.stdout.strip()
            return ssid or None
        except FileNotFoundError:
            # iwgetid n'existe pas
            return None

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
        try:
        # POWER SYMBOL
            power_icon = Image.open('icons/power-btn.png').convert("RGBA")
            power_icon = power_icon.resize((16, 16))
            x, y = self.get_position('ld', obj_size=(16, 16), margin=5)
            img.paste(power_icon, (x, y), power_icon)
        finally:
            pass

        try:
            # SETTINGS
            settings_icon = Image.open('icons/settings-btn.png').convert("RGBA")
            settings_icon = settings_icon.resize((16, 16))
            x, y = self.get_position('rd', obj_size=(16, 16), margin=5)
            img.paste(settings_icon, (x, y), settings_icon)
        finally:
            pass
        
        # DEBUG
        ssid = self.get_wifi_ssid()
        txt = f"SSID: {ssid}" if ssid is not None else "SSID: /"

        ip = self.get_wifi_ip()
        txt += f"\nIP: {ip}" if ssid is not None else "IP: /"
        
        x, y = self.get_position('lu', margin=5)
        draw.text((x, y + header_height), txt, fill=(255, 0, 0), font=self.font_small)

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
                self.render_home_screen()
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
