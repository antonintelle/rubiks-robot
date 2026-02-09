# ============================================================================
#  robot_servo.py
#  ----------------
#  Objectif :
#     Gérer l’ensemble des fonctions matérielles du robot Rubik’s Cube :
#     initialisation pigpio, contrôle des servos, mouvements mécaniques
#     (rotation du cube, ouverture/fermeture du couvercle, retournement, etc.).
#
#  Fonctions principales :
#     - move_to(pulsewidth, servo, wait=0.5) :
#         Commande bas-niveau : envoie une largeur d’impulsion PWM sur un servo.
#
#     - move_slow(from_pw, to_pw, servo, step, delay) :
#         Mouvement progressif en micropas, évite les à-coups mécaniques.
#
#     - flip_open(), flip_close(), flip_up() :
#         Contrôle du couvercle (servo top) : ouverture, fermeture, retournement.
#
#     - spin_out(direction, rotate=False) :
#         Rotation libre du cube vers 'D' (droite) ou 'G' (gauche).
#
#     - spin_mid(rotate=False) :
#         Recentrage du cube en position centrale.
#
#     - rotate_out(direction) :
#         Rotation contrainte du cube sous couvercle fermé (mouvement Singmaster).
#
#     - rotate_mid() :
#         Recentrage contraint après rotation.
#
#     - test_manual_pwm() :
#         Mode de calibration manuel du servo bas (PWM).
#
#     - hardware_test() :
#         Menu interactif pour tester couvercle, rotations libres, contraintes, etc.
#
#  IMPORTANT :
#     - Ce module centralise toutes les commandes matérielles.
#     - Toujours garantir un pi.stop() en fin de programme (try/finally ou main).
#
# ============================================================================

import time
import pigpio  # Assure-toi que pigpiod tourne: sudo systemctl start pigpiod

# GPIO des servos (choix B : nouveau câblage)
B_SERVO_PIN = 24  # servo inférieur (rotation cube)
T_SERVO_PIN = 23  # servo supérieur (couvercle)

# Largeurs d'impulsions en microsecondes (à ajuster si besoin)
LEFT_PW  = 850    # ~90° gauche
LEFT_LOOSE_PW = LEFT_PW + 50

MID_PW   = 1500   # milieu
MIDL_LOOSE_PW = MID_PW - 20
MIDR_LOOSE_PW = MID_PW + 20

RIGHT_PW = 2150   # ~90° droite
RIGHT_LOOSE_PW = RIGHT_PW - 50

OPEN_PW  = 1250   # couvercle ouvert
#CLOSE_PW = 1500  # couvercle fermé
CLOSE_PW = 1500   # couvercle fermé
FLIP_PW  = 800    # position pour retourner le cube

COVER_RELEASE = 15      # µs, à ajuster plus tard
COVER_CLOSE_WAIT = 0.35 # s
COVER_REL_WAIT = 0.15   # s
ROT_OVERSHOOT = 0
B_OFFSET = -0 #### OFFSET pour le centrage du plateau inclus dans les move (attention les 2 cotés en même temps)
RIGHT_TRIM = +30  # µs -- centrage du plateau à droite
LEFT_TRIM  = -10  # µs -- centrage du plateau à gauche 
MID_TRIM_CONSTRAINED = +10  # pour retour du cube au centre

# --- STABILITÉ (Rubik's plus dur) ---
COVER_LOCK_SETTLE = 0.25   # pause après flip_close avant rotation contrainte
B_WAIT_FREE = 0.65         # attente fin de spin libres
B_WAIT_ROT  = 0.90         # attente fin de rotations contraintes (rotate=True)
ROTATE_HOLD = 0.70         # tenir capot fermé après rotation avant ouverture
SPIN_SETTLE = 0.12         # petite pause anti-oscillation après spin


# Positions globales
cover_pos = "open"   # position du couvercle "open", "close" ou "flip"
cube_pos  = "mid"    # position du cube "mid", "right", "left"

# variable globale pour mémoriser la dernière pulsewidth de la position du couvercle
current_pw = OPEN_PW  # par exemple, au départ il est ouvert

# Connexion pigpio
pi = pigpio.pi()
if not pi.connected:
    raise SystemExit("Impossible de se connecter à pigpio (vérifie que pigpiod est démarré).")


# ============================================================================
# BAS NIVEAU
# ============================================================================

