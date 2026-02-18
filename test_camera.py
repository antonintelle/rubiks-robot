#!/usr/bin/env python3
# ============================================================================
#  test_camera.py
#  -------------
#  Objectif :
#     Script de **test minimal Picamera2** pour vérifier rapidement que :
#       - la caméra démarre correctement,
#       - la capture d’une image fonctionne,
#       - l’autofocus (AF) peut être activé,
#       - l’image est bien enregistrée sur disque.
#
#  Entrée principale :
#     - Exécution directe (__main__) :
#         python3 test_camera.py
#         -> Capture une image et écrit "test.jpg" dans le répertoire courant.
#
#  Étapes principales :
#     1) Initialisation Picamera2 :
#        - Picamera2() + configuration “still” en 1280×720
#        - start() pour lancer le flux caméra
#
#     2) Activation autofocus :
#        - set_controls({"AfMode": controls.AfModeEnum.Continuous})
#        - sleep(1.0) pour laisser le temps à l’AF de converger
#
#     3) Capture + sauvegarde :
#        - capture_array() (RGB)
#        - conversion RGB -> BGR (OpenCV) puis cv2.imwrite("test.jpg")
#
#     4) Nettoyage :
#        - stop() + close() pour libérer proprement la caméra
#
#  Dépendances :
#     - picamera2 (Picamera2)
#     - libcamera.controls (AfModeEnum)
#     - opencv-python (cv2) pour conversion et écriture image
#     - time (temporisation autofocus)
#
#  Notes :
#     - Script volontairement simple : pas de lock AE/AWB, pas de rotation,
#       pas de gestion d’erreurs, juste un “smoke test” caméra.
# ============================================================================


from picamera2 import Picamera2
from libcamera import controls
import cv2, time

picam2 = Picamera2()
config = picam2.create_still_configuration(
    main={"size": (1280, 720)}
)
picam2.configure(config)
picam2.start()

picam2.set_controls({
    "AfMode": controls.AfModeEnum.Continuous
})

time.sleep(1.0)   # Laisse l’autofocus se caler
frame = picam2.capture_array()
frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
cv2.imwrite("test.jpg", frame_bgr)

picam2.stop()
picam2.close()
