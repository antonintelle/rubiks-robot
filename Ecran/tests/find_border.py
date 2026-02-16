#!/usr/bin/env python3
"""
Calibration intelligente - Détecte automatiquement les coins
Explorez l'écran avec le stylet, les limites se mettent à jour automatiquement
"""
import RPi.GPIO as GPIO
import time
import signal
from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from PIL import Image, ImageDraw, ImageFont

# Config GPIO
DC, RST, IRQ, CS, CLK, MOSI, MISO = 25, 24, 17, 27, 18, 23, 19

stop, device = False, None

# Limites dynamiques (initialisées à l'inverse)
bounds = {
    'x_min': 4095,
    'x_max': 0,
    'y_min': 4095,
    'y_max': 0,
    'samples': 0
}

def signal_handler(s, f):
    global stop
    stop = True

def spi_rw(data):
    result = []
    for byte in data:
        recv = 0
        for _ in range(8):
            GPIO.output(MOSI, byte & 0x80)
            byte <<= 1
            time.sleep(0.00001)
            GPIO.output(CLK, GPIO.HIGH)
            time.sleep(0.00001)
            recv = (recv << 1) | GPIO.input(MISO)
            GPIO.output(CLK, GPIO.LOW)
            time.sleep(0.00001)
        result.append(recv)
    return result

def read_xy_raw():
    GPIO.output(CS, GPIO.LOW)
    time.sleep(0.0001)
    x = ((spi_rw([0x90,0,0])[1] << 8) | spi_rw([0x90,0,0])[2]) >> 3
    y = ((spi_rw([0xD0,0,0])[1] << 8) | spi_rw([0xD0,0,0])[2]) >> 3
    GPIO.output(CS, GPIO.HIGH)
    return x if 100 < x < 4000 else None, y if 100 < y < 4000 else None

def update_bounds(x_raw, y_raw):
    """Met à jour les limites si nouveau record"""
    updated = False
    
    if x_raw < bounds['x_min']:
        bounds['x_min'] = x_raw
        updated = True
    if x_raw > bounds['x_max']:
        bounds['x_max'] = x_raw
        updated = True
    if y_raw < bounds['y_min']:
        bounds['y_min'] = y_raw
        updated = True
    if y_raw > bounds['y_max']:
        bounds['y_max'] = y_raw
        updated = True
    
    bounds['samples'] += 1
    return updated

def get_calibrated_xy(x_raw, y_raw):
    """Convertit brut → pixels avec limites actuelles"""
    if bounds['x_max'] == bounds['x_min'] or bounds['y_max'] == bounds['y_min']:
        return None, None
    
    # Détection auto du flip
    x_range = bounds['x_max'] - bounds['x_min']
    y_range = bounds['y_max'] - bounds['y_min']
    
    # Normalisation 0-1
    x_norm = (x_raw - bounds['x_min']) / x_range
    y_norm = (y_raw - bounds['y_min']) / y_range
    
    # On teste si inversé en comparant avec le premier échantillon
    # Pour simplifier, on assume inversé (comme vos mesures précédentes)
    x_pixel = int((1 - x_norm) * 319)
    y_pixel = int((1 - y_norm) * 239)
    
    return max(0, min(319, x_pixel)), max(0, min(239, y_pixel))