def move_to(pulsewidth, servo, wait=0.5):
    """
    pulsewidth en microsecondes (entre ~500 et 2500 µs)
    Envoie la largeur d’impulsion au servo et attend 'wait' secondes.
    """
    if servo == B_SERVO_PIN:
        pulsewidth = pulsewidth + B_OFFSET    
        print(f"[move_to] B servo raw={pulsewidth-B_OFFSET} offset={B_OFFSET} sent={pulsewidth}")
    pi.set_servo_pulsewidth(servo, pulsewidth)
    time.sleep(wait)
    # On laisse le pulsewidth actif pendant la pause
    # pour que le servo tienne bien sa position.


def move_slow(from_pw, to_pw, servo, step=10, delay=0.02):
    """
    Déplace le servo progressivement de from_pw à to_pw.
    step : taille des pas en µs
    delay : temps entre chaque pas en s
    """
    if servo == B_SERVO_PIN:
        from_pw += B_OFFSET
        to_pw += B_OFFSET

    if from_pw < to_pw:
        pw = from_pw
        while pw <= to_pw:
            pi.set_servo_pulsewidth(servo, pw)
            time.sleep(delay)
            pw += step
    else:
        pw = from_pw
        while pw >= to_pw:
            pi.set_servo_pulsewidth(servo, pw)
            time.sleep(delay)
            pw -= step
    # on termine exactement sur la valeur cible
    pi.set_servo_pulsewidth(servo, to_pw)


# ============================================================================
# COUVERCLE (servo top)
# ============================================================================

def flip_up():
    """
    Fonction pour retourner le cube via le couvercle :
    - va en position FLIP_PW
    - ATTEND que le cube bascule
    - puis revient à OPEN_PW
    """
    global cover_pos, current_pw

    # Aller vers position flip
    move_slow(current_pw, FLIP_PW, T_SERVO_PIN, step=10, delay=0.02)
    current_pw = FLIP_PW
    cover_pos = 'flip'
    
    time.sleep(0.5)  # ✅ ATTENDRE que cube bascule (AVANT retour)
    
    # Revenir à open
    move_slow(current_pw, OPEN_PW, T_SERVO_PIN, step=10, delay=0.02)
    current_pw = OPEN_PW
    cover_pos = 'open'
    time.sleep(0.3)

def flip_open():
    """ Fonction pour ouvrir le couvercle """

    global cover_pos, current_pw

    move_to(OPEN_PW, T_SERVO_PIN)
    current_pw = OPEN_PW
    cover_pos = 'open'
    time.sleep(0.3)


def flip_close():
    """ Fonction pour fermer le couvercle (avec micro-release anti-cisaillement) """

    global cover_pos, current_pw

    move_to(CLOSE_PW, T_SERVO_PIN, wait=COVER_CLOSE_WAIT)

    # micro release: relâche un poil la pression
    move_to(CLOSE_PW - COVER_RELEASE, T_SERVO_PIN, wait=COVER_REL_WAIT)

    current_pw = CLOSE_PW - COVER_RELEASE
    cover_pos = 'close'


# ============================================================================
# SERVO BAS — ROTATION CUBE (libre)
# ============================================================================

def spin_out(direction, rotate=False):
    """ Fonction pour faire tourner le cube de 90
        selon une direction "D" ou  "G"."""

    global cube_pos, cover_pos
    
    if not rotate and cover_pos != 'open':
        flip_open()
    
    w = B_WAIT_ROT if rotate else B_WAIT_FREE

    if direction == 'D':
        print("Tourne a droite")
        target = RIGHT_PW + RIGHT_TRIM
        #print(f"[spin_out] dir={direction} RIGHT_TRIM={RIGHT_TRIM} target={target} ROT_OVERSHOOT={ROT_OVERSHOOT}")
        if rotate:
            move_to(target + ROT_OVERSHOOT, B_SERVO_PIN,wait=w)
            move_to(target, B_SERVO_PIN,wait=w)   # <- settle sur la cible
        else:
            move_to(target, B_SERVO_PIN,wait=w)
        cube_pos = 'right'

    elif direction == 'G':
        print("Tourne a gauche")
        target = LEFT_PW + LEFT_TRIM
        #print(f"[spin_out] dir={direction} LEFT_TRIM={LEFT_TRIM} target={target} ROT_OVERSHOOT={ROT_OVERSHOOT}")       
        if rotate:
            move_to(target - ROT_OVERSHOOT, B_SERVO_PIN,wait=w)  # overshoot de l'autre côté
            move_to(target, B_SERVO_PIN,wait=w)       # <- settle sur la cible
        else:
            move_to(target, B_SERVO_PIN,wait=w)

        cube_pos = 'left'
    time.sleep(SPIN_SETTLE)

