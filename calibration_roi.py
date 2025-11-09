
# ============================================================================
#  calibration_roi.py
#  ------------------
#  Objectif :
#     Gérer la calibration des ROI (zones d'intérêt) sur les 6 faces du cube.
#     Ce module permet :
#        - de charger / sauvegarder les coordonnées de ROI
#        - de valider leur format
#        - d'effectuer une calibration interactive OpenCV (clic souris)
#
#  Fonctionnalités :
#     - validate_roi_dict(roi_data)
#     - load_calibration(filename='rubiks_calibration.json')
#     - save_calibration(roi_data, filename='rubiks_calibration.json')
#     - calibrate_roi_interactive(single_face_only=True)
#     - calibrate_single_face(image_path, face_name)
#     - calibrate_roi_yolo(model_path="in/best.pt", images_dir="tmp")
#
#  Utilisation :
#     from calibration_roi import calibrate_roi_interactive
#     calibrate_roi_interactive()  # même ROI pour les 6 faces (par défaut)
#
#     ou :
#     calibrate_roi_interactive(single_face_only=False)  # ROI différente par face
#
#  Auteur : refactor ChatGPT (style d'origine préservé)
#  Date   : 2025-10-09
# ============================================================================

from __future__ import annotations
import os, json, cv2
from typing import Dict, Tuple, Optional
from ultralytics import YOLO
import numpy as np
from colorama import Fore, Style, init
init(autoreset=True)

ROI = Tuple[int, int, int, int]
CANON_FACES = ["U", "D", "L", "R", "F", "B"]

# ----------------------------------------------------------------------------
#  Validation et I/O
# ----------------------------------------------------------------------------

def validate_roi_dict(roi_data: Dict[str, ROI]) -> bool:
    """Validation basique de la structure ROI."""
    if not isinstance(roi_data, dict):
        return False
    for f in CANON_FACES:
        if f not in roi_data:
            return False
        v = roi_data[f]
        if not isinstance(v, (list, tuple)) or len(v) != 4:
            return False
        x1, y1, x2, y2 = v
        try:
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        except Exception:
            return False
        if x2 <= x1 or y2 <= y1:
            return False
    return True


def load_calibration(filename: str | None = "rubiks_calibration.json") -> Optional[Dict[str, ROI]]:
    """Charge la calibration ROI depuis un fichier JSON."""
    if filename is None:
        filename = "rubiks_calibration.json"  # fallback par défaut

    try:
        if not os.path.exists(filename):
            print(f"Aucune calibration ROI trouvée ({filename}). Lancez d'abord le mode calibration.")
            return None

        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        norm = {k: tuple(map(int, v)) for k, v in data.items() if k in CANON_FACES}
        if not validate_roi_dict(norm):
            print("⚠️ Calibration ROI invalide (format ou valeurs incohérentes).")
            return None

        print(f"✅ Calibration ROI chargée depuis {filename}")
        return norm

    except Exception as e:
        print(f"❌ Erreur lecture calibration ROI: {e}")
        return None


def save_calibration(roi_data: Dict[str, ROI], filename: str = "rubiks_calibration.json") -> bool:
    """Sauvegarde la calibration ROI au format JSON (sécurisée)."""
    try:
        if not validate_roi_dict(roi_data):
            raise ValueError("roi_data invalide (structure ou valeurs)")

        payload = {k: [int(x) for x in v] for k, v in roi_data.items()}
        tmp = filename + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, filename)

        print(f"💾 Calibration ROI sauvegardée: {filename}")
        return True

    except Exception as e:
        print(f"❌ Erreur sauvegarde ROI: {e}")
        return False


# ----------------------------------------------------------------------------
#  Calibration interactive
# ----------------------------------------------------------------------------

_click_points = []
_temp_image = None
_current_face = ""

