# ============================================================================
#  screen_tft.py
#  ----------------
#  Objectif :
#     Gérer l’affichage sur l’écran TFT 1.8" SPI (ST7735).
#     Affiche une animation GIF image par image en boucle.
#
#  Branchement matériel (CONSERVÉS + MIS AU PROPRE)
#  -------------------------------------------------
#  BRANCHEMENTS RÉELS UTILISÉS :
#
#   VCC   → 3.3V                → Fil rouge
#   LED   → 3.3V                → Fil rouge
#   GND   → GND                 → Fil noir
#
#   SCK   → SPISCLK (GPIO11)    → Fil blanc
#   SDA   → SPIMOSI (GPIO10)    → Fil bleu
#   CS    → SPICE0  (GPIO8)     → Fil jaune   (port 0, device 0)
#
#   A0    → GPIO17              → Fil vert    (DC : Data/Command)
#   RESET → GPIO27              → Fil violet  (RST)
#
#  Remarque importante :
#     Le code DOIT utiliser gpio_DC=17 et gpio_RST=27,
#     pour correspondre aux branchements réels ci-dessus.
#
#  Dépendances :
#     - luma.lcd
#     - Pillow (PIL)
#
# ============================================================================

from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageSequence
from luma.core.render import canvas
import time
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
from PIL import ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Configuration SPI + GPIO correspondant EXACTEMENT aux branchements réels
# ---------------------------------------------------------------------------
serial = spi(
    port=0,
    device=0,   # correspond à CS → GPIO8 / CE0
    gpio_DC=17, # tu as branché A0 (DC) sur GPIO17
    gpio_RST=27 # tu as branché RESET sur GPIO27
)

# Taille réelle de l'écran 1.8" ST7735
device = st7735(serial)

# ---------------------------------------------------------------------------
# Chargement du GIF
# ---------------------------------------------------------------------------
gif_path = "ecran/cube2.gif"  # Chemin vers ton GIF
gif = Image.open(gif_path)

# ---------------------------------------------------------------------------
# Boucle d’animation en continu
# ---------------------------------------------------------------------------

def display_gif(duration_seconds: int):
    """
    Affiche le GIF sur le TFT pendant `duration_seconds` secondes.
    """
    gif = Image.open(gif_path)
    start = time.time()

    while time.time() - start < duration_seconds:
        for frame in ImageSequence.Iterator(gif):
            if time.time() - start >= duration_seconds:
                break

            frame = frame.convert("RGB").resize((device.width, device.height))
            device.display(frame)

            delay = frame.info.get("duration", 100) / 1000.0
            time.sleep(delay)

    # Éteindre l'écran en noir à la fin
    device.display(Image.new("RGB", (device.width, device.height), "black"))

def display_text(message: str, duration_seconds: int = 5):
    """
    Affiche un texte centré sur le TFT pendant `duration_seconds` secondes.
    Compatible Pillow 10.
    """
    img = Image.new("RGB", (device.width, device.height), "black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Calcule bbox du texte (Pillow 10+)
    bbox = draw.textbbox((0, 0), message, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Centrage
    x = (device.width - w) // 2
    y = (device.height - h) // 2

    draw.text((x, y), message, font=font, fill="white")

    # Affiche
    device.display(img)

    # Attend la durée demandée
    time.sleep(duration_seconds)

    # Éteint l'écran (noir)
    device.display(Image.new("RGB", (device.width, device.height), "black"))


# ---------------------------------------------------------------------------
# MAIN — affichage par défaut 30 secondes
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🖥️ Démarrage test TFT pendant 30 secondes…")
    display_gif(30)
    print("✔️ Test TFT terminé.")