def spin_mid(rotate=False):
    global cube_pos
    if rotate:
        if cube_pos == 'right':
            move_to(MIDL_LOOSE_PW, B_SERVO_PIN, wait=0.6)
            move_to(MID_PW + MID_TRIM_CONSTRAINED, B_SERVO_PIN, wait=0.6)
        elif cube_pos == 'left':
            move_to(MIDR_LOOSE_PW, B_SERVO_PIN, wait=0.5)
            move_to(MID_PW + MID_TRIM_CONSTRAINED, B_SERVO_PIN, wait=0.6)
        else:
            move_to(MID_PW + MID_TRIM_CONSTRAINED, B_SERVO_PIN, wait=0.6)
    else:
        move_to(MID_PW, B_SERVO_PIN,wait=0.6)
    cube_pos = 'mid'
    time.sleep(SPIN_SETTLE)

# ============================================================================
# PRIMITIVES ROTATION CONTRAINTE (mouvements Singmaster)
# ============================================================================

def rotate_out(direction):
    global cover_pos
    if cover_pos != 'close':
        flip_close()
        time.sleep(COVER_LOCK_SETTLE)
    spin_out(direction, True)
    time.sleep(ROTATE_HOLD)
    flip_open()

def rotate_mid():
    global cube_pos, cover_pos
    if cover_pos != 'close':
        flip_close()
        time.sleep(0.15)
    if cube_pos in ('right', 'left'):
        spin_mid(True)
    cube_pos = 'mid'
    time.sleep(ROTATE_HOLD)
    flip_open()

# ============================================================================
# MODE CALIBRATION : TEST MANUEL PWM
# ============================================================================

def test_manual_pwm():
    """
    Mode de test manuel pour le servo bas.
    Permet d'envoyer des PWM directement ou via des raccourcis :
      - M : aller au milieu (MID_PW)
      - L : aller à gauche (LEFT_PW)
      - R : aller à droite (RIGHT_PW)
      - +10 / -10 : ajuster finement
      - nombre : PWM direct
      - Q : quitter
    """

    print("=== MODE TEST MANUEL PWM ===")
    print("Commandes disponibles :")
    print("  M  → aller au milieu (MID_PW)")
    print("  L  → aller à gauche  (LEFT_PW)")
    print("  R  → aller à droite  (RIGHT_PW)")
    print("  +10 / -10 → ajuster finement (incrément)")
    print("  nombre → envoyer directement ce PWM")
    print("  Q → quitter")
    print("-----------------------------------")

    # Commencer au milieu (ne touche pas au couvercle ici)
    current = MID_PW
    move_to(current, B_SERVO_PIN)
    print(f"Position initiale : MID = {current}")

    while True:
        val = input("PWM / commande = ").strip().upper()

        if val == "Q":
            print("Fin du test manuel PWM.")
            break

        elif val == "M":
            current = MID_PW

        elif val == "L":
            current = LEFT_PW

        elif val == "R":
            current = RIGHT_PW

        elif val.startswith("+"):
            try:
                delta = int(val)
                current += delta
            except ValueError:
                print("Commande + invalide.")
                continue

        elif val.startswith("-"):
            try:
                delta = int(val)
                current += delta
            except ValueError:
                print("Commande - invalide.")
                continue

        else:
            # Essayer d'interpréter comme un PWM direct
            try:
                current = int(val)
            except ValueError:
                print("Commande invalide.")
                continue

        # Limites de sécurité
        if current < 500:
            current = 500
        if current > 2500:
            current = 2500

        move_to(current, B_SERVO_PIN)
        print(f"→ Servo bas envoyé à {current} µs")


# ============================================================================
# TESTS MOTEURS — SIMPLE
# ============================================================================
def reset_silent():
    """
    Coupe la PWM des servos (silence moteur) sans modifier l'état mécanique.
    Utile quand on veut arrêter les vibrations.
    """
    print("\n=== RESET SILENCIEUX (RS) ===")
    try:
        pi.set_servo_pulsewidth(B_SERVO_PIN, 0)
        pi.set_servo_pulsewidth(T_SERVO_PIN, 0)
        time.sleep(0.2)
        print("✔ Servos désactivés (silence).")
    except Exception as e:
        print(f"❌ Erreur RS : {e}")

