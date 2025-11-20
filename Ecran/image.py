from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image

# Configuration SPI avec broches DC et RST adaptées
serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24)
device = st7735(serial)

# Charger une image locale et la redimensionner à la résolution 128x160 de l'écran
image_path = "cube.gif"  # Remplacez par le chemin de votre image
image = Image.open(image_path).convert("RGB")
image = image.resize((device.width, device.height))

# Afficher l'image sur l'écran
while True: 
    device.display(image)
