# system_tools.py
import socket
import subprocess
import os
import platform
import psutil   # pip install psutil [web:366][web:370]

class SystemTools:
    def __init__(self, wifi_iface: str = "wlan0"):
        self.wifi_iface = wifi_iface

    # --- Réseau ---

    def get_wifi_ip(self) -> str | None:
        """IP utilisée pour sortir sur le réseau."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError:
            return None
        finally:
            s.close()

    def get_wifi_ssid(self) -> str | None:
        """SSID courant (Linux, via iwgetid)."""
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

    # --- SSH / utilisateurs ---

    def get_logged_users(self):
        """Liste des utilisateurs connectés (souvent via SSH sur une Pi)."""
        return psutil.users()  # renvoie une liste de namedtuple (name, host, terminal, ...) [web:366][web:370]

    def has_ssh_connection(self) -> bool:
        """Vrai si au moins une session distante est ouverte."""
        return any(u.host for u in psutil.users())  # host non vide => connexion distante (souvent SSH) [web:366][web:370]

    # --- Gestion de la machine ---

    def shutdown(self):
        """Éteint proprement la Raspberry Pi."""
        if platform.system() == "Linux":
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        elif platform.system() == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "1"])
        else:
            subprocess.run(["shutdown", "-h", "now"])
