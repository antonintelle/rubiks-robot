#!/usr/bin/env python3
# ============================================================================
#  anneau_lumineux.py - VERSION 2 ANNEAUX SÉPARÉS
#  -----------------
#  Fonctions distinctes pour contrôler indépendamment :
#    - Anneau 1 : GPIO18 (Pin 12) - suffixe _anneau1() --> CAPOT
#    - Anneau 2 : GPIO12 (Pin 32) - suffixe _anneau2() --> LAMPE
#    ATTENTION AM ETTRE SUR DEUX CANNEAUX DIFFERENTS 12 et 13 et pas par exemple 18 et 12
#    - Les 2 ensemble : suffixe _tous() ou pas de suffixe
# ============================================================================

import time
import board
import neopixel
import digitalio
import json, os
from config_manager import get_config

# ============================================
# CHARGEMENT DE LA CONFIGURATION
# ============================================

cfg = get_config()
leds_cfg = cfg.leds_config or {}

# Configuration globale
leds_off = not cfg.leds_enabled

# Configuration anneau 1 CAPOT
anneau1_cfg = leds_cfg.get("anneau1", {})
anneau1_enabled = anneau1_cfg.get("enabled", True) and not leds_off
LED_PIN_1 = getattr(board, f"D{anneau1_cfg.get('pin', 18)}")
LED_COUNT_1 = anneau1_cfg.get("count", 24)
BRIGHTNESS_1 = anneau1_cfg.get("brightness", 0.3)

# Configuration anneau 2 LAMPE
anneau2_cfg = leds_cfg.get("anneau2", {})
anneau2_enabled = anneau2_cfg.get("enabled", True) and not leds_off
LED_PIN_2 = getattr(board, f"D{anneau2_cfg.get('pin', 12)}")
LED_COUNT_2 = anneau2_cfg.get("count", 24)
BRIGHTNESS_2 = anneau2_cfg.get("brightness", 0.3)

print("📋 Configuration LEDs chargée:")
print(f"  - Global: {'Activé' if not leds_off else 'Désactivé'}")
print(f"  - Anneau 1: {'Activé' if anneau1_enabled else 'Désactivé'} (GPIO{anneau1_cfg.get('pin', 18)}, {LED_COUNT_1} LEDs, brightness {BRIGHTNESS_1})")
print(f"  - Anneau 2: {'Activé' if anneau2_enabled else 'Désactivé'} (GPIO{anneau2_cfg.get('pin', 13)}, {LED_COUNT_2} LEDs, brightness {BRIGHTNESS_2})")

# ============================================
# INITIALISATION
# ============================================

pixels_1 = None
pixels_2 = None

if leds_off:
    print("⚠️ LEDs désactivées globalement via configuration")
else:
    # Anneau 1
    if anneau1_enabled:
        try:
            pixels_1 = neopixel.NeoPixel(LED_PIN_1, LED_COUNT_1, brightness=BRIGHTNESS_1, auto_write=False)
            print(f"✅ Anneau 1 initialisé (GPIO{anneau1_cfg.get('pin', 18)}, {LED_COUNT_1} LEDs)")
        except Exception as e:
            print(f"❌ Erreur init anneau 1 : {e}")
            pixels_1 = None
    else:
        print(f"⚠️ Anneau 1 désactivé via configuration")
    
    # Anneau 2
    if anneau2_enabled:
        try:
            pixels_2 = neopixel.NeoPixel(LED_PIN_2, LED_COUNT_2, brightness=BRIGHTNESS_2, auto_write=False)
            print(f"✅ Anneau 2 initialisé (GPIO{anneau2_cfg.get('pin', 13)}, {LED_COUNT_2} LEDs)")
        except Exception as e:
            print(f"❌ Erreur init anneau 2 : {e}")
            pixels_2 = None
    else:
        print(f"⚠️ Anneau 2 désactivé via configuration")


# ============================================
# FONCTIONS ANNEAU 1 UNIQUEMENT
# ============================================

def eteindre_anneau1():
    """Éteint uniquement l'anneau 1"""
    if leds_off or not pixels_1:
        return
    pixels_1.fill((0, 0, 0))
    pixels_1.show()
    print("✨ Anneau 1 éteint")


def couleur_fixe_anneau1(couleur, duree=3):
    """Couleur fixe sur anneau 1 uniquement"""
    if leds_off or not pixels_1:
        return
    pixels_1.fill(couleur)
    pixels_1.show()
    print(f"🎨 Anneau 1: {couleur}")
    if duree > 0:
        time.sleep(duree)


