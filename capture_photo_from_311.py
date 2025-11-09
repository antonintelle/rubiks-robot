#!/usr/bin/env python3
"""
capture_photo_from_311.py
-------------------------
Capture d'image compatible Windows & Raspberry Pi OS Bookworm.
→ Utilise Picamera2 sur Raspberry Pi
→ Utilise OpenCV sur Windows
→ Capture en continu jusqu’à ce que l’utilisateur tape 'q'
→ Pause manuelle entre chaque photo
→ Renvoie un JSON récapitulatif à la fin
"""

import sys, json, platform, datetime, time, os, cv2


def capture_image(filename="capture.jpg", rotation=180):
    """Capture une seule image et la sauvegarde avec rotation éventuelle."""
    system_name = platform.system().lower()
    print(f"✅ Lancement sur plateforme = {system_name}")
    print(f"✅ Fichier de sortie = {filename}")
    print(f"🔄 Rotation demandée = {rotation}°")

    # Raspberry Pi (Picamera2)
    if "linux" in system_name:
        try:
            from picamera2 import Picamera2
            picam2 = Picamera2()
            config = picam2.create_still_configuration(main={"size": (2304, 1296)})
            picam2.configure(config)
            picam2.start()
            time.sleep(1.5)
            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            if rotation == 90:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_180)
            elif rotation == 270:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)

            cv2.imwrite(filename, frame_bgr)
            picam2.stop()
            picam2.close()
            time.sleep(0.3)
            print(f"✅ Image enregistrée : {filename}")
            return filename

        except Exception as e:
            print(f"❌ Erreur Picamera2 : {e}")
            return None

    # Windows / autres (OpenCV)
    else:
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("❌ Impossible d’ouvrir la caméra (OpenCV)")
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret:
                print("❌ Échec de capture d’image")
                return None

            if rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            cv2.imwrite(filename, frame)
            print(f"✅ Image enregistrée : {filename}")
            return filename

        except Exception as e:
            print(f"❌ Erreur OpenCV : {e}")
            return None


# ---------------------------------------------------------------------
# Capture en boucle jusqu'à 'q'
# ---------------------------------------------------------------------
def capture_loop(rotation=180, folder="tmp"):
    """
    Capture en boucle : attend Entrée entre chaque image, 'q' pour quitter.

    Args:
        rotation (int): angle de rotation (0, 90, 180, 270)
        folder (str): dossier de sortie
    """
    os.makedirs(folder, exist_ok=True)
    filenames = []
    print("📸 Mode capture continue — appuie sur [Entrée] pour capturer, [q] pour quitter.\n")

    while True:
        key = input("➡️  Appuie sur [Entrée] pour capturer une image ou [q] pour quitter : ").strip().lower()
        if key == "q":
            print("🛑 Fin de la session de capture.")
            break

        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename = os.path.join(folder, f"capture_{timestamp}.jpg")

        path = capture_image(filename, rotation)
        if path:
            filenames.append(path)
        else:
            print("⚠️ Capture échouée.")

    print(f"\n✅ {len(filenames)} images capturées.")
    return filenames


# ---------------------------------------------------------------------
# Mode exécution directe → JSON de sortie
# ---------------------------------------------------------------------
if __name__ == "__main__":
    rotation = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    folder = sys.argv[2] if len(sys.argv) > 2 else "tmp"

    files = capture_loop(rotation, folder)

    result = {
        "success": len(files) > 0,
        "count": len(files),
        "files": files,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    print(json.dumps(result))
