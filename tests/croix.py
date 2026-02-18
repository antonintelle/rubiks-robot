import time
import pigpio  # Assure-toi que pigpiod tourne: sudo systemctl start pigpiod

B_SERVO_PIN = 24  # GPIO du servo bottom
T_SERVO_PIN = 23  # GPIO du servo top

# Largeurs d'impulsions en microsecondes (ajuster si besoin)
LEFT_PW  = 850   # ~90gauche
LEFT_LOOSE_PW = LEFT_PW + 50

MID_PW   = 1500   # milieu
MIDL_LOOSE_PW = MID_PW - 50
MIDR_LOOSE_PW = MID_PW + 50

RIGHT_PW = 2150   # ~90 droite
RIGHT_LOOSE_PW = RIGHT_PW - 50

OPEN_PW = 1250       # couvercle ouvert
CLOSE_PW = 1500      # couvercle ferm
FLIP_PW = 800       # position pour retourner le cube

global cover_pos  # position du couvercle "open", "close" ou "flip"
global cube_pos   # position du cube "mid", "right", "left"

pi = pigpio.pi()
if not pi.connected:
    raise SystemExit("Impossible de se connecter pigpio (vrifie que pigpiod est dmarr).")

def move_to(pulsewidth, servo, wait=0.5):
    # pulsewidth en microsecondes (entre ~500 et 2500s)
    pi.set_servo_pulsewidth(servo, pulsewidth)
    time.sleep(wait)
    # On laisse le pulsewidth actif pendant les 3 s de pause
    # puis on coupe si on veut supprimer toute tension.
    # Ici on ne coupe pas tout de suite pour que le servo tienne bien sa position.

def move_slow(from_pw, to_pw, servo, step=10, delay=0.02):
    """
    Dplace le servo progressivement de from_pw to_pw.
    step : taille des pas en s
    delay : temps entre chaque pas en s
    """
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



# variable globale pour mmoriser la dernire pulsewidth de la position du couvercle
current_pw = OPEN_PW  # par exemple, au dpart il est ouvert

def flip_up():
    global cover_pos, current_pw

    # Aller doucement vers la position flip
    move_slow(current_pw, FLIP_PW, T_SERVO_PIN, step=10, delay=0.02)
    current_pw = FLIP_PW
    cover_pos = 'flip'

    # Puis doucement revenir la position open
    move_slow(current_pw, OPEN_PW, T_SERVO_PIN, step=10, delay=0.02)
    current_pw = OPEN_PW
    cover_pos = 'open'

    time.sleep(1)


def flip_open() :
    """ Fonction pour ouvrir le couvercle """

    global cover_pos

    move_to(OPEN_PW, T_SERVO_PIN)
    cover_pos = 'open'


def flip_close() :
    """ Fonction pour fermer le couvercle """

    global cover_pos

    move_to(CLOSE_PW, T_SERVO_PIN)
    cover_pos = 'close'


def spin_out(direction, rotate = False):
    """ Fonction pour faire tourner le cube de 90
        selon une direction "D" ou  "G"."""
    
    global cube_pos
    
    if direction == 'D':
        print("Tourne a droite")

        if rotate :
            move_to(RIGHT_PW + 50, B_SERVO_PIN)
            move_to(RIGHT_PW - 50, B_SERVO_PIN)
        else :
            move_to(RIGHT_PW, B_SERVO_PIN)
        cube_pos = 'right'

    elif direction == 'G':
        print("Tourne a gauche")

        if rotate :
            move_to(LEFT_PW + 50, B_SERVO_PIN)
            move_to(LEFT_PW - 50, B_SERVO_PIN)
        else :
            move_to(LEFT_PW, B_SERVO_PIN)

        cube_pos = 'left'


def spin_mid(rotate = False):
    """ Fonction pour mettre le cube en position centrale.
        Pendant ce mouvement le cube n'est pas contraint par le couvercle."""

    global cube_pos

    if rotate :
        move_to(MID_PW + 50, B_SERVO_PIN)
        move_to(MID_PW, B_SERVO_PIN)
        print("tourne mid + 50")
    else :
        move_to(MID_PW, B_SERVO_PIN)
    
    move_to(MID_PW, B_SERVO_PIN)
    cube_pos = 'mid'


def rotate_out(direction):
    """ Fonction pour faire tourner le cube de 90.
        Lors de la rotation le cube est contraint par le couvercle."""

    global cover_pos

    if cover_pos != 'close':
        flip_close()

    spin_out(direction, True)


def rotate_mid():
    """ Fonction pour mettre le cube en position centrale. 
        Lors de la rotation le cube est contraint par le couvercle."""

    global cube_pos

    if cover_pos != 'close':
        flip_close()

    if cube_pos == 'right' :
        spin_mid(True)
    elif cube_pos == 'left' :
        spin_mid(True)
    cube_pos = 'mid'

def victory():
    move_to(MID_PW + 150, B_SERVO_PIN)
    move_to(MID_PW - 150, B_SERVO_PIN)
    move_to(MID_PW + 150, B_SERVO_PIN)
    move_to(MID_PW - 150, B_SERVO_PIN)
    move_to(MID_PW + 150, B_SERVO_PIN)
    move_to(MID_PW - 150, B_SERVO_PIN)
    move_to(MID_PW + 150, B_SERVO_PIN)
    move_to(MID_PW - 150, B_SERVO_PIN)
    spin_mid()

try:
    cover_pos = 'open'
    cube_pos = 'mid'

    spin_mid()
    flip_open()
    print("Posez le cube")
    time.sleep(3)

    print("Cration de la croix")
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
    victory()

    # Option: couper le servo pour viter tout bruit une fois termin
    pi.set_servo_pulsewidth(B_SERVO_PIN, 0)
    time.sleep(0.2)

finally:
    pi.stop()
    print("pigpio arr, fin du programme.")
 
