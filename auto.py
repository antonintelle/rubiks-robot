#!/usr/bin/env python3
# ============================================================================
#  auto.py  (keypad_autolearn.py) - Apprentissage interactif clavier 4x4
#  --------------------------------------------------------------------
#  Objectif :
#     Outil de “mapping” pour identifier automatiquement le câblage d’un clavier
#     matriciel 4x4 sur Raspberry Pi, en testant les combinaisons de GPIO et en
#     construisant une table de correspondance touche -> (GPIO_out, GPIO_in).
#
#  Principe :
#     - Toutes les broches candidates (ALL_PINS) sont mises en entrée avec pull-up.
#     - Le programme “balaye” ensuite chaque broche en la passant temporairement
#       en sortie à 0, puis lit les autres broches : si une broche lue passe à 0,
#       cela indique qu’une touche relie la paire (out_pin, in_pin).
#     - L’utilisateur saisit le nom de la touche (ex: "1", "2", "A"...), et le
#       script enregistre la paire détectée dans un dictionnaire mapping.
#
#  Configuration matérielle (GPIO testés) :
#     - ALL_PINS = [5, 6, 13, 16, 19, 20, 22, 26]
#     - Accès GPIO via lgpio (chip = gpiochip_open(0))
#     - Pull-up activé sur chaque pin en mode entrée (SET_PULL_UP)
#
#  Entrée principale :
#     - Script standalone (exécution directe) : boucle interactive jusqu’à Ctrl+C.
#
#  Sorties / résultats :
#     - Affiche un résumé : touche -> (GPIOout ↔ GPIOin)
#     - Déduit une proposition de configuration :
#         * ROW_PINS = liste des out_pin vus
#         * COL_PINS = liste des in_pin vus
#     - Génère un tableau KEY_PAD “approximatif” (matrice rows x cols) à partir
#       des mappings saisis.
#
#  Dépendances :
#     - lgpio (accès GPIO bas niveau)
#     - time (temporisations de balayage)
#
#  Notes :
#     - Le balayage utilise une petite temporisation (2ms) après claim_output pour
#       laisser le niveau se stabiliser.
#     - En fin de programme : fermeture du chip (gpiochip_close) en finally.
#     - Le mapping dépend de l’ordre de détection et des pins choisies dans ALL_PINS.
# ============================================================================

import lgpio
import time

ALL_PINS = [5, 6, 13, 16, 19, 20, 22, 26]
chip = lgpio.gpiochip_open(0)

# Met toutes les broches en entrée avec pull-up
for p in ALL_PINS:
    lgpio.gpio_claim_input(chip, p, lgpio.SET_PULL_UP)

print("=== MODE APPRENTISSAGE CLAVIER 4x4 ===")
print("Appuie sur une touche, puis entre son nom (ex: 1, 2, A, B...)")
print("Quand tu as fini, fais Ctrl+C pour quitter.\n")

mapping = {}

try:
    while True:
        detected = None
        # Balayage de toutes les combinaisons
        for out_pin in ALL_PINS:
            lgpio.gpio_claim_output(chip, out_pin, 0)
            time.sleep(0.002)
            for in_pin in ALL_PINS:
                if in_pin != out_pin and lgpio.gpio_read(chip, in_pin) == 0:
                    detected = (out_pin, in_pin)
            lgpio.gpio_claim_input(chip, out_pin, lgpio.SET_PULL_UP)

        if detected:
            out_pin, in_pin = detected
            key = input(f"Touche détectée entre GPIO{out_pin} et GPIO{in_pin}. "
                        f"Nom de la touche ? ")
            mapping[key.strip()] = (out_pin, in_pin)
            print(f"✅ Enregistré : {key.strip()} → ({out_pin}, {in_pin})\n")
            time.sleep(0.5)
        else:
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\n=== Fin de l'apprentissage ===")

finally:
    lgpio.gpiochip_close(chip)

# Affiche le mapping complet
if mapping:
    print("\n--- Résumé des correspondances ---")
    for k, v in mapping.items():
        print(f"{k}: GPIO{v[0]} ↔ GPIO{v[1]}")

    # Déduit automatiquement les groupes de lignes et colonnes
    all_outs = sorted(set([v[0] for v in mapping.values()]))
    all_ins = sorted(set([v[1] for v in mapping.values()]))
    print("\n--- Proposition de configuration ---")
    print(f"ROW_PINS = {all_outs}")
    print(f"COL_PINS = {all_ins}")

    # Crée une matrice brute pour KEY_PAD
    print("\n--- Tableau KEY_PAD approximatif ---")
    rows = list(all_outs)
    cols = list(all_ins)
    pad = [[" " for _ in cols] for _ in rows]
    for k, (r, c) in mapping.items():
        ri, ci = rows.index(r), cols.index(c)
        pad[ri][ci] = k
    for row in pad:
        print(row)
