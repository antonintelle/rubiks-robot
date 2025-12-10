#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test écran TFT SPI 1.8" ST7735 sur Raspberry Pi
Affiche un test pattern avec texte, rectangles colorés et cercles
"""

from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont
import time

# Configuration GPIO pour l'écran TFT
# DC (Data/Command) = GPIO 24
# RST (Reset) = GPIO 25
# SPI utilise les broches SPI0 matérielles du Pi
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)

# Initialisation écran ST7735
# Pour un écran 1.8" 128x160, essayez d'abord sans spécifier width/height
# ou utilisez h=160, w=128 selon l'orientation
device = st7735(serial, rotate=0)

def test_display():
    """Fonction de test complète de l'écran"""
    
    print(f"Résolution détectée: {device.width}x{device.height}")
    
    # Test 1: Fond de couleur plein écran
    print("Test 1: Affichage fond rouge...")
    image = Image.new("RGB", (device.width, device.height), "red")
    device.display(image)
    time.sleep(2)
    
    print("Test 2: Affichage fond vert...")
    image = Image.new("RGB", (device.width, device.height), "green")
    device.display(image)
    time.sleep(2)
    
    print("Test 3: Affichage fond bleu...")
    image = Image.new("RGB", (device.width, device.height), "blue")
    device.display(image)
    time.sleep(2)
    
    # Test 2: Dessin de formes géométriques
    print("Test 4: Formes géométriques...")
    image = Image.new("RGB", (device.width, device.height), "black")
    draw = ImageDraw.Draw(image)
    
    # Adaptation des positions selon la taille réelle
    rect_size = min(device.width, device.height) // 3
    
    # Rectangle rouge
    draw.rectangle([10, 10, 10 + rect_size, 30], outline="red", fill="red")
    # Rectangle vert
    draw.rectangle([device.width - rect_size - 10, 10, device.width - 10, 30], outline="green", fill="green")
    # Cercle bleu centré
    center_x = device.width // 2
    center_y = device.height // 2
    radius = 30
    draw.ellipse([center_x - radius, center_y - radius, 
                  center_x + radius, center_y + radius], 
                 outline="blue", fill="blue")
    
    device.display(image)
    time.sleep(3)
    
    # Test 3: Affichage de texte
    print("Test 5: Affichage texte...")
    image = Image.new("RGB", (device.width, device.height), "black")
    draw = ImageDraw.Draw(image)
    
    font = ImageFont.load_default()
    
    # Texte centré
    text1 = "TFT Test OK!"
    text2 = "Raspberry Pi"
    text3 = f"{device.width}x{device.height}"
    
    # Calcul position centrée pour chaque ligne
    bbox1 = draw.textbbox((0, 0), text1, font=font)
    bbox2 = draw.textbbox((0, 0), text2, font=font)
    bbox3 = draw.textbbox((0, 0), text3, font=font)
    
    w1 = bbox1[2] - bbox1[0]
    w2 = bbox2[2] - bbox2[0]
    w3 = bbox3[2] - bbox3[0]
    
    draw.text(((device.width - w1) // 2, 40), text1, font=font, fill="white")
    draw.text(((device.width - w2) // 2, 70), text2, font=font, fill="cyan")
    draw.text(((device.width - w3) // 2, 100), text3, font=font, fill="yellow")
    
    device.display(image)
    time.sleep(3)
    
    # Test 4: Dégradé
    print("Test 6: Pattern final...")
    image = Image.new("RGB", (device.width, device.height), "black")
    draw = ImageDraw.Draw(image)
    
    # Bandes colorées
    colors = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "white"]
    ban

test_display()