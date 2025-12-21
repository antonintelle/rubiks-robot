from .base import Screen, HEADER_HEIGHT

import subprocess
import socket

class DebugScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Debug")

    def render_body(self, draw, header_h: int):
        ssid = self.gui.net.get_wifi_ssid()
        ip   = self.gui.net.get_wifi_ip()

        txt =  f"SSID: {ssid}" if ssid else "SSID: /"
        txt += f"\nIP:   {ip}"   if ip   else "IP:   /"

        x, y = self.get_position('lu', margin=5)
        draw.text((x, y + header_h), txt, fill=(255, 0, 0), font=self.gui.font_small)
