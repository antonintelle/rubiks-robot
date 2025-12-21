# screens/debug.py
from .base import Screen, HEADER_HEIGHT

import subprocess
import socket

class DebugScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Debug")

    def get_wifi_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Utilise la route par défaut
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
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

    def render_body(self, draw, header_h: int):
        ssid = self.get_wifi_ssid()
        ip   = self.get_wifi_ip()

        txt =  f"SSID: {ssid}" if ssid else "SSID: /"
        txt += f"\nIP:   {ip}"   if ip   else "IP:   /"

        x, y = self.gui.get_position('lu', margin=5)
        draw.text((x, y + header_h), txt, fill=(255, 0, 0), font=self.gui.font_small)
