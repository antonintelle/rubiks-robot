# debug.py
from .base import Screen, HEADER_HEIGHT, BLACK

class DebugScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Debug")

    def render_body(self, draw, header_h: int):
        ssid = self.gui.net.get_wifi_ssid() or "/"
        ip = self.gui.net.get_wifi_ip() or "/"

        txt = f"SSID: {ssid}\nIP: {ip}"

        # zone texte sous le header
        self.write_text(
            draw,
            5, header_h + 5,
            self.gui.device.width - 5, self.gui.device.height - 5,
            txt,
            color=(255, 0, 0),
            font_path=None,
            size=11,
            align="left",
        )
