# ============================================================================
#  calibration_colors.py
#  ---------------------
#  Objectif :
#     Regrouper TOUT ce qui concerne la **calibration et classification des couleurs**.
#
#  Fonctions principales :
#     - load_color_calibration(filename='rubiks_color_calibration.json')
#     - save_color_calibration(color_calibration, filename='rubiks_color_calibration.json')
#     - analyze_colors(cells) / analyze_colors_with_calibration(cells, calib)
#     - calibrate_colors_interactive()  ← utilise la ROI existante + clic utilisateur
#     - FaceSelector / display_and_select_cell : interface de sélection
#
#  Remarques :
#     - Pour éviter les imports circulaires, on importe localement
#       process_face_with_roi (depuis process_images_cube) au moment d'usage.
# ============================================================================

from __future__ import annotations
import os, json
from typing import Dict, Tuple, Optional, List
import numpy as np
import cv2

# ---------------------------
# Chargement / Sauvegarde RGB
# ---------------------------

def load_color_calibration(filename: str = "rubiks_color_calibration.json") -> Optional[Dict[str, Tuple[float,float,float,float]]]:
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        color_data = data.get("color_data", data)  # compat ancien format
        calib = {}
        for name, arr in color_data.items():
            r, g, b, tol = arr
            calib[name] = (float(r), float(g), float(b), float(tol))
        print(f"Calibration couleurs chargée: {list(calib.keys())}")
        return calib
    except Exception as e:
        print(f"Erreur lors du chargement des couleurs: {e}")
        return None


def save_color_calibration(color_calibration: Dict[str, Tuple[float,float,float,float]],
                           filename: str = "rubiks_color_calibration.json") -> bool:
    try:
        color_data = {k: [float(r), float(g), float(b), float(t)]
                      for k, (r,g,b,t) in color_calibration.items()}
        payload = {
            "metadata": {
                "created_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                "colors_count": len(color_data),
                "version": "1.0",
            },
            "color_data": color_data,
        }
        tmp = filename + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, filename)
        print(f"Calibration couleurs sauvegardée: {filename}")
        return True
    except Exception as e:
        print(f"Erreur sauvegarde calibration couleurs: {e}")
        return False

# ---------------------------
# Classification / Analyse
# ---------------------------

def _avg_center_rgb(cell_roi) -> Tuple[float,float,float]:
    h, w = cell_roi.shape[:2]
    ch, cw = int(h*0.1), int(w*0.1)
    center = cell_roi[ch:h-ch, cw:w-cw]
    if center.size == 0:
        return (0.0, 0.0, 0.0)
    mean_bgr = np.mean(center, axis=(0,1))
    b, g, r = mean_bgr
    return float(r), float(g), float(b)


def classify_color_default(r: float, g: float, b: float) -> str:
    # Utilise HSV pour une classification robuste
    rgb_norm = np.array([[[r, g, b]]], dtype=np.uint8)
    h, s, v = map(float, cv2.cvtColor(rgb_norm, cv2.COLOR_RGB2HSV)[0,0])
    if s < 50 and v > 200: return "white"
    if s < 50 and v < 50:  return "black"
    if h < 10 or h > 170:  return "red"
    if 10 <= h < 25:       return "orange"
    if 25 <= h < 35:       return "yellow"
    if 35 <= h < 85:       return "green"
    if 85 <= h < 125:      return "blue"
    if 125 <= h < 170:     return "blue"
    return f"hsv({int(h)},{int(s)},{int(v)})"


def classify_with_calibration(r: float, g: float, b: float,
                              color_calibration: Dict[str, Tuple[float,float,float,float]]) -> str:
    best = "unknown"
    min_d = float("inf")
    for name, (rr,gg,bb,tol) in color_calibration.items():
        d = ((r-rr)**2 + (g-gg)**2 + (b-bb)**2) ** 0.5
        if d < tol and d < min_d:
            min_d, best = d, name
    return best if best != "unknown" else f"rgb({r:.0f},{g:.0f},{b:.0f})"


