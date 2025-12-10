from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont
import time

GPIO_DC = 25
GPIO_RST = 24

class RubikGUI:
    def __init__(self):
        self.serial = spi(port=0, device=0, gpio_DC=GPIO_DC, gpio_RST=GPIO_RST)
        self.device = st7735(self.serial)
        self.running = True
        self.font_small = ImageFont.load_default()
        self.render_home_screen()
    
    def render_home_screen(self):
        img = Image.new('RGB', self.device.size, color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # En-tête
        draw.rectangle([(0, 0), (self.device.width, 20)], fill=(0, 0, 0))
        draw.text((10, 4), "RUBIK", fill=(255, 255, 255), font=self.font_small)
        
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