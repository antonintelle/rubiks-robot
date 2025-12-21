from .base import Screen, HEADER_HEIGHT
import subprocess
import socket

class DebugScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Debug")
    
    def render_body(self):
        """Pygame text au lieu PIL draw.text [file:23]."""
        ssid = self.gui.net.get_wifi_ssid() or "No WiFi"
        ip = self.gui.net.get_wifi_ip() or "No IP"
        
        txt = self.font_small.render(f"SSID: {ssid}\nIP: {ip}", True, (255, 0, 0))
        
        pos1 = self.get_position('lu', txt.get_size())
        pos2 = (pos1[0], pos1[1] + 20)
        
        self.surface.blit(txt, (pos1[0], pos1[1] + HEADER_HEIGHT))