def analyze_colors_with_calibration(cells, color_calibration: Optional[Dict[str, Tuple[float,float,float,float]]] = None) -> List[str]:
    out = []
    for (_ij), roi in [(ij, roi) for (ij, roi) in cells]:
        if roi is None or getattr(roi, "size", 0) == 0:
            out.append("unknown"); continue
        r,g,b = _avg_center_rgb(roi)
        if color_calibration:
            out.append(classify_with_calibration(r,g,b,color_calibration))
        else:
            out.append(classify_color_default(r,g,b))
    return out


def analyze_colors(cells) -> List[str]:
    calib = load_color_calibration()
    return analyze_colors_with_calibration(cells, calib)

# ---------------------------
# UI de calibration par clic
# ---------------------------

class FaceSelector:
    """Interface Matplotlib pour sélectionner une cellule contenant une couleur."""
    def __init__(self, roi_data: Dict[str, tuple], color_name: str):
        import matplotlib.pyplot as plt
        self.plt = plt
        self.roi_data = roi_data
        self.color_name = color_name
        self.selected_face = None
        self.selected_cell = None
        self.face_images = {}
        self.face_axes = {}

    def _load_images(self):
        for f in ["F","R","B","L","U","D"]:
            p = f"tmp/{f}.jpg"
            if os.path.exists(p):
                img = cv2.imread(p)
                if img is not None:
                    self.face_images[f] = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def _cell_from_xy(self, face: str, x: float, y: float):
        if face not in self.roi_data: return None
        x1,y1,x2,y2 = self.roi_data[face]
        if not (x1 <= x <= x2 and y1 <= y <= y2): return None
        cw = (x2-x1)/3.0; ch = (y2-y1)/3.0
        col = int((x-x1)/cw); row = int((y-y1)/ch)
        col = max(0, min(2, col)); row = max(0, min(2, row))
        return row*3 + col

    def _on_click(self, event):
        if event.inaxes is None: return
        for face, ax in self.face_axes.items():
            if event.inaxes == ax:
                cell = self._cell_from_xy(face, event.xdata, event.ydata)
                if cell is not None:
                    self.selected_face, self.selected_cell = face, cell
                    print(f"\nSélectionné: Face {face}, Cellule {cell+1}")
                    self.plt.close("all")
                break

    def show(self):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        self._load_images()
        order = ["F","R","B","L","U","D"]
        face_names = {"F":"Front","R":"Right","B":"Back","L":"Left","U":"Up","D":"Down"}

        # --- Crée la figure principale
        fig, axs = plt.subplots(2, 3, figsize=(8.2, 8.2))
        fig.canvas.manager.set_window_title("Calibration des couleurs")

        # --- Supprime les marges globales
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)

        for idx, face in enumerate(order):
            ax = axs[idx // 3, idx % 3]
            self.face_axes[face] = ax
            ax.axis("off")

            if face in self.face_images and face in self.roi_data:
                img = self.face_images[face]
                ax.imshow(img, aspect="equal")  # garde le bon ratio
                x1, y1, x2, y2 = self.roi_data[face]

                # Grille verte + lignes blanches
                ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1,
                                    linewidth=2, edgecolor="lime", facecolor="none"))
                cw, ch = (x2 - x1) / 3.0, (y2 - y1) / 3.0
                for i in range(1, 3):
                    ax.axvline(x=x1 + i * cw, color="white", linewidth=1, alpha=0.7)
                    ax.axhline(y=y1 + i * ch, color="white", linewidth=1, alpha=0.7)

                ax.set_title(f"{face} ({face_names[face]})",
                            fontsize=9, fontweight="bold", pad=1)
            else:
                ax.text(0.5, 0.5, f"Face {face}\nnon trouvée",
                        ha="center", va="center", transform=ax.transAxes,
                        fontsize=10, color="red")

        # --- Positionne chaque axe manuellement pour remplir au maximum
        for r in range(2):
            for c in range(3):
                axs[r, c].set_position([
                    0.005 + c * (1 / 3.01),   # x
                    0.5 - r * 0.49,           # y
                    1 / 3.05,                 # largeur
                    0.48                      # hauteur
                ])

        # --- Titre principal et aide regroupés en haut
        fig.text(0.5, 0.985,
                f"Sélectionnez une cellule contenant du {self.color_name.upper()}",
                ha="center", va="top", fontsize=13, fontweight="bold")

        fig.text(0.5, 0.955,
                "Cliquez dans la zone verte pour sélectionner une cellule",
                ha="center", va="top", fontsize=9, style="italic")

        # --- Taille fenêtre max 820x820, centrée si possible
        try:
            mng = plt.get_current_fig_manager()
            #mng.window.geometry("820x620+100+50")
            mng.full_screen_toggle()
        except Exception:
            pass

        # --- Garde la gestion du clic utilisateur
        fig.canvas.mpl_connect("button_press_event", self._on_click)

        plt.show()