def arc_en_ciel_anneau1(cycles=3, vitesse=0.05):
    """Arc-en-ciel sur anneau 1 uniquement"""
    if leds_off or not pixels_1:
        return
    print("🌈 Arc-en-ciel anneau 1...")
    
    def roue(pos):
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    for cycle in range(cycles * 256):
        for i in range(LED_COUNT_1):
            pixel_index = (i * 256 // LED_COUNT_1) + cycle
            pixels_1[i] = roue(pixel_index & 255)
        pixels_1.show()
        time.sleep(vitesse)


def pulse_anneau1(couleur=(0, 0, 255), cycles=3, vitesse=0.02):
    """Pulsation sur anneau 1 uniquement"""
    if leds_off or not pixels_1:
        return
    print(f"💙 Pulsation anneau 1: {couleur}")
    
    for _ in range(cycles):
        for b in range(0, 100, 5):
            brightness = b / 100.0
            r, g, b_val = couleur
            pixels_1.fill((int(r * brightness), int(g * brightness), int(b_val * brightness)))
            pixels_1.show()
            time.sleep(vitesse)
        
        for b in range(100, 0, -5):
            brightness = b / 100.0
            r, g, b_val = couleur
            pixels_1.fill((int(r * brightness), int(g * brightness), int(b_val * brightness)))
            pixels_1.show()
            time.sleep(vitesse)


def eclairage_capture_anneau1(brightness=0.12, color=(255, 255, 255)):
    """Éclairage capture anneau 1 uniquement"""
    if leds_off or not pixels_1:
        return
    pixels_1.brightness = brightness
    pixels_1.fill(color)
    pixels_1.show()
    print(f"💡 Anneau 1 éclairage: brightness={brightness:.2f}")


def eclairage_2_leds_anneau1(brightness=0.15, leds=(18, 22), color=(255, 180, 60)):
    """Éclairage partiel anneau 1 uniquement"""
    if leds_off or not pixels_1:
        return
    pixels_1.brightness = brightness
    pixels_1.fill((0, 0, 0))
    for i in leds:
        if i < LED_COUNT_1:
            pixels_1[i] = color
    pixels_1.show()
    print(f"💡 Anneau 1: {len(leds)} LEDs actives")


# ============================================
# FONCTIONS ANNEAU 2 UNIQUEMENT
# ============================================

def eteindre_anneau2():
    """Éteint uniquement l'anneau 2"""
    if leds_off or not pixels_2:
        return
    pixels_2.fill((0, 0, 0))
    pixels_2.show()
    print("✨ Anneau 2 éteint")


def couleur_fixe_anneau2(couleur, duree=3):
    """Couleur fixe sur anneau 2 uniquement"""
    if leds_off or not pixels_2:
        return
    pixels_2.fill(couleur)
    pixels_2.show()
    print(f"🎨 Anneau 2: {couleur}")
    if duree > 0:
        time.sleep(duree)


def arc_en_ciel_anneau2(cycles=3, vitesse=0.05):
    """Arc-en-ciel sur anneau 2 uniquement"""
    if leds_off or not pixels_2:
        return
    print("🌈 Arc-en-ciel anneau 2...")
    
    def roue(pos):
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)
    
    for cycle in range(cycles * 256):
        for i in range(LED_COUNT_2):
            pixel_index = (i * 256 // LED_COUNT_2) + cycle
            pixels_2[i] = roue(pixel_index & 255)
        pixels_2.show()
        time.sleep(vitesse)


def pulse_anneau2(couleur=(0, 0, 255), cycles=3, vitesse=0.02):
    """Pulsation sur anneau 2 uniquement"""
    if leds_off or not pixels_2:
        return
    print(f"💙 Pulsation anneau 2: {couleur}")
    
    for _ in range(cycles):
        for b in range(0, 100, 5):
            brightness = b / 100.0
            r, g, b_val = couleur
            pixels_2.fill((int(r * brightness), int(g * brightness), int(b_val * brightness)))
            pixels_2.show()
            time.sleep(vitesse)
        
        for b in range(100, 0, -5):
            brightness = b / 100.0
            r, g, b_val = couleur
            pixels_2.fill((int(r * brightness), int(g * brightness), int(b_val * brightness)))
            pixels_2.show()
            time.sleep(vitesse)


def eclairage_capture_anneau2(brightness=0.12, color=(255, 255, 255)):
    """Éclairage capture anneau 2 uniquement"""
    if leds_off or not pixels_2:
        return
    pixels_2.brightness = brightness
    pixels_2.fill(color)
    pixels_2.show()
    print(f"💡 Anneau 2 éclairage: brightness={brightness:.2f}")


def eclairage_2_leds_anneau2(brightness=0.15, leds=(18, 22), color=(255, 180, 60)):
    """Éclairage partiel anneau 2 uniquement"""
    if leds_off or not pixels_2:
        return
    pixels_2.brightness = brightness
    pixels_2.fill((0, 0, 0))
    for i in leds:
        if i < LED_COUNT_2:
            pixels_2[i] = color
    pixels_2.show()
    print(f"💡 Anneau 2: {len(leds)} LEDs actives")


# ============================================
# FONCTIONS POUR LES 2 ANNEAUX ENSEMBLE
# ============================================

def eteindre():
    """Éteint les 2 anneaux"""
    if leds_off:
        return
    eteindre_anneau1()
    eteindre_anneau2()


def eteindre_force():
    """Reset complet des 2 anneaux"""
    global pixels_1, pixels_2
    
    if leds_off:
        return
    
    # Reset anneau 1
    if pixels_1:
        try:
            pixels_1.deinit()
            time.sleep(0.2)
            pin = digitalio.DigitalInOut(board.D18)
            pin.direction = digitalio.Direction.OUTPUT
            pin.value = False
            time.sleep(0.2)
            pin.deinit()
            time.sleep(0.2)
            pixels_1 = neopixel.NeoPixel(LED_PIN_1, LED_COUNT_1, brightness=BRIGHTNESS_1, auto_write=False)
            pixels_1.fill((0, 0, 0))
            pixels_1.show()
            print("✨ Anneau 1 forcé à l'extinction")
        except Exception as e:
            print(f"⚠️ Erreur reset anneau 1: {e}")
    
    # Reset anneau 2
    if pixels_2:
        try:
            pixels_2.deinit()
            time.sleep(0.2)
            pin = digitalio.DigitalInOut(board.D12)
            pin.direction = digitalio.Direction.OUTPUT
            pin.value = False
            time.sleep(0.2)
            pin.deinit()
            time.sleep(0.2)
            pixels_2 = neopixel.NeoPixel(LED_PIN_2, LED_COUNT_2, brightness=BRIGHTNESS_2, auto_write=False)
            pixels_2.fill((0, 0, 0))
            pixels_2.show()
            print("✨ Anneau 2 forcé à l'extinction")
        except Exception as e:
            print(f"⚠️ Erreur reset anneau 2: {e}")


def couleur_fixe_tous(couleur, duree=3):
    """Couleur fixe sur les 2 anneaux"""
    couleur_fixe_anneau1(couleur, duree=0)
    couleur_fixe_anneau2(couleur, duree=0)
    if duree > 0:
        time.sleep(duree)


def couleurs_differentes(couleur1, couleur2, duree=3):
    """Anneau 1 et anneau 2 avec couleurs différentes"""
    couleur_fixe_anneau1(couleur1, duree=0)
    couleur_fixe_anneau2(couleur2, duree=0)
    if duree > 0:
        time.sleep(duree)


def eclairage_capture(brightness=0.12):
    """Éclairage capture sur les 2 anneaux"""
    eclairage_capture_anneau1(brightness)
    eclairage_capture_anneau2(brightness)


def eclairage_capture_2_leds(brightness=0.15, leds=(18, 22), color=(255, 180, 60)):
    """Éclairage 2 LEDs sur les 2 anneaux"""
    eclairage_2_leds_anneau1(brightness, leds, color)
    eclairage_2_leds_anneau2(brightness, leds, color)


# ============================================
# PRESETS ET CONFIGURATION
# ============================================

VISION_PRESETS = {
    "warm": (255, 170, 40),
    "very_warm": (255, 150, 30),
    "neutral": (255, 180, 60),
    "coolish": (220, 170, 90),
    "warm_balanced": (255, 185, 70),
    "neutral_warm": (255, 200, 100),
    "white": (255, 255, 255),
    "cold": (200, 220, 255),
    "cool": (180, 210, 255),
}


def eclairage_capture_2_leds_preset(
    brightness=0.08,
    leds=(18, 22),
    preset="neutral_warm",
    gradient=False,
    anneau=None  # None=tous, 1=anneau1, 2=anneau2
):
    """
    Éclairage avec preset de couleur
    anneau: None (les 2), 1 (anneau 1 seul), 2 (anneau 2 seul)
    """
    if leds_off:
        return
    
    color = VISION_PRESETS.get(preset, VISION_PRESETS["white"])
    
    if anneau is None or anneau == 1:
        eclairage_2_leds_anneau1(brightness, leds, color)
    
    if anneau is None or anneau == 2:
        eclairage_2_leds_anneau2(brightness, leds, color)



def _merge_dict(base: dict, override: dict) -> dict:
    """Merge simple: override gagne. Ne modifie pas base."""
    if not override:
        return dict(base) if base else {}
    out = dict(base) if base else {}
    out.update({k: v for k, v in override.items() if v is not None})
    return out

def leds_on_for_scan_cfg():
    """
    Charge la config scan depuis config_manager
    Utilise les configs SÉPARÉES pour chaque anneau
    + surcharge possible via le lock_profile_active (camera.lock_profiles[*].led_scan)
    """
    cfg = get_config()
    if not cfg.leds_enabled:
        return

    leds_cfg = cfg.leds_config or {}

    # --------- Récupérer overrides LED depuis le profil caméra actif ---------
    cam_cfg = getattr(cfg, "camera_config", None) or getattr(cfg, "camera", None) or {}
    lock_profile_active = cam_cfg.get("lock_profile_active")
    lock_profiles = cam_cfg.get("lock_profiles", {}) or {}
    prof = lock_profiles.get(lock_profile_active, {}) if lock_profile_active else {}
    led_scan_overrides = prof.get("led_scan", {}) or {}

    # --------- Anneau 1 ---------
    anneau1_cfg = leds_cfg.get("anneau1", {})
    scan1_cfg = anneau1_cfg.get("scan", {}) or {}

    # Merge overrides profil -> scan
    scan1_cfg = _merge_dict(scan1_cfg, led_scan_overrides.get("anneau1", {}))

    anneau1_scan_enabled = scan1_cfg.get("enabled", True)

    # --------- Anneau 2 ---------
    anneau2_cfg = leds_cfg.get("anneau2", {})
    scan2_cfg = anneau2_cfg.get("scan", {}) or {}

    # Merge overrides profil -> scan
    scan2_cfg = _merge_dict(scan2_cfg, led_scan_overrides.get("anneau2", {}))

    anneau2_scan_enabled = scan2_cfg.get("enabled", True)

    print(f"📋 Éclairage scan (profil={lock_profile_active}):")
    print(f"  - Anneau 1: {'Activé' if anneau1_scan_enabled else 'Désactivé'}")
    print(f"  - Anneau 2: {'Activé' if anneau2_scan_enabled else 'Désactivé'}")

    # --------- Appliquer anneau 1 ---------
    if anneau1_scan_enabled and pixels_1:
        mode1 = scan1_cfg.get("mode", "2_leds_preset")
        brightness1 = float(scan1_cfg.get("brightness", 0.08))
        brightness1 = min(brightness1, float(scan1_cfg.get("brightness_max", brightness1)))
        leds1 = tuple(scan1_cfg.get("led_indices", [18, 22]))
        preset1 = scan1_cfg.get("preset", "neutral_warm")
        color1 = VISION_PRESETS.get(preset1, VISION_PRESETS["white"])

        print(f"  🔍 DEBUG Anneau 1: mode={mode1} led_indices={leds1}")

        # ⚠️ Ici tu ignores mode1. Si tu as plusieurs modes, branche-les ici.
        eclairage_2_leds_anneau1(brightness=brightness1, leds=leds1, color=color1)
        print(f"  ✅ Anneau 1: {len(leds1)} LEDs, brightness={brightness1:.2f}, preset={preset1}")

    # --------- Appliquer anneau 2 ---------
    if anneau2_scan_enabled and pixels_2:
        mode2 = scan2_cfg.get("mode", "2_leds_preset")
        brightness2 = float(scan2_cfg.get("brightness", 0.08))
        brightness2 = min(brightness2, float(scan2_cfg.get("brightness_max", brightness2)))
        leds2 = tuple(scan2_cfg.get("led_indices", [18, 22]))
        preset2 = scan2_cfg.get("preset", "neutral_warm")
        color2 = VISION_PRESETS.get(preset2, VISION_PRESETS["white"])

        print(f"  🔍 DEBUG Anneau 2: mode={mode2} led_indices={leds2}")

        eclairage_2_leds_anneau2(brightness=brightness2, leds=leds2, color=color2)
        print(f"  ✅ Anneau 2: {len(leds2)} LEDs, brightness={brightness2:.2f}, preset={preset2}")


def leds_on_for_scan_cfg_legacy():
    """
    Charge la config scan depuis config_manager
    Utilise les configs SÉPARÉES pour chaque anneau
    """
    cfg = get_config()
    if not cfg.leds_enabled:
        return

    leds_cfg = cfg.leds_config or {}
    
    # Configuration scan anneau 1
    anneau1_cfg = leds_cfg.get("anneau1", {})
    scan1_cfg = anneau1_cfg.get("scan", {})
    anneau1_scan_enabled = scan1_cfg.get("enabled", True)
    
    # Configuration scan anneau 2
    anneau2_cfg = leds_cfg.get("anneau2", {})
    scan2_cfg = anneau2_cfg.get("scan", {})
    anneau2_scan_enabled = scan2_cfg.get("enabled", True)
    
    print(f"📋 Éclairage scan:")
    print(f"  - Anneau 1: {'Activé' if anneau1_scan_enabled else 'Désactivé'}")
    print(f"  - Anneau 2: {'Activé' if anneau2_scan_enabled else 'Désactivé'}")
    
    # Appliquer config anneau 1
    if anneau1_scan_enabled and pixels_1:
        mode1 = scan1_cfg.get("mode", "2_leds_preset")
        brightness1 = float(scan1_cfg.get("brightness", 0.08))
        brightness1 = min(brightness1, float(scan1_cfg.get("brightness_max", brightness1)))
        leds1 = tuple(scan1_cfg.get("led_indices", [18, 22]))
        preset1 = scan1_cfg.get("preset", "neutral_warm")
        color1 = VISION_PRESETS.get(preset1, VISION_PRESETS["white"])
        
        # 🔍 DEBUG : Afficher les indices chargés
        print(f"  🔍 DEBUG Anneau 1: led_indices chargés = {leds1}")
        
        eclairage_2_leds_anneau1(brightness=brightness1, leds=leds1, color=color1)
        print(f"  ✅ Anneau 1: {len(leds1)} LEDs, brightness={brightness1:.2f}, preset={preset1}")
    
    # Appliquer config anneau 2
    if anneau2_scan_enabled and pixels_2:
        mode2 = scan2_cfg.get("mode", "2_leds_preset")
        brightness2 = float(scan2_cfg.get("brightness", 0.08))
        brightness2 = min(brightness2, float(scan2_cfg.get("brightness_max", brightness2)))
        leds2 = tuple(scan2_cfg.get("led_indices", [18, 22]))
        preset2 = scan2_cfg.get("preset", "neutral_warm")
        color2 = VISION_PRESETS.get(preset2, VISION_PRESETS["white"])
        
        # 🔍 DEBUG : Afficher les indices chargés
        print(f"  🔍 DEBUG Anneau 2: led_indices chargés = {leds2}")
        
        eclairage_2_leds_anneau2(brightness=brightness2, leds=leds2, color=color2)
        print(f"  ✅ Anneau 2: {len(leds2)} LEDs, brightness={brightness2:.2f}, preset={preset2}")


# ============================================
# CLEANUP
# ============================================

def cleanup():
    """Nettoie et libère les ressources"""
    global pixels_1, pixels_2
    
    if pixels_1:
        try:
            pixels_1.fill((0, 0, 0))
            pixels_1.show()
            pixels_1.deinit()
            print("✅ Anneau 1 nettoyé")
        except:
            pass
    
    if pixels_2:
        try:
            pixels_2.fill((0, 0, 0))
            pixels_2.show()
            pixels_2.deinit()
            print("✅ Anneau 2 nettoyé")
        except:
            pass


# ============================================
# MENU PRINCIPAL
# ============================================

def afficher_menu():
    """Menu interactif"""
    print("\n" + "="*60)
    print("🎨 CONTRÔLE 2 ANNEAUX LED - FONCTIONS SÉPARÉES")
    print("="*60)
    print("ANNEAU 1 (GPIO18):")
    print("  1. Arc-en-ciel anneau 1")
    print("  2. Pulsation bleue anneau 1")
    print("  3. Rouge anneau 1")
    print("  4. 💡 Éclairage SCAN anneau 1 (config.json)")
    print("")
    print("ANNEAU 2 (GPIO12):")
    print("  5. Arc-en-ciel anneau 2")
    print("  6. Pulsation bleue anneau 2")
    print("  7. Vert anneau 2")
    print("  8. 💡 Éclairage SCAN anneau 2 (config.json)")
    print("")
    print("LES 2 ANNEAUX:")
    print("  9. Éteindre les 2")
    print(" 10. Blanc les 2 (uniforme)")
    print(" 11. Anneau 1 rouge + Anneau 2 bleu")
    print(" 12. 💡 Éclairage SCAN les 2 (config.json)")
    print("")
    print("DEBUG:")
    print(" 15. 🎯 Test complet config.json + DEBUG")
    print("")
    print("  0. Quitter")
    print("="*60)


def main():
    """Programme principal"""
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\n⚠️ Interruption (Ctrl+C)")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n🌟 Contrôleur 2 anneaux NeoPixel - Fonctions séparées 🌟\n")
    
    try:
        while True:
            afficher_menu()
            choix = input("\n👉 Choix (0-15): ").strip()
            
            # Anneau 1
            if choix == "1":
                arc_en_ciel_anneau1(cycles=2)
            elif choix == "2":
                pulse_anneau1((0, 0, 255), cycles=2)
            elif choix == "3":
                couleur_fixe_anneau1((255, 0, 0), duree=3)
            elif choix == "4":
                print("\n💡 Éclairage SCAN Anneau 1 (depuis config.json)...")
                # Charger config anneau 1
                cfg = get_config()
                leds_cfg = cfg.leds_config or {}
                anneau1_cfg = leds_cfg.get("anneau1", {})
                scan1_cfg = anneau1_cfg.get("scan", {})
                
                brightness1 = float(scan1_cfg.get("brightness", 0.12))
                leds1 = tuple(scan1_cfg.get("led_indices", [18, 22]))
                preset1 = scan1_cfg.get("preset", "neutral_warm")
                color1 = VISION_PRESETS.get(preset1, VISION_PRESETS["white"])
                
                print(f"  🔍 Config: brightness={brightness1}, leds={leds1}, preset={preset1}")
                eclairage_2_leds_anneau1(brightness=brightness1, leds=leds1, color=color1)
                input("Appuyez sur Entrée pour éteindre...")
                eteindre_anneau1()
            
            # Anneau 2
            elif choix == "5":
                arc_en_ciel_anneau2(cycles=2)
            elif choix == "6":
                pulse_anneau2((0, 0, 255), cycles=2)
            elif choix == "7":
                couleur_fixe_anneau2((0, 255, 0), duree=3)
            elif choix == "8":
                print("\n💡 Éclairage SCAN Anneau 2 (depuis config.json)...")
                # Charger config anneau 2
                cfg = get_config()
                leds_cfg = cfg.leds_config or {}
                anneau2_cfg = leds_cfg.get("anneau2", {})
                scan2_cfg = anneau2_cfg.get("scan", {})
                
                brightness2 = float(scan2_cfg.get("brightness", 0.08))
                leds2 = tuple(scan2_cfg.get("led_indices", [18, 22]))
                preset2 = scan2_cfg.get("preset", "white")
                color2 = VISION_PRESETS.get(preset2, VISION_PRESETS["white"])
                
                print(f"  🔍 Config: brightness={brightness2}, leds={leds2}, preset={preset2}")
                eclairage_2_leds_anneau2(brightness=brightness2, leds=leds2, color=color2)
                input("Appuyez sur Entrée pour éteindre...")
                eteindre_anneau2()
            
            # Les 2
            elif choix == "9":
                eteindre()
            elif choix == "10":
                couleur_fixe_tous((255, 255, 255), duree=3)
            elif choix == "11":
                couleurs_differentes((255, 0, 0), (0, 0, 255), duree=3)
            elif choix == "12":
                print("\n💡 Éclairage SCAN LES 2 (depuis config.json)...")
                leds_on_for_scan_cfg()
                input("Appuyez sur Entrée pour éteindre...")
                eteindre()
            
            # Configuration
            elif choix == "15":
                print("\n🎯 Chargement de l'éclairage SCAN depuis config.json...")
                leds_on_for_scan_cfg()
                print("\n✅ Éclairage appliqué selon votre configuration !")
                print("Vérifiez visuellement les LEDs allumées.")
                input("Appuyez sur Entrée pour éteindre...")
                eteindre()
            
            elif choix == "0":
                print("\n👋 Arrêt...")
                eteindre()
                break
            
            else:
                print("❌ Choix invalide")
            
            time.sleep(0.5)
    
    finally:
        cleanup()


if __name__ == "__main__":
    main()
