

##
## BRANCHEMENT
# VCC   → 3.3V → Fil rouge
# GND   → GND → Fil noir
# SCK   → SPISCLK (GPIO11) → Fil blanc
# SDA   → SPIMOSI (GPIO10) → Fil bleu
# CS    → SPICE0  (GPIO8) → Fil jaune
# A0    → GPIO17 (au choix) → Fil vert
# RESET → GPIO27 (au choix) → Fil violet
# LED   → 3.3V → Fil rouge
##

from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageSequence
import time

# Configuration SPI et écran
serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24)
device = st7735(serial)

# Chargement du GIF animé
gif_path = "lamb.gif"  # Remplacer par le chemin vers votre GIF
gif = Image.open(gif_path)

# Boucle pour afficher toutes les frames du GIF en continu
while True:
    for frame in ImageSequence.Iterator(gif):
        # Convertir la frame au format RGB et redimensionner
        frame = frame.convert("RGB").resize((device.width, device.height))
        
        # Afficher la frame
        device.display(frame)
        
        # Pause selon le temps d'affichage de l'image (en ms)
        delay = frame.info.get('duration', 100) / 1000.0  # Durée par défaut 100 ms
        time.sleep(delay)