def display_and_select_cell(roi_data: Dict[str, tuple], color_name: str):
    selector = FaceSelector(roi_data, color_name)
    selector.show()
    return selector.selected_face, selector.selected_cell

# ---------------------------
# Calibration interactive
# ---------------------------

def calibrate_colors_interactive(default_tolerance: float = None) -> Optional[Dict[str, Tuple[float,float,float,float]]]:
    """Demande de cliquer une cellule pour chaque couleur, calcule (R,G,B) moyens.
       Si default_tolerance est fourni, il est utilisé sans poser de question.
    """
    from calibration_roi import load_calibration  # import tardif pour éviter cycles
    roi_data = load_calibration()
    if roi_data is None:
        print("Aucune calibration ROI trouvée. Calibrez d'abord les positions.")
        return None

    calib: Dict[str, Tuple[float,float,float,float]] = {}
    for color_name in ["red","orange","yellow","green","blue","white"]:
        print(f"\n=== Calibration couleur: {color_name.upper()} ===")
        face, cell_idx = display_and_select_cell(roi_data, color_name)
        if face is None or cell_idx is None:
            print(f"Couleur {color_name} ignorée"); continue

        from process_images_cube import process_face_with_roi  # import tardif
        file_path = f"tmp/{face}.jpg"
        warped, cells = process_face_with_roi(file_path, roi_data[face], face, show=False, save_intermediates=False)
        if warped is None or not cells or cell_idx >= len(cells):
            print(f"Échec extraction cellules pour {face}"); continue
        (_ij, roi) = cells[cell_idx]
        r,g,b = _avg_center_rgb(roi)

        # 🔹 Nouvelle logique de tolérance
        if default_tolerance is not None:
            tol = float(default_tolerance)
            print(f"Tolérance forcée = {tol}")
        else:
            try:
                t = input(f"Tolérance pour {color_name} (défaut: 50) ? ").strip()
                tol = float(t) if t else 50.0
            except Exception:
                tol = 50.0

        calib[color_name] = (r,g,b,tol)
        print(f"Couleur {color_name} calibrée: RGB({r:.0f},{g:.0f},{b:.0f}) ±{tol}")

    if calib:
        save_color_calibration(calib)
        print("\nCalibration des couleurs sauvegardée.")
        print(f"Couleurs calibrées: {list(calib.keys())}")
    return calib if calib else None


# ============================================================================
# POINT D’ENTRÉE DIRECT
# ============================================================================

if __name__ == "__main__":
    import sys
    tol = None
    if "--tolerance" in sys.argv:
        idx = sys.argv.index("--tolerance")
        if idx + 1 < len(sys.argv):
            try:
                tol = float(sys.argv[idx + 1])
            except ValueError:
                print("⚠️ Tolérance invalide, utilisation de la valeur par défaut (50).")

    print("\n=== Calibration interactive des couleurs ===")
    calib = calibrate_colors_interactive(default_tolerance=tol)
    if calib:
        print("\n✅ Calibration terminée et sauvegardée.")
    else:
        print("\n⚠️ Calibration interrompue ou incomplète.")
    
    import time
    time.sleep(2)


