from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image
import time

# Configuration SPI avec broches DC et RST adaptées
serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24)
device = st7735(serial)

# Charger le GIF animé
gif_path = "rotating-lamb-souvlaki.gif"  # Remplace par le chemin de ton GIF

try:
    # Boucle d'affichage infinie
    while True:
        gif = Image.open(gif_path)
        
        # Obtenir la durée de chaque frame
        try:
            duration = gif.info.get('duration', 100) / 1000.0  # Convertir en secondes
        except:
            duration = 0.1
        
        # Parcourir les frames du GIF
        frame_num = 0
        while True:
            try:
                gif.seek(frame_num)
                
                # Convertir et redimensionner la frame courante uniquement
                frame = gif.convert("RGB")
                frame = frame.resize((device.width, device.height), Image.LANCZOS)
                
                # Afficher
                device.display(frame)
                time.sleep(duration)
                
                frame_num += 1
                
            except EOFError:
                # Fin du GIF, recommencer
                break
                
except KeyboardInterrupt:
    print("\nArrêt demandé")
    device.clear()
except Exception as e:
    print(f"Erreur: {e}")
    device.clear()
