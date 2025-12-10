from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import time

GPIO_DC = 25
GPIO_RST = 24

# Style
PRIMARY_COLOR = (10, 14, 39)
SECONDARY_COLOR = (255, 255, 255)

class RubikGUI:
    def __init__(self):
        self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
        self.device = st7735(self.serial)
        self.running = True
        self.font_small = ImageFont.load_default()
        self.render_home_screen()
    
    def render_home_screen(self):
        img = Image.new('RGB', self.device.size, color=SECONDARY_COLOR)
        draw = ImageDraw.Draw(img)
        
        # En-tête
        draw.rectangle([(0, 0), (self.device.width, 20)], fill=PRIMARY_COLOR)
        draw.text((10, 4), "Home", fill=SECONDARY_COLOR, font=self.font_small)
        
        # HEURE HAUT DROITE
        now = datetime.now().strftime("%H:%M")
        bbox = draw.textbbox((0, 0), now, font=self.font_small)
        text_width = bbox[2] - bbox[0]
        draw.text((self.device.width - text_width - 5, 4), now, fill=SECONDARY_COLOR, font=self.font_small)
        
        self.device.display(img)

    def run(self):
        while self.running:
            time.sleep(0.1)
            self.render_home_screen()

if __name__ == "__main__":
    try:
        app = RubikGUI()
        app.run()
    except KeyboardInterrupt:
        pass