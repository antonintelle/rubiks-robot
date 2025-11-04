import cv2
import numpy as np
import csv
import time

cap = cv2.VideoCapture(0)

# Ouvrir un fichier CSV pour écrire les données
with open('detection_couleurs.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Timestamp_ms', 'Couleur', 'X_center', 'Y_center'])

    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Définition des plages HSV (même qu’avant)
        lower_red1 = np.array([0, 186, 105])
        upper_red1 = np.array([10, 255, 138])
        lower_red2 = np.array([169, 147, 100])
        upper_red2 = np.array([179, 255, 142])

        lower_blue = np.array([105, 226, 130])
        upper_blue = np.array([113, 255, 255])

        lower_green = np.array([52, 16, 69])
        upper_green = np.array([86, 149, 180])

        lower_yellow = np.array([19, 98, 160])
        upper_yellow = np.array([27, 255, 255])

        lower_orange = np.array([9, 198, 154])
        upper_orange = np.array([17, 255, 255])

        lower_white = np.array([30, 1, 176])
        upper_white = np.array([141, 59, 255])

        # Masques
        masks = {
            'Rouge': cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2),
            'Bleu': cv2.inRange(hsv, lower_blue, upper_blue),
            'Vert': cv2.inRange(hsv, lower_green, upper_green),
            'Jaune': cv2.inRange(hsv, lower_yellow, upper_yellow),
            'Orange': cv2.inRange(hsv, lower_orange, upper_orange),
            'Blanc': cv2.inRange(hsv, lower_white, upper_white),
        }

        timestamp_ms = int((time.time() - start_time) * 1000)

        for color_name, mask in masks.items():
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Ignorer les petites zones parasites
                if area > 500: 
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])

                        # Écrire dans le fichier CSV
                        writer.writerow([timestamp_ms, color_name, cX, cY])

                        # Dessiner un cercle sur l’image pour visualiser la détection
                        cv2.circle(frame, (cX, cY), 5, (0, 0, 0), -1)
                        cv2.putText(frame, color_name, (cX - 20, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)

        cv2.imshow('Detection Couleurs Rubik\'s Cube', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
