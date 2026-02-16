import os
import sys
import subprocess
import socket
import time
import termios
import fcntl
import select
import tty
from datetime import datetime
from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont

GPIO_DC = 25
GPIO_RST = 24

class RubikScreenOnly:  # ← NOM CORRECT
    def __init__(self):
        self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
        self.device = st7735(self.serial)
        self.running = True
        
        try:
            self.font_small = ImageFont.load_default()
        except:
            self.font_small = ImageFont.load_default()
        
        self.status_message = "READY"
        self.log_lines = ["System ready"]
        self.render_home_screen()
    
    def render_home_screen(self):
        img = Image.new('RGB', self.device.size, color=(10, 14, 39))
        draw = ImageDraw.Draw(img)
        
        # En-tête
        draw.rectangle([(0, 0), (self.device.width, 20)], fill=(20, 30, 60))
        draw.text((10, 4), "RUBIK", fill=(0, 200, 160), font=self.font_small)
        
        # Horloge
        now = datetime.now().strftime("%H:%M")
        bbox = draw.textbbox((0, 0), now, font=self.font_small)
        draw.text((self.device.width//2 - bbox[2]//2, 30), now, 
                 fill=(0, 200, 160), font=self.font_small)
        
        # Boutons
        buttons = [("RESOLVE", 55), ("WIFI", 70), ("INFO", 85), ("SHUTDOWN", 100)]
        for btn_text, y in buttons:
            draw.rectangle([(8, y), (120, y+13)], outline=(0, 200, 160), fill=(0, 40, 30))
            bbox = draw.textbbox((0, 0), btn_text, font=self.font_small)
            draw.text((self.device.width//2 - bbox[2]//2, y+3), btn_text, 
                     fill=(0, 200, 160), font=self.font_small)
        
        # Statut
        bbox = draw.textbbox((0, 0), self.status_message, font=self.font_small)
        draw.rectangle([(0, 135), (self.device.width, 158)], fill=(20, 30, 60))
        draw.text((self.device.width//2 - bbox[2]//2, 142), self.status_message, 
                 fill=(0, 200, 160), font=self.font_small)
        
        self.device.display(img)
    
    def render_status_screen(self, title, lines):
        img = Image.new('RGB', self.device.size, color=(10, 14, 39))
        draw = ImageDraw.Draw(img)
        
        # Titre
        draw.rectangle([(0, 0), (self.device.width, 25)], fill=(0, 40, 30))
        bbox = draw.textbbox((0, 0), title, font=self.font_small)
        draw.text((self.device.width//2 - bbox[2]//2, 8), title, 
                 fill=(0, 200, 160), font=self.font_small)
        
        # 4 lignes max
        for i, line in enumerate(lines[-4:]):
            y = 35 + i * 15
            bbox = draw.textbbox((0, 0), line[:15], font=self.font_small)  # Tronquer
            draw.text((5, y), line[:15], fill=(160, 200, 160), font=self.font_small)
        
        # Bouton BACK
        draw.rectangle([(8, 130), (120, 155)], outline=(160, 160, 160), fill=(0, 40, 30))
        draw.text((64, 138), "BACK", fill=(160, 160, 160), font=self.font_small)
        
        self.device.display(img)
    
    def action_resolve(self):
        self.status_message = "SOLVING..."
        self.render_home_screen()
        time.sleep(2)
        self.status_message = "READY"
        self.render_home_screen()
    
    def action_wifi(self):
        self.log_lines = ["Scanning..."]
        self.render_status_screen("WIFI", self.log_lines)
        time.sleep(1)
        
        try:
            result = subprocess.run(['nmcli', 'dev', 'wifi', 'list'], 
                                  capture_output=True, text=True, timeout=3)
            networks = []
            for line in result.stdout.strip().split('\n')[1:4]:
                if line.strip():
                    parts = line.split()
                    if len(parts) > 1:
                        ssid = parts[1][:12]
                        networks.append(ssid)
            self.log_lines = networks if networks else ["No networks"]
        except:
            self.log_lines = ["Scan error"]
        
        self.render_status_screen("WIFI", self.log_lines)
        time.sleep(3)
        self.render_home_screen()
    
    def action_info(self):
        info_lines = []
        try:
            ip = socket.gethostbyname(socket.gethostname())
            info_lines.append(f"IP:{ip[:8]}...")
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_c = int(f.read().strip()) / 1000
            info_lines.append(f"CPU:{int(temp_c)}C")
            info_lines.append("READY")
        except:
            info_lines = ["Error"]
        
        self.render_status_screen("INFO", info_lines)
        time.sleep(5)
        self.render_home_screen()
    
    def action_shutdown(self):
        try:
            flag_path = os.path.expanduser("~/Desktop/shutdown.flag")
            os.makedirs(os.path.dirname(flag_path), exist_ok=True)
            with open(flag_path, 'w') as f:
                f.write(f"Shutdown {datetime.now()}\n")
            self.status_message = "SHUTDOWN OK"
        except:
            self.status_message = "SHUTDOWN ERR"
        self.render_home_screen()
        time.sleep(3)
    
    def get_key(self):
        """Lecture touche IMMÉDIATE (sans ENTRÉE)"""
        fd = sys.stdin.fileno()
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        try:
            termios.tcsetattr(fd, termios.TCSANOW, newattr)
            tty.setcbreak(sys.stdin.fileno())
            if select.select([sys.stdin], [], [], 0.1)[0]:
                return sys.stdin.read(1)
        except:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        return None
    
    def run(self):
        while self.running:
            key = self.get_key()
            
            if key == '1':
                self.action_resolve()
            elif key == '2':
                self.action_wifi()
            elif key == '3':
                self.action_info()
            elif key == 's':
                self.action_shutdown()
            elif key == 'q':
                break
            
            time.sleep(0.1)
            self.render_home_screen()

if __name__ == "__main__":
    try:
        app = RubikScreenOnly()  # ← NOM CORRECT
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass
