#!/usr/bin/env python3
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
