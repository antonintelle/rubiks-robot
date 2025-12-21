import socket
import subprocess

class NetworkTools:
    def __init__(self, wifi_iface: str = "wlan0"):
        self.wifi_iface = wifi_iface

    def get_wifi_ip(self) -> str | None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
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
                return None
            ssid = result.stdout.strip()
            return ssid or None
        except FileNotFoundError:
            return None