def draw_ui(cursor_x=None, cursor_y=None, msg=""):
    """Dessine l'interface avec limites actuelles"""
    img = Image.new('RGB', (320, 240), (255, 255, 255))
    d = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = font_big = None
    
    # Grille de fond
    for i in range(0, 320, 40):
        d.line([(i, 0), (i, 240)], fill=(230, 230, 230))
    for i in range(0, 240, 40):
        d.line([(0, i), (320, i)], fill=(230, 230, 230))
    
    # Bordure rouge si calibration incomplète
    if bounds['x_max'] - bounds['x_min'] < 3000 or bounds['y_max'] - bounds['y_min'] < 3000:
        d.rectangle([(0, 0), (319, 239)], outline=(255, 0, 0), width=3)
    else:
        d.rectangle([(0, 0), (319, 239)], outline=(0, 255, 0), width=3)
    
    # Croix aux 4 coins cibles
    corners = [(10, 10), (310, 10), (10, 230), (310, 230)]
    for cx, cy in corners:
        d.line([(cx-8, cy), (cx+8, cy)], fill=(200, 200, 200), width=2)
        d.line([(cx, cy-8), (cx, cy+8)], fill=(200, 200, 200), width=2)
    
    # Curseur actuel
    if cursor_x is not None and cursor_y is not None:
        # Croix bleue
        d.line([(cursor_x-15, cursor_y), (cursor_x+15, cursor_y)], fill=(0, 0, 255), width=3)
        d.line([(cursor_x, cursor_y-15), (cursor_x, cursor_y+15)], fill=(0, 0, 255), width=3)
        # Cercle
        d.ellipse([(cursor_x-10, cursor_y-10), (cursor_x+10, cursor_y+10)], 
                  outline=(0, 0, 255), width=2)
        # Point central
        d.ellipse([(cursor_x-3, cursor_y-3), (cursor_x+3, cursor_y+3)], fill=(255, 0, 0))
    
    # Info texte
    y_pos = 5
    
    # Titre
    d.text((5, y_pos), "CALIBRATION AUTO", fill=(0, 0, 255), font=font_big)
    y_pos += 20
    
    # Instructions
    if bounds['samples'] < 10:
        d.text((5, y_pos), "Explorez TOUS les coins!", fill=(255, 0, 0), font=font)
    else:
        coverage = min(100, int((bounds['x_max'] - bounds['x_min']) / 35))
        d.text((5, y_pos), f"Couverture: {coverage}%", fill=(0, 150, 0), font=font)
    y_pos += 15
    
    # Limites actuelles (en bas)
    info_y = 180
    d.rectangle([(0, info_y-2), (319, 239)], fill=(240, 240, 240))
    
    d.text((5, info_y), f"X: {bounds['x_min']} - {bounds['x_max']}", fill=(0, 0, 0), font=font)
    d.text((5, info_y+15), f"Y: {bounds['y_min']} - {bounds['y_max']}", fill=(0, 0, 0), font=font)
    d.text((5, info_y+30), f"Samples: {bounds['samples']}", fill=(100, 100, 100), font=font)
    
    # Message d'update
    if msg:
        d.text((170, info_y+15), msg, fill=(255, 0, 0), font=font_big)
    
    # Message de fin
    if bounds['x_max'] - bounds['x_min'] > 3400 and bounds['y_max'] - bounds['y_min'] > 3400:
        d.text((100, 100), "CALIBRATION OK!", fill=(0, 200, 0), font=font_big)
        d.text((80, 120), "Ctrl+C pour terminer", fill=(0, 150, 0), font=font)
    
    return img

# Init
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

serial = spi(port=0, device=0, gpio_DC=DC, gpio_RST=RST)
device = ili9341(serial)

GPIO.setup(IRQ, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CS, GPIO.OUT)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.output(CS, GPIO.HIGH)
GPIO.output(CLK, GPIO.LOW)

signal.signal(signal.SIGINT, signal_handler)

print("\n" + "="*60)
print("CALIBRATION AUTOMATIQUE INTELLIGENTE")
print("="*60)
print("\nExplorez TOUS les coins de l'ecran avec le stylet")
print("Les limites se mettent a jour automatiquement")
print("Appuyez sur Ctrl+C quand termine\n")

device.display(draw_ui())

last_update_msg = ""
last_update_time = 0

try:
    while not stop:
        if GPIO.input(IRQ) == GPIO.LOW:
            x_raw, y_raw = read_xy_raw()
            
            if x_raw and y_raw:
                # Met à jour les limites
                updated = update_bounds(x_raw, y_raw)
                
                if updated:
                    msg = "NOUVEAU!"
                    last_update_time = time.time()
                    print(f"[{bounds['samples']:4d}] NOUVEAU RECORD: X[{bounds['x_min']}-{bounds['x_max']}] Y[{bounds['y_min']}-{bounds['y_max']}]")
                else:
                    # Efface le message après 1 sec
                    msg = "NOUVEAU!" if time.time() - last_update_time < 1 else ""
                
                # Calcul position calibrée
                x_pixel, y_pixel = get_calibrated_xy(x_raw, y_raw)
                
                if x_pixel is not None:
                    img = draw_ui(x_pixel, y_pixel, msg)
                    device.display(img)
            
            time.sleep(0.03)
        else:
            time.sleep(0.01)

except KeyboardInterrupt:
    pass

finally:
    print("\n" + "="*60)
    print("CALIBRATION TERMINEE")
    print("="*60)
    print(f"\nNombre d'echantillons: {bounds['samples']}")
    print(f"\nValeurs de calibration:")
    print(f"  X_MIN = {bounds['x_min']}")
    print(f"  X_MAX = {bounds['x_max']}")
    print(f"  Y_MIN = {bounds['y_min']}")
    print(f"  Y_MAX = {bounds['y_max']}")
    print(f"\nPlage X: {bounds['x_max'] - bounds['x_min']}")
    print(f"Plage Y: {bounds['y_max'] - bounds['y_min']}")
    print(f"\nCopiez ces valeurs dans votre programme:")
    print(f"X_MIN, X_MAX = {bounds['x_min']}, {bounds['x_max']}")
    print(f"Y_MIN, Y_MAX = {bounds['y_min']}, {bounds['y_max']}")
    
    try:
        device.clear()
    except:
        pass
    GPIO.cleanup()
