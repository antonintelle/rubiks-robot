#!/usr/bin/env python3
# ============================================================================
#  test_solveur_robot.py
#  ---------------------
#  Objectif :
#     Script de test “ultra simple” pour lancer en console le **mode manuel**
#     d’exécution des mouvements Singmaster sur le robot.
#     Il sert principalement à valider rapidement que :
#       - le module hardware (robot_servo) est accessible,
#       - la boucle interactive `manual_singmaster_loop_cubotino()` fonctionne,
#       - le robot exécute correctement une séquence saisie à la main.
#
#  Entrée principale :
#     - Exécution directe (__main__) :
#         python3 test_solveur_robot.py
#         -> Lance immédiatement la boucle interactive.
#
#  Fonction appelée :
#     - robot_servo.manual_singmaster_loop_cubotino()
#         Menu / loop de saisie :
#           * l’utilisateur tape une solution Singmaster (ex: "R U R' U'")
#           * le robot exécute la séquence via la couche Cubotino (robot_moves_cubotino)
#
#  Dépendances :
#     - robot_servo (pilotage servos + interface de test)
#     - time (importé mais non utilisé dans ce script)
#
#  Notes :
#     - Ce fichier est volontairement minimal : c’est un “raccourci” vers le mode test
#       déjà implémenté dans robot_servo.py.
# ============================================================================


import time
import robot_servo as rs

rs.manual_singmaster_loop_cubotino()
