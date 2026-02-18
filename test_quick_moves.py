#!/usr/bin/env python3
# ============================================================================
#  test_quick_moves.py
#  -------------------
#  Objectif :
#     Script de **test manuel rapide** des primitives mécaniques (robot_servo.py),
#     afin de valider :
#       - la cohérence des états internes (cube_pos / cover_pos),
#       - la rotation contrainte à droite (D) puis retour au centre,
#       - la rotation contrainte à gauche (G) puis retour au centre,
#     avec une interaction utilisateur entre les étapes pour surveiller l’effort
#     et stopper immédiatement en cas de contrainte anormale.
#
#  Entrée principale :
#     - Exécution directe (__main__) :
#         python3 test_quick_moves.py
#         -> Enchaîne une séquence “courte” de mouvements et affiche l’état avant/après.
#
#  Dépendances :
#     - robot_servo as rs : fournit reset_initial, flip_close/open, spin_out, rotate_mid,
#       et expose les variables globales rs.cube_pos et rs.cover_pos.
#     - time (importé mais non utilisé ici, peut servir si tu ajoutes des pauses).
#
#  Organisation du test :
#     - Helpers :
#         * state(tag) : print état courant (cube_pos, cover_pos)
#         * step(title, fn, pause=True) :
#             affiche un titre, log “avant/après”, exécute fn(),
#             puis attend [Entrée] (sauf pause=False) pour sécuriser.
#
#     - Séquence test :
#         1) Bloc DROITE (rotation contrainte) :
#            [0] reset_initial()
#            [1] flip_close()
#            [2] spin_out("D", rotate=True)     (sans pause intermédiaire)
#            [3] flip_open()
#            [4] rotate_mid()                  (retour centre “normal”)
#
#         2) Bloc GAUCHE (rotation contrainte) :
#            [5] reset_initial()
#            [6] flip_close()
#            [7] spin_out("G", rotate=True)     (sans pause intermédiaire)
#            [8] flip_open()
#            [9] rotate_mid()                  (retour centre “normal”)
#
#  Notes :
#     - Le prompt “Entrée pour continuer (stop si effort anormal)” est volontaire :
#       ce test sert à observer mécaniquement l’angle atteint avant ré-ouverture
#       du capot et à valider que rotate_mid() ramène correctement au centre.
#     - Le script imprime deux messages de fin (“Fin du test normal…”), redondant
#       mais sans impact fonctionnel.
# ============================================================================

import time
import robot_servo as rs

def state(tag):
    print(f"{tag}: cube_pos={rs.cube_pos}, cover_pos={rs.cover_pos}")

def step(title, fn, pause=True):
    print("\n" + "-"*60)
    print(title)
    print("-"*60)
    state("avant")
    fn()
    state("après")
    if pause:
        input("Entrée pour continuer (stop si effort anormal) ")

print("="*60)
print("TEST NORMAL — primitives Cubotino-like (court)")
print("="*60)

# ---- BLOC DROITE (contrainte, observation angle avant ouverture) ----
step("[0] reset_initial()", rs.reset_initial)
step("[1] flip_close()", rs.flip_close)
step("[2] spin_out('D', rotate=True)", lambda: rs.spin_out("D", rotate=True), pause=False)
step("[3] flip_open()", rs.flip_open)

# Retour centre "normal" (comme en exécution de solution)
step("[4] rotate_mid()", rs.rotate_mid)

# ---- BLOC GAUCHE (contrainte, observation angle avant ouverture) ----
step("[5] reset_initial()", rs.reset_initial)
step("[6] flip_close()", rs.flip_close)
step("[7] spin_out('G', rotate=True)", lambda: rs.spin_out("G", rotate=True), pause=False)
step("[8] flip_open()", rs.flip_open)

# Retour centre "normal"
step("[9] rotate_mid()", rs.rotate_mid)

print("\n✅ Fin du test normal figé.")


print("\n✅ Fin du test normal.")