def _mouse_callback(event, x, y, flags, param):
    global _click_points, _temp_image, _current_face
    if event == cv2.EVENT_LBUTTONDOWN:
        _click_points.append((x, y))
        cv2.circle(_temp_image, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow(f'Calibration { _current_face }', _temp_image)
        if len(_click_points) == 2:
            x1, y1 = _click_points[0]
            x2, y2 = _click_points[1]
            cv2.rectangle(_temp_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.imshow(f'Calibration { _current_face }', _temp_image)
            print(f"Rectangle défini: ({x1},{y1}) → ({x2},{y2})")
            print("Appuyez sur 'ENTER' pour valider ou 'r' pour recommencer.")

def calibrate_single_face(image_path: str, face_name: str) -> Optional[ROI]:
    """Calibre une seule face à partir d'une image."""
    global _click_points, _temp_image, _current_face
    _click_points = []
    _current_face = face_name

    image = cv2.imread(image_path)
    if image is None:
        print(f"Erreur: impossible de charger {image_path}")
        return None

    _temp_image = image.copy()
    print(f"\n=== Calibration face {face_name} ===")
    print("1. Cliquez coin haut-gauche")
    print("2. Cliquez coin bas-droit")
    print("ENTER = valider, 'r' = recommencer, 'q' = ignorer")

    cv2.namedWindow(f'Calibration {face_name}', cv2.WINDOW_NORMAL)
    cv2.imshow(f'Calibration {face_name}', _temp_image)
    cv2.setMouseCallback(f'Calibration {face_name}', _mouse_callback)

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cv2.destroyAllWindows()
            return None
        elif key == ord('r'):
            _click_points = []
            _temp_image = image.copy()
            cv2.imshow(f'Calibration {face_name}', _temp_image)
        elif key == 13 and len(_click_points) == 2:  # ENTER
            x1, y1 = _click_points[0]
            x2, y2 = _click_points[1]
            cv2.destroyAllWindows()
            roi = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            print(f"ROI validée: {roi}")
            return roi

# ----------------------------------------------------------------------------
#  Calibration interactive
# ----------------------------------------------------------------------------

def calibrate_roi_interactive(single_face_only: bool = True) -> Dict[str, ROI]:
    """Calibre les 6 faces (avec option même ROI pour toutes)."""
    faces = ["U", "D", "L", "R", "F", "B"]
    files = [f"tmp/{f}.jpg" for f in faces]
    roi_data: Dict[str, ROI] = {}
    first_roi = None
    first_face = None

    print("\n=== MODE CALIBRATION ROI ===")
    print("Instructions:")
    print(" - Cliquez deux coins pour chaque face")
    print(" - ENTER = valider, 'r' = recommencer, 'q' = ignorer cette face\n")

    if single_face_only:
        print("⚙️  Mode: même ROI appliquée à toutes les faces.")

    for file_path, face in zip(files, faces):
        if not os.path.exists(file_path):
            print(f"Fichier {file_path} introuvable → ignoré.")
            continue

        if single_face_only and first_roi is not None:
            roi_data[face] = first_roi
            print(f"➡️  Face {face}: même ROI que {first_face}")
        else:
            roi = calibrate_single_face(file_path, face)
            if roi:
                roi_data[face] = roi
                print(f"✅ Face {face} calibrée: {roi}")
                if single_face_only and first_roi is None:
                    first_roi = roi
                    first_face = face

    if roi_data:
        save_calibration(roi_data)
        print(f"\n✅ Calibration sauvegardée ({len(roi_data)} faces calibrées).")
    else:
        print("\n❌ Aucune face calibrée.")

    return roi_data


# ----------------------------------------------------------------------------
#  Calibration automatique avec yolo
# ----------------------------------------------------------------------------

def calibrate_roi_yolo(model_path="in/best.pt", images_dir="tmp", show_preview=True):
    """
    Calibration automatique des ROI à l’aide de YOLO.
    Affiche les infos de détection et sauvegarde les ROI.
    """
    faces = ["U", "D", "L", "R", "F", "B"]
    roi_data = {}

    if not os.path.exists(model_path):
        print(f"❌ Modèle YOLO introuvable ({model_path})")
        return None

    print(f"\n🤖 Chargement du modèle YOLO ({model_path})...")
    model = YOLO(model_path)
    print("   ✓ Modèle chargé")

    for face in faces:
        img_path = os.path.join(images_dir, f"{face}.jpg")
        if not os.path.exists(img_path):
            print(f"⚠️ Image manquante: {img_path}")
            continue

        img = cv2.imread(img_path)
        if img is None:
            print(f"❌ Impossible de lire {img_path}")
            continue

        print(f"\n📸 Détection YOLO sur la face {face}...")
        results = model(img, verbose=False)
        boxes = results[0].boxes

        if len(boxes) == 0:
            print(f"❌ Aucune détection trouvée sur {face}")
            continue

        # On prend la boîte la plus confiante
        best_idx = int(np.argmax(boxes.conf.cpu().numpy()))
        x1, y1, x2, y2 = map(int, boxes.xyxy[best_idx].cpu().numpy())
        conf = float(boxes.conf[best_idx])
        cls_id = int(boxes.cls[best_idx]) if hasattr(boxes, 'cls') else -1

        roi_data[face] = (x1, y1, x2, y2)
        print(f"✅ {face}: ROI ({x1},{y1})→({x2},{y2}) | conf={conf:.3f} | class={cls_id}")

        if show_preview:
            vis = img.copy()
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 3)
            label = f"{face} ({conf:.2f})"
            cv2.putText(vis, label, (x1 + 10, y1 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.imshow(f"YOLO ROI {face}", vis)
            cv2.waitKey(500)
            cv2.destroyAllWindows()

    if roi_data:
        save_calibration(roi_data)
        print(f"\n💾 Calibration automatique sauvegardée ({len(roi_data)} faces).")
    else:
        print("\n❌ Aucune face calibrée (YOLO n’a rien trouvé).")

    return roi_data

# ----------------------------------------------------------------------------
#  Menu utilisateur (console)
# ----------------------------------------------------------------------------

def calibration_menu():
    """Menu simple pour lancer la calibration ROI."""
    print(Fore.YELLOW + Style.BRIGHT + "\n=== MODE CALIBRATION ROI ===" + Style.RESET_ALL)
    print(Fore.WHITE + "Vous allez calibrer les 6 faces: F, R, B, L, U, D (ordre optimal robot)")

    print(Fore.YELLOW + Style.BRIGHT + "\n=== MENU CALIBRATION ROI ===" + Style.RESET_ALL)
    print(Fore.GREEN + "1." + Fore.WHITE + " Même ROI pour les 6 faces (mode rapide)")
    print(Fore.GREEN + "2." + Fore.WHITE + " ROI différente par face (mode complet)")
    print(Fore.GREEN + "3." + Fore.WHITE + " ROI automatique avec YOLO")
    print(Fore.RED + "4." + Fore.WHITE + " Quitter\n")

    choice = input(Fore.YELLOW + "Choisissez une option (1/2/3) : " + Style.RESET_ALL).strip()

    if choice == "1":
        print(Fore.CYAN + "➡️ Calibration avec une même ROI pour les 6 faces" + Style.RESET_ALL)
        calibrate_roi_interactive(single_face_only=True)
    elif choice == "2":
        print(Fore.CYAN + "➡️ Calibration individuelle des 6 faces" + Style.RESET_ALL)
        calibrate_roi_interactive(single_face_only=False)
    elif choice == "3":
        print(Fore.CYAN + "➡️ Calibration automatique avec YOLO" + Style.RESET_ALL)
        calibrate_roi_yolo()        
    else:
        print(Fore.YELLOW + "Fin du mode calibration ROI." + Style.RESET_ALL)