def calibration_plateau():
    """
    Calibration du plateau :
    1) Aller au MID physique (servo bas)
    2) Fermer le capot (tenir le cube)
    3) L'utilisateur tourne et revisse le plateau pour aligner parfaitement
    """
    print("\n=== CALIBRATION PLATEAU (CP) ===")

    try:
        # 1) Mettre le servo bas en MID
        print("→ Mise en position MID du plateau…")
        flip_open()
        time.sleep(0.2)
        spin_mid()
        time.sleep(0.2)

        # 2) Fermer le capot pour tenir le cube
        print("→ Fermez le capot pour bloquer le cube.")
        flip_close()
        time.sleep(0.2)

        print("\n=========================================")
        print(" ALIGNEMENT PLATEAU")
        print(" Tournez délicatement le plateau à la main")
        print(" pour que le cube soit EXACTEMENT droit.")
        print(" (Face avant vers toi, aucune rotation latérale)")
        print(" Puis revissez la vis du plateau si nécessaire.")
        print(" Appuyez sur Entrée quand terminé.")
        print("=========================================\n")

        input(">> Appuyez Entrée quand le plateau est aligné... ")

        # 3) Réouverture + double mid
        flip_open()
        spin_mid()
        spin_mid()

        print("✔ Calibration terminée. Plateau aligné.")
    except Exception as e:
        print(f"❌ Erreur CP : {e}")

def reset_rotation():
    """
    Recalage de la rotation du plateau uniquement.
    Utile si la base semble légèrement décalée.
    """
    print("\n=== RESET ROTATION (RR) ===")

    try:
        # Capot fermé = rotation contrainte valide
        flip_close()
        time.sleep(0.2)

        rotate_mid()
        time.sleep(0.3)

        # Réouverture + double mid
        flip_open()
        spin_mid()
        spin_mid()

        print("✔ Rotation du plateau recalée.")
    except Exception as e:
        print(f"❌ Erreur RR : {e}")

def reset_initial():
    """
    Réinitialisation rapide du robot :
    - Capot ouvert
    - Plateau centré
    - Sans couper pigpio
    - Sans flips ou rotations inutiles
    """
    print("\n=== RESET INITIAL (RI) ===")

    try:
        # Capot ouvert
        flip_open()
        time.sleep(0.2)

        # Centrage du plateau
        spin_mid()
        time.sleep(0.2)
        #spin_mid()  # double mid pour garantir l'alignement
        #time.sleep(0.2)

        # Mise à jour des états globaux
        global cover_pos, cube_pos
        cover_pos = 'open'
        cube_pos = 'mid'

        print("✔ Robot remis à l'état initial.\n")

    except Exception as e:
        print(f"❌ Erreur dans RI : {e}")


# ============================================================================
# DEMO ROBOT — SÉQUENCE D’ORIGINE (création de la croix, etc.)
# ============================================================================

def hardware_demo_sequence():
    """Reproduction exacte du  script CROIX de démonstration (séquence complète)."""
    print("=== DEMO ROBOT : séquence complète ===")

    try:
        global cover_pos, cube_pos

        cover_pos = 'open'
        cube_pos = 'mid'

        spin_mid()
        flip_open()
        print("Posez le cube")
        time.sleep(3)

        print("Création de la croix")
        spin_out('G')
        rotate_out('D')
        rotate_out('D')
        flip_up()
        flip_up()
        rotate_out('G')
        rotate_out('G')
        flip_open()

        flip_up()

        spin_out('G')
        rotate_out('D')
        rotate_out('D')
        flip_up()
        flip_up()
        rotate_out('G')
        rotate_out('G')
        flip_open()

        spin_mid()
        flip_up()
        spin_out('G')
        rotate_out('D')
        rotate_out('D')
        flip_up()
        flip_up()
        rotate_out('G')
        rotate_out('G')

        flip_open()

        pi.set_servo_pulsewidth(B_SERVO_PIN, 0)
        time.sleep(0.2)

        print("=== Démonstration complète terminée ===")

    except Exception as e:
        print("Erreur dans la démo robot :", e)

    finally:
        print("pigpio arrêté, fin de la démo.")

