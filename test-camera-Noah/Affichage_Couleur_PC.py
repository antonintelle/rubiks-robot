import cv2
import numpy as np

# Initialisation de la capture webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Conversion BGR vers HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Définition des plages HSV pour chaque couleur du Rubik's Cube

    # Rouge (deux plages car le rouge HSV est discontinu)
    lower_red1 = np.array([0, 186, 105])
    upper_red1 = np.array([10, 255, 138])
    lower_red2 = np.array([169, 147, 100])
    upper_red2 = np.array([179, 255, 142])

    # Bleu
    lower_blue = np.array([105, 226, 130])
    upper_blue = np.array([113, 255, 255])

    # Vert
    lower_green = np.array([52, 16, 69])
    upper_green = np.array([86, 149, 180])

    # Jaune
    lower_yellow = np.array([19, 98, 160])
    upper_yellow = np.array([27, 255, 255])

    # Orange
    lower_orange = np.array([9, 198, 154])
    upper_orange = np.array([17, 255, 255])

    # Blanc (faible saturation et haute valeur)
    lower_white = np.array([30, 1, 176])
    upper_white = np.array([141, 59, 255])

    # Masques pour chaque couleur
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    # Appliquer les masques pour chaque couleur
    res_red = cv2.bitwise_and(frame, frame, mask=mask_red)
    res_blue = cv2.bitwise_and(frame, frame, mask=mask_blue)
    res_green = cv2.bitwise_and(frame, frame, mask=mask_green)
    res_yellow = cv2.bitwise_and(frame, frame, mask=mask_yellow)
    res_orange = cv2.bitwise_and(frame, frame, mask=mask_orange)
    res_white = cv2.bitwise_and(frame, frame, mask=mask_white)

    # Affichage
    cv2.imshow('Original', frame)
    cv2.imshow('Rouge', res_red)
    cv2.imshow('Bleu', res_blue)
    cv2.imshow('Vert', res_green)
    cv2.imshow('Jaune', res_yellow)
    cv2.imshow('Orange', res_orange)
    cv2.imshow('Blanc', res_white)

    # Quitter avec la touche 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Relâcher la capture et fermer les fenêtres
cap.release()
cv2.destroyAllWindows()
