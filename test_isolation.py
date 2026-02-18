#!/usr/bin/env python3
"""
Debug des 2 anneaux
"""
import board
import neopixel
import time

print("🔍 DEBUG : Vérification complète des anneaux\n")

# Vérifier que les GPIO sont différents
print("=" * 60)
print("ÉTAPE 1 : Vérification des GPIO")
print("=" * 60)
print(f"GPIO anneau 1 : board.D18 = {board.D18}")
print(f"GPIO anneau 2 : board.D13 = {board.D13}")

if board.D18 == board.D12:
    print("❌ ERREUR : Les deux GPIO sont identiques !")
    exit(1)
else:
    print("✅ Les GPIO sont différents\n")

# Initialiser les anneaux
print("=" * 60)
print("ÉTAPE 2 : Initialisation")
print("=" * 60)

pixels_1 = neopixel.NeoPixel(board.D18, 24, brightness=0.3, auto_write=False)
print(f"✅ Anneau 1 initialisé : {pixels_1}")

pixels_2 = neopixel.NeoPixel(board.D13, 12, brightness=0.3, auto_write=False)
print(f"✅ Anneau 2 initialisé : {pixels_2}")

# Vérifier que ce sont des objets différents
if pixels_1 is pixels_2:
    print("❌ ERREUR : pixels_1 et pixels_2 sont le même objet !")
    exit(1)
else:
    print("✅ pixels_1 et pixels_2 sont des objets différents\n")

# Test anneau 1 SEUL
print("=" * 60)
print("ÉTAPE 3 : Test anneau 1 SEUL (rouge)")
print("=" * 60)
print("Anneau 1 : ROUGE")
pixels_1.fill((255, 0, 0))
pixels_1.show()
print("Anneau 2 : NOIR (éteint)")
pixels_2.fill((0, 0, 0))
pixels_2.show()
input("\n⏸️  Vérifiez : SEUL le grand anneau doit être rouge. Appuyez sur Entrée...\n")

# Test anneau 2 SEUL
print("=" * 60)
print("ÉTAPE 4 : Test anneau 2 SEUL (vert)")
print("=" * 60)
print("Anneau 1 : NOIR (éteint)")
pixels_1.fill((0, 0, 0))
pixels_1.show()
print("Anneau 2 : VERT")
pixels_2.fill((0, 255, 0))
pixels_2.show()
input("\n⏸️  Vérifiez : SEUL le petit anneau doit être vert. Appuyez sur Entrée...\n")

# Test pulsation anneau 1
print("=" * 60)
print("ÉTAPE 5 : Pulsation anneau 1 SEUL")
print("=" * 60)
print("Anneau 2 : NOIR (reste éteint)")
pixels_2.fill((0, 0, 0))
pixels_2.show()

print("Anneau 1 : Pulsation bleue...")
for cycle in range(2):
    for b in range(0, 100, 10):
        brightness = b / 100.0
        pixels_1.fill((0, 0, int(255 * brightness)))
        pixels_1.show()
        time.sleep(0.05)
    
    for b in range(100, 0, -10):
        brightness = b / 100.0
        pixels_1.fill((0, 0, int(255 * brightness)))
        pixels_1.show()
        time.sleep(0.05)

pixels_1.fill((0, 0, 0))
pixels_1.show()

print("\n⏸️  Pendant la pulsation, le petit anneau devait rester éteint.")
input("Appuyez sur Entrée pour terminer...\n")

# Nettoyage
pixels_1.deinit()
pixels_2.deinit()

print("\n" + "=" * 60)
print("✅ Test terminé")
print("=" * 60)
print("\nRÉSULTATS ATTENDUS :")
print("  - Étape 3 : SEUL grand anneau rouge")
print("  - Étape 4 : SEUL petit anneau vert")
print("  - Étape 5 : SEUL grand anneau pulse")
print("\nSi un des anneaux réagit alors qu'il devrait être éteint,")
print("vérifiez le branchement physique des fils DATA !")