# ============================================================================
# TEST — SAISIE MANUELLE (Cubotino adapter)
# ============================================================================
def manual_singmaster_loop_cubotino():
    """
    Mode interactif: saisie d'une chaîne Singmaster et exécution immédiate
    via robot_moves_cubotino (algo Cubotino -> F/S/R -> robot_servo).
    """
    import robot_moves_cubotino as rm

    help_txt = """
Saisie Singmaster (espaces optionnels).
Exemples:
  L'
  L L'
  U R2 F' L B D'
  RUR'U'          (sans espaces)

Commandes:
  help                 -> aide
  status               -> affiche options
  reset on/off         -> reset_initial automatique avant chaque commande
  start ufr/scan       -> orientation de départ (UFR ou AFTER_SCAN)
  dry on/off           -> n'actionne pas les servos (affiche seulement)
  verbose on/off       -> logs détaillés
  compile <seq>        -> affiche la séquence robot F/S/R sans exécuter
  ri                   -> reset_initial maintenant
  open                 -> ouvre le capot
  close                -> ferme le capot
  quit                 -> sortir
"""

    reset_each = True
    start_mode = "UFR"      # ou "AFTER_SCAN"
    dry_run = False
    verbose = True

    def _normalize(s: str) -> str:
        return s.replace("’", "'").replace("‘", "'").strip()

    print("=" * 60)
    print("ROBOT MOVES — MODE MANUEL SINGMASTER (CUBOTINO)")
    print("=" * 60)
    print(help_txt)

    while True:
        try:
            s = input("\nSM> ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        s = _normalize(s)
        if not s:
            continue

        cmd = s.lower().strip()

        # --- commandes ---
        if cmd in ("quit", "exit", "q"):
            print("Bye.")
            break

        if cmd == "help":
            print(help_txt)
            continue

        if cmd == "status":
            # état "vu" depuis ce module (robot_servo.py)
            print(f"reset_each = {reset_each}")
            print(f"start_mode  = {start_mode}")
            print(f"dry_run     = {dry_run}")
            print(f"verbose     = {verbose}")
            print(f"servo.cube_pos  = {cube_pos}")
            print(f"servo.cover_pos = {cover_pos}")

            # état "vu" depuis l'adapter (robot_moves_cubotino -> rm.hw)
            hw = getattr(rm, "hw", None)
            if hw is not None:
                print(f"rm.hw.cube_pos  = {getattr(hw, 'cube_pos', 'MISSING')}")
                print(f"rm.hw.cover_pos = {getattr(hw, 'cover_pos', 'MISSING')}")
                print(f"rm.hw.__file__  = {getattr(hw, '__file__', 'unknown')}")
            print(f"servo.__file__  = {__file__}")
            continue

        if cmd in ("reset on", "reset_on"):
            reset_each = True
            print("✅ reset_each = True")
            continue

        if cmd in ("reset off", "reset_off"):
            reset_each = False
            print("✅ reset_each = False")
            continue

        if cmd in ("start ufr", "start_ufr"):
            start_mode = "UFR"
            print("✅ start_mode = UFR")
            continue

        if cmd in ("start scan", "start_after_scan", "start after_scan"):
            start_mode = "AFTER_SCAN"
            print("✅ start_mode = AFTER_SCAN")
            continue

        if cmd in ("dry on", "dry_on"):
            dry_run = True
            print("✅ dry_run = True")
            continue

        if cmd in ("dry off", "dry_off"):
            dry_run = False
            print("✅ dry_run = False")
            continue

        if cmd in ("verbose on", "v on", "verbose_on"):
            verbose = True
            print("✅ verbose = True")
            continue

        if cmd in ("verbose off", "v off", "verbose_off"):
            verbose = False
            print("✅ verbose = False")
            continue

        if cmd in ("ri", "reset_initial", "reset"):
            reset_initial()
            print("✅ RI OK.")
            continue

        if cmd in ("open", "capot open"):
            flip_open()
            print("✅ Capot ouvert.")
            continue

        if cmd in ("close", "capot close"):
            flip_close()
            print("✅ Capot fermé.")
            continue

        # compile <seq>
        if cmd.startswith("compile "):
            seq = _normalize(s[len("compile "):])
            try:
                moves_str, tot = rm.compile_robot_moves(seq, start_mode=start_mode)
                print(f"Robot moves: {moves_str} | Total: {tot}")
            except Exception as e:
                print(f"❌ Erreur compile: {e}")
            continue

        if cmd == "compile":
            print("Usage: compile <sequence_singmaster>")
            continue

        # --- exécution par défaut ---
        try:
            if reset_each:
                reset_initial()

            moves_str = rm.execute_solution(
                s,
                start_mode=start_mode,
                dry_run=dry_run,
                verbose=verbose,
            )
            if not verbose:
                print(f"✅ OK | moves={moves_str}")

        except Exception as e:
            print(f"❌ Erreur: {e}")



def hardware_test():
    """
    Menu interactif pour tester :
      - le couvercle (ouvrir / fermer / flip)
      - les rotations libres 90° (capot ouvert)
      - les rotations contraintes (capot fermé)
      - la calibration PWM (M1 / M2)
    """

    from robot_moves_cubotino import return_to_u_fr,step_yaw90_to_mid, step_flip, step_yaw
    global cover_pos, cube_pos

    print("=== HARDWARE TEST : démarrage ===")

    # État initial
    cover_pos = 'open'
    cube_pos = 'mid'
    flip_open()
    spin_mid()

    while True:
        print("""
=== MENU TEST MATÉRIEL ===
-- COUVERCLE --
  O) Ouvrir capot
  F ou C) Fermer capot  
  U) Flip complet (flip_up)
-- OUTILS --
  RI) Reset Initial (capot ouvert + mid)
  RS) Reset Silencieux (coupe les servos)
  RR) Reset Rotation (recalage plateau)
  CP) Calibration Plateau (alignement mécanique)
-- TESTS MOVE --
  T2) Faire la croix (ou retour état initial)
-- TEST SINGMASTER --
  SM) Saisie manuelle d'une séquence
-- TESTS ACTIONS --
UFR) Retour à l'état UFR
-- AUTRES --
  S) Afficher l'état (state)
-- SERVO BAS (yaw / plateau) --
  BD) spin_out("D")  (droite OUT)
  BG) spin_out("G")  (gauche OUT)
  BM) spin_mid()     (centre MID)
  YD) step_yaw90_to_mid("D") (pas 90° sens droite, finit MID)
  YG) step_yaw90_to_mid("G") (pas 90° sens gauche, finit MID)
  FD) step_yaw("D")
  FG) step_yaw("G")
  FU) flip_up()              
  Q) Quitter
==========================
""")

        choix = input("Ton choix : ").upper().strip()

        # -------------------
        # COUVERCLE
        # -------------------
        if choix == "O":
            flip_open()
        elif choix in ("C","F"):
            flip_close()
        elif choix == "U":
            flip_up()

        # -------------------
        # OUTILS
        # -------------------
        elif choix == "RI":
            reset_initial()
        elif choix == "RS":
            reset_silent()
        elif choix == "RR":
            reset_rotation()
        elif choix == "CP":
            calibration_plateau()

        # -------------------
        # TEST COMPLET
        # -------------------
        elif choix == "T2":
            hardware_demo_sequence()
        # -------------------
        # TEST SINGMASTER
        # -------------------
        elif choix == "SM":
            manual_singmaster_loop_cubotino()

        # -------------------
        # TESTS ACTIONS
        # -------------------
        elif choix == "UFR":
            return_to_u_fr()
        elif choix == "BD":
            spin_out("D")   # yaw droite, capot doit être open (ton spin_out le force si rotate=False)
        elif choix == "BG":
            spin_out("G")   # yaw gauche
        elif choix == "BM":
            flip_open()
            spin_mid()      # retour milieu      
        elif choix == "YD":
            step_yaw90_to_mid("D") 
        elif choix == "YG":
            step_yaw90_to_mid("G")   
        elif choix == "FD":
            step_yaw("D")
        elif choix == "FG":
            step_yaw("G")    
        elif choix == "FU":
            flip_up()                                                     
        # QUITTER
        # -------------------
        elif choix == "Q":
            print(">>> Fin du test.")
            break
        elif choix == "S":
            pass
        else:
            print(">>> Option invalide.")
        print(f"[STATE] cover_pos={cover_pos} | cube_pos={cube_pos}")

    # -------------------
    # RESET + ARRET PIGPIO
    # -------------------
    print(">>> Reset servos & arrêt pigpio")
    pi.set_servo_pulsewidth(B_SERVO_PIN, 0)
    pi.set_servo_pulsewidth(T_SERVO_PIN, 0)
    time.sleep(0.2)
    print(">>> pigpio arrêté.")


# ============================================================================
# MAIN — lance hardware_test pour validation
# ============================================================================

if __name__ == "__main__":
    try:
        hardware_test()
        #   ()
    finally:
        pi.stop()
