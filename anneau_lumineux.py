#!/usr/bin/env python3
"""
Programme pour contrôler un anneau NeoPixel
Connexions:
- Rouge (5V) -> 5V
- Blanc (GND) -> GND
- Vert (Data) -> GPIO18
"""

import time
import board
import neopixel

# Configuration de l'anneau LED
LED_PIN = board.D18      # GPIO18
LED_COUNT = 24           # Nombre de LEDs (changez selon votre anneau: 12, 16, 24, etc.)
BRIGHTNESS = 0.3         # Luminosité (0.0 à 1.0)

# Initialisation de l'anneau
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)


# ========== FONCTIONS D'EFFETS ==========

def eteindre():
    """Éteint toutes les LEDs"""
    pixels.fill((0, 0, 0))
    pixels.show()
    print("✨ Toutes les LEDs éteintes")


def couleur_fixe(couleur, duree=3):
    """
    Allume toutes les LEDs d'une couleur fixe
    couleur: tuple (R, G, B) de 0 à 255
    """
    pixels.fill(couleur)
    pixels.show()
    print(f"🎨 Couleur fixe: {couleur}")
    time.sleep(duree)


def arc_en_ciel(cycles=3, vitesse=0.05):
    """Effet arc-en-ciel qui tourne autour de l'anneau"""
    print("🌈 Arc-en-ciel en cours...")
    
    def roue(pos):
        """Génère une couleur selon la position (0-255)"""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    for cycle in range(cycles * 256):
        for i in range(LED_COUNT):
            pixel_index = (i * 256 // LED_COUNT) + cycle
            pixels[i] = roue(pixel_index & 255)
        pixels.show()
        time.sleep(vitesse)


def chenillard(couleur=(255, 0, 0), tours=3, vitesse=0.1):
    """Une LED qui tourne autour de l'anneau"""
    print(f"🔴 Chenillard {couleur}...")
    
    for _ in range(tours):
        for i in range(LED_COUNT):
            pixels.fill((0, 0, 0))
            pixels[i] = couleur
            pixels.show()
            time.sleep(vitesse)


def pulse(couleur=(0, 0, 255), cycles=3, vitesse=0.02):
    """Effet de pulsation (respiration)"""
    print(f"💙 Pulsation {couleur}...")
    
    for _ in range(cycles):
        # Monte
        for b in range(0, 100, 5):
            brightness = b / 100.0
            r, g, b_val = couleur
            pixels.fill((int(r * brightness), int(g * brightness), int(b_val * brightness)))
            pixels.show()
            time.sleep(vitesse)
        
        # Descend
        for b in range(100, 0, -5):
            brightness = b / 100.0
            r, g, b_val = couleur
            pixels.fill((int(r * brightness), int(g * brightness), int(b_val * brightness)))
            pixels.show()
            time.sleep(vitesse)


def theatre(couleur=(255, 255, 0), cycles=10, vitesse=0.1):
    """Effet théâtre - 1 LED sur 3 allumée"""
    print(f"🎭 Théâtre {couleur}...")
    
    for _ in range(cycles):
        for offset in range(3):
            pixels.fill((0, 0, 0))
            for i in range(offset, LED_COUNT, 3):
                pixels[i] = couleur
            pixels.show()
            time.sleep(vitesse)


def clignotement(couleur=(255, 255, 255), fois=5, vitesse=0.3):
    """Clignotement on/off"""
    print(f"⚡ Clignotement {couleur}...")
    
    for _ in range(fois):
        pixels.fill(couleur)
        pixels.show()
        time.sleep(vitesse)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(vitesse)


def moitie_moitie(couleur1=(255, 0, 0), couleur2=(0, 255, 0), tours=5, vitesse=0.3):
    """Divise l'anneau en deux moitiés de couleurs différentes qui tournent"""
    print(f"🔄 Moitié-moitié {couleur1} / {couleur2}...")
    
    moitie = LED_COUNT // 2
    for _ in range(tours * LED_COUNT):
        pixels.fill((0, 0, 0))
        for i in range(moitie):
            pixels[i] = couleur1
        for i in range(moitie, LED_COUNT):
            pixels[i] = couleur2
        pixels.show()
        
        # Rotation
        temp = pixels[0]
        for i in range(LED_COUNT - 1):
            pixels[i] = pixels[i + 1]
        pixels[LED_COUNT - 1] = temp
        pixels.show()
        time.sleep(vitesse)


def feu(cycles=50, vitesse=0.05):
    """Simule des flammes avec des rouges/oranges aléatoires"""
    print("🔥 Effet feu...")
    import random
    
    for _ in range(cycles):
        for i in range(LED_COUNT):
            # Rouge et orange aléatoires
            r = random.randint(150, 255)
            g = random.randint(0, 100)
            b = 0
            pixels[i] = (r, g, b)
        pixels.show()
        time.sleep(vitesse)


def police(cycles=10, vitesse=0.1):
    """Effet gyrophare police (bleu-rouge alterné)"""
    print("🚨 Gyrophare police...")
    
    moitie = LED_COUNT // 2
    for _ in range(cycles):
        # Bleu à gauche, rouge à droite
        for i in range(moitie):
            pixels[i] = (0, 0, 255)
        for i in range(moitie, LED_COUNT):
            pixels[i] = (255, 0, 0)
        pixels.show()
        time.sleep(vitesse)
        
        # Inverse
        for i in range(moitie):
            pixels[i] = (255, 0, 0)
        for i in range(moitie, LED_COUNT):
            pixels[i] = (0, 0, 255)
        pixels.show()
        time.sleep(vitesse)


def remplissage(couleur=(0, 255, 0), vitesse=0.1):
    """Remplit progressivement l'anneau"""
    print(f"📊 Remplissage {couleur}...")
    
    pixels.fill((0, 0, 0))
    for i in range(LED_COUNT):
        pixels[i] = couleur
        pixels.show()
        time.sleep(vitesse)
    
    time.sleep(0.5)
    
    # Vide progressivement
    for i in range(LED_COUNT):
        pixels[i] = (0, 0, 0)
        pixels.show()
        time.sleep(vitesse)


def etincelle(couleur=(255, 255, 255), duree=3, densite=0.3):
    """LEDs qui scintillent aléatoirement comme des étoiles"""
    print(f"✨ Étincelles {couleur}...")
    import random
    
    debut = time.time()
    while time.time() - debut < duree:
        pixels.fill((0, 0, 0))
        # Allume quelques LEDs aléatoires
        for i in range(LED_COUNT):
            if random.random() < densite:
                pixels[i] = couleur
        pixels.show()
        time.sleep(0.05)

def eclairage_capture(brightness=0.4):
    """💡 Mode éclairage pour la capture d’images du cube"""
    print(f"💡 Mode éclairage capture (blanc neutre, intensité {brightness*100:.0f}%)")
    pixels.brightness = brightness
    pixels.fill((255, 255, 255))
    pixels.show()


# ========== MENU ET PROGRAMME PRINCIPAL ==========

def afficher_menu():
    """Affiche la liste des effets disponibles"""
    print("\n" + "="*50)
    print("🎨 EFFETS DISPONIBLES POUR ANNEAU LED 🎨")
    print("="*50)
    print("1.  Arc-en-ciel")
    print("2.  Chenillard rouge")
    print("3.  Pulsation bleue")
    print("4.  Théâtre jaune")
    print("5.  Clignotement blanc")
    print("6.  Moitié-moitié rouge/vert")
    print("7.  Feu")
    print("8.  Gyrophare police")
    print("9.  Remplissage vert")
    print("10. Étincelles blanches")
    print("11. Couleur fixe rouge")
    print("12. Couleur fixe bleu")
    print("13. Couleur fixe vert")
    print("14. Éclairage capture (blanc neutre)")
    print("0.  Éteindre et quitter")
    print("="*50)


def main():
    """Programme principal avec menu interactif"""
    print("\n🌟 Démarrage du contrôleur NeoPixel Ring 🌟\n")
    
    try:
        while True:
            afficher_menu()
            choix = input("\n👉 Choisissez un effet (0-13): ").strip()
            
            if choix == "1":
                arc_en_ciel(cycles=3, vitesse=0.03)
            elif choix == "2":
                chenillard(couleur=(255, 0, 0), tours=3, vitesse=0.08)
            elif choix == "3":
                pulse(couleur=(0, 0, 255), cycles=3, vitesse=0.02)
            elif choix == "4":
                theatre(couleur=(255, 255, 0), cycles=10, vitesse=0.1)
            elif choix == "5":
                clignotement(couleur=(255, 255, 255), fois=5, vitesse=0.3)
            elif choix == "6":
                moitie_moitie(couleur1=(255, 0, 0), couleur2=(0, 255, 0), tours=3, vitesse=0.1)
            elif choix == "7":
                feu(cycles=50, vitesse=0.05)
            elif choix == "8":
                police(cycles=10, vitesse=0.1)
            elif choix == "9":
                remplissage(couleur=(0, 255, 0), vitesse=0.08)
            elif choix == "10":
                etincelle(couleur=(255, 255, 255), duree=3, densite=0.3)
            elif choix == "11":
                couleur_fixe((255, 0, 0), duree=3)
            elif choix == "12":
                couleur_fixe((0, 0, 255), duree=3)
            elif choix == "13":
                couleur_fixe((0, 255, 0), duree=3)
            elif choix == "14":
                eclairage_capture()
            elif choix == "0":
                print("\n👋 Arrêt du programme...")
                eteindre()
                break
            else:
                print("❌ Choix invalide ! Choisissez entre 0 et 13.")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption détectée (Ctrl+C)")
        eteindre()
        print("👋 Programme arrêté proprement")


# ========== EXEMPLE D'UTILISATION DIRECTE ==========

def demo_automatique():
    """
    Démo automatique qui joue tous les effets l'un après l'autre
    Décommentez cette fonction dans __main__ pour l'utiliser
    """
    print("\n🎬 Démo automatique - Tous les effets\n")
    
    effets = [
        ("Arc-en-ciel", lambda: arc_en_ciel(cycles=2)),
        ("Chenillard", lambda: chenillard((255, 0, 0), tours=2)),
        ("Pulsation", lambda: pulse((0, 0, 255), cycles=2)),
        ("Théâtre", lambda: theatre((255, 255, 0), cycles=5)),
        ("Gyrophare", lambda: police(cycles=5)),
        ("Feu", lambda: feu(cycles=30)),
        ("Étincelles", lambda: etincelle(duree=2)),
    ]
    
    try:
        for nom, effet in effets:
            print(f"\n▶️  {nom}")
            effet()
            time.sleep(1)
            eteindre()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n⚠️  Démo interrompue")
        eteindre()


if __name__ == "__main__":
    # Menu interactif (décommentez la ligne suivante)
    main()
    
    # OU démo automatique (décommentez la ligne suivante)
    # demo_automatique()