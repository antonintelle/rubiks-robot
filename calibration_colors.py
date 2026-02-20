<<<<<<< HEAD
#!/usr/bin/env python3
=======
>>>>>>> screen-gui
# ============================================================================
#  calibration_colors.py
#  ---------------------
#  Objectif :
<<<<<<< HEAD
#     Centraliser toute la logique de **mesure**, **calibration**, et
#     **classification** des couleurs des stickers du Rubik’s Cube.
#     Le fichier fournit :
#       - des méthodes robustes d’échantillonnage couleur (anti-reflets),
#       - une calibration utilisateur sauvegardée en JSON,
#       - plusieurs classificateurs (calibré / “cubotino-like” simple),
#       - des heuristiques de stabilisation (yellow/orange, reflets, centre).
#
#  Entrées principales :
#     - calibrate_colors_interactive(default_tolerance=None)
#         Calibration guidée par clic (Matplotlib) sur des images tmp/{F,R,B,L,U,D}.jpg,
#         en s’appuyant sur la calibration ROI (calibration_roi.load_calibration).
#         Sauvegarde rubiks_color_calibration.json via save_color_calibration().
#
#     - load_color_calibration(path="rubiks_color_calibration.json")
#     - save_color_calibration(color_calibration, filename="rubiks_color_calibration.json")
#         I/O JSON de la calibration : dict {color: (r,g,b,tol)} + metadata.
#
#     - analyze_colors_with_calibration(cells, color_calibration, margin=0.25, debug=False)
#         Analyse d’une face (liste de cellules) à partir d’une calibration fournie.
#
#     - analyze_colors(cells)
#         Wrapper qui charge automatiquement la calibration JSON, puis appelle
#         analyze_colors_with_calibration(...).
#
#     - analyze_colors_simple(cells, margin=0.25, debug=False)
#         Variante “Cubotino-like” (HSV + correctifs Lab) plus robuste aux reflets,
#         avec détection de faces à risque et heuristiques anti-confusions.
#
#  Mesure couleur (sampling) :
#     - sample_rgb_from_cell_bgr(cell_bgr, margin=0.25)
#         Mesure robuste sur une ROI cellule (OpenCV BGR) :
#           * coupe une marge interne (anti-bords/joints),
#           * blur léger,
#           * rejet des pixels specular via HSV (V haut + S bas),
#           * médiane sur pixels restants (robuste).
#     - sample_rgb_from_cell_bgr_legacy(...) : ancienne version sans rejet specular.
#
#  Classification (modes) :
#     1) Mode calibré :
#        - classify_with_calibration(r,g,b, color_calibration, debug_hsv=False)
#          * shortlist par tolérance RGB
#          * fallback “plus proche RGB”
#          * arbitrages HSV pour couples ambigus (yellow/orange, red/orange)
#        - classify_color_default(r,g,b) : fallback HSV simple (non calibré).
#
#     2) Mode simple “cubotino-like” :
#        - classify_color_cubotino_like(cell_bgr, ..., shiny=False, yo_centers=None)
#          * décisions via HSV + règles spécifiques
#          * décision Yellow/Orange renforcée via Lab (centres YO calculés depuis calib)
#        - detect_risky_face(...) / detect_shiny_face(...) : déclenchement mode “shiny”
#          si conditions de reflets + bandes de teinte à risque.
#
#  Heuristiques / correctifs :
#     - _decide_yellow_orange_lab(...) + cache YO (_get_yo_lab_centers_cached)
#         Décision YO en espace Lab (a,b) à partir des centres calibrés.
#     - fix_center_by_majority(colors)
#         Corrige le centre si "unknown" en forçant la couleur majoritaire des 8 autres.
#     - _is_fake_red_that_should_be_orange(cell_bgr)
#         Détecte un “faux rouge” dû à un effondrement orange (wrap hue) et corrige.
#     - Score reflets : _specular_score_cell(...) + détection face brillante.
#
#  UI calibration (clic) :
#     - FaceSelector : affiche les 6 faces et permet de cliquer une cellule
#       Support ROI au format :
#         * bbox (x1,y1,x2,y2) (legacy)
#         * quad (4 points) avec projection perspective (cv2.getPerspectiveTransform)
#     - display_and_select_cell(roi_data, color_name)
#
#  Dépendances / intégration pipeline :
#     - Utilise OpenCV (cv2) / NumPy.
#     - Évite les imports circulaires via imports tardifs :
#         * process_images_cube.process_face_with_roi (extraction cellules depuis ROI)
#         * calibration_roi.load_calibration (chargement ROI)
#     - Fichiers attendus :
#         * tmp/{F,R,B,L,U,D}.jpg : images des faces pour la calibration interactive
#         * rubiks_color_calibration.json : calibration persistante
#
#  Exécution directe :
#     - __main__ : lance calibrate_colors_interactive()
#       Option CLI : --tolerance <float> pour forcer la tolérance sur toutes les couleurs.
# ============================================================================


from __future__ import annotations
import os, json
from typing import Dict, Tuple, Optional, List
from collections import Counter
import numpy as np
import cv2
import math
from config_manager import get_config

# ============================================
# CHARGEMENT DE LA CONFIGURATION
# ============================================

def _get_vision_mode() -> str:
    cfg = get_config()
    profile = cfg.get("camera.lock_profile_active", "")
    profile = str(profile).lower()
    return "night" if ("soir" in profile or "night" in profile) else "day"


def _hue_deg_from_rgb(r: float, g: float, b: float) -> float:
    """Hue en degrés [0..360). OpenCV: H en [0..179]."""
    px = np.uint8([[[int(b), int(g), int(r)]]])  # BGR pour OpenCV
    hsv = cv2.cvtColor(px, cv2.COLOR_BGR2HSV)[0, 0]
    h = float(hsv[0]) * 2.0
    return h  # degrés

def _circular_dist_deg(a: float, b: float) -> float:
    """Distance angulaire sur un cercle 0..360."""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def sample_rgb_from_cell_bgr(cell_bgr: np.ndarray, margin: float = 0.25) -> tuple[float, float, float]:
    """
    Mesure robuste de couleur dans une cellule:
    - coupe une marge (par défaut 25%) pour éviter bords/joints/reflets
    - blur léger
    - rejette les pixels specular (reflets blancs) via HSV (V haut + S bas)
    - médiane (plus robuste que la moyenne)
    Retourne (r,g,b).
    """
    if cell_bgr is None or cell_bgr.size == 0:
        return (0.0, 0.0, 0.0)

    h, w = cell_bgr.shape[:2]
    mh, mw = int(h * margin), int(w * margin)

    roi = cell_bgr[mh:h-mh, mw:w-mw]
    if roi.size == 0:
        roi = cell_bgr

    roi = cv2.GaussianBlur(roi, (3, 3), 0)

    # --- NOUVEAU: rejet des reflets (specular) ---
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    S = hsv[..., 1]
    V = hsv[..., 2]

    # Pixels "reflet": très lumineux et peu saturés
    spec = (V > 240) & (S < 90)

    flat = roi.reshape(-1, 3)
    keep = (~spec).reshape(-1)

    if keep.sum() > 20:  # assez de pixels non-reflets
        bgr = np.median(flat[keep], axis=0)
    else:
        # fallback si presque tout est reflet
        bgr = np.median(flat, axis=0)
    # --- fin nouveau ---

    b, g, r = bgr
    return (float(r), float(g), float(b))

def sample_rgb_from_cell_bgr_legacy(cell_bgr: np.ndarray, margin: float = 0.25) -> tuple[float, float, float]:
    """
    Mesure robuste de couleur dans une cellule:
    - coupe une marge (par défaut 25%) pour éviter bords/joints/reflets
    - blur léger
    - médiane (plus robuste que la moyenne)
    Retourne (r,g,b).
    """
    if cell_bgr is None or cell_bgr.size == 0:
        return (0.0, 0.0, 0.0)

    h, w = cell_bgr.shape[:2]
    mh, mw = int(h * margin), int(w * margin)

    roi = cell_bgr[mh:h-mh, mw:w-mw]
    if roi.size == 0:
        roi = cell_bgr

    roi = cv2.GaussianBlur(roi, (3, 3), 0)

    bgr = np.median(roi.reshape(-1, 3), axis=0)
    b, g, r = bgr
    return (float(r), float(g), float(b))
# ---------------------------
# Helpers ROI (BBOX ou QUAD)
# ---------------------------

def _is_number(v) -> bool:
    """True si v est un scalaire numérique (inclut numpy scalars)."""
    return isinstance(v, (int, float, np.number))


def _as_list(obj):
    """Convertit ndarray -> list, laisse list/tuple inchangé."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def _is_point2(pt) -> bool:
    pt = _as_list(pt)
    return (
        isinstance(pt, (list, tuple)) and len(pt) == 2 and
        _is_number(pt[0]) and _is_number(pt[1])
    )


def is_bbox_roi(roi) -> bool:
    """ROI bbox : (x1, y1, x2, y2) scalaires."""
    roi = _as_list(roi)
    return (
        isinstance(roi, (list, tuple)) and len(roi) == 4 and
        all(_is_number(v) for v in roi)
    )


def is_quad_roi(roi) -> bool:
    """ROI quad : 4 points ((x,y), ...). Tolère ndarray (4,2)."""
    roi = _as_list(roi)
    return (
        isinstance(roi, (list, tuple)) and len(roi) == 4 and
        all(_is_point2(pt) for pt in roi)
    )


def quad_to_np(roi_quad) -> np.ndarray:
    """Convertit une ROI quad en np.array float32 shape (4,2)."""
    roi_quad = _as_list(roi_quad)
    return np.array([[float(px), float(py)] for (px, py) in roi_quad], dtype=np.float32)
=======
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
>>>>>>> screen-gui

# ---------------------------
# Chargement / Sauvegarde RGB
# ---------------------------

<<<<<<< HEAD
def load_color_calibration(path="rubiks_color_calibration.json"):
    """
    Charge la calibration couleurs (centres RGB + tol) depuis le JSON.
    Retourne dict: name -> (r,g,b,tol)
    """
    with open(path, "r") as f:
        data = json.load(f)

    color_data = data.get("color_data", data)  # sécurité si format différent

    calib = {}
    for name, arr in color_data.items():
        r, g, b, tol = arr
        calib[name] = (float(r), float(g), float(b), float(tol))

    print("Calibration couleurs chargée:", list(calib.keys()))
    return calib


=======
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
>>>>>>> screen-gui


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

<<<<<<< HEAD
def _avg_center_rgb_from_bgr_roi(roi_bgr: np.ndarray, frac: float = 0.35):
    """
    ROI OpenCV = BGR.
    Prend un patch central (pour éviter bords/reflets) et renvoie (r,g,b) moyens.
    """
    h, w = roi_bgr.shape[:2]
    ch, cw = int(h * frac), int(w * frac)
    y0 = (h - ch) // 2
    x0 = (w - cw) // 2
    patch = roi_bgr[y0:y0+ch, x0:x0+cw]

    b, g, r = patch.reshape(-1, 3).mean(axis=0)
    return float(r), float(g), float(b)

=======
>>>>>>> screen-gui

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


<<<<<<< HEAD
def classify_with_calibration(
    r: float, g: float, b: float,
    color_calibration,
    debug_hsv: bool = False
) -> str:
    """
    color_calibration: dict {name: (rr, gg, bb, tol)}

    Logique:
      1) shortlist par tol (distance RGB <= tol)
      2) best = plus proche en RGB parmi candidats
      3) arbitres HSV (Hue) pour couples ambigus:
         - yellow vs orange
         - red vs orange
         (même si l'autre n'est pas dans candidates)
    """

    # 1) shortlist par tol (RGB)
    candidates = []
    for name, (rr, gg, bb, tol) in color_calibration.items():
        d = ((r - rr) ** 2 + (g - gg) ** 2 + (b - bb) ** 2) ** 0.5
        if d <= float(tol):
            candidates.append((d, name))

    # 2) fallback si aucun candidat: plus proche RGB sans tol
    if not candidates:
        best = "unknown"
        min_d = float("inf")
        for name, (rr, gg, bb, _tol) in color_calibration.items():
            d = ((r - rr) ** 2 + (g - gg) ** 2 + (b - bb) ** 2) ** 0.5
            if d < min_d:
                min_d = d
                best = name
        return best

    # best RGB parmi candidats
    candidates.sort(key=lambda x: x[0])
    best = candidates[0][1]
    # --- Correction robuste Yellow/Orange via Hue ---
    if best in ("yellow", "orange"):
        h = _hue_deg_from_rgb(r, g, b)
        if debug_hsv:
            print(f"[HSV RULE] best={best} RGB=({r:.0f},{g:.0f},{b:.0f}) h={h:.1f}")

        # seuil simple (à ajuster si besoin)
        return "yellow" if h >= 50.0 else "orange"

    # 3) Arbitre HSV (Hue) — robuste et systématique
    # a) yellow vs orange
    if best in ("yellow", "orange") and "yellow" in color_calibration and "orange" in color_calibration:
        h = _hue_deg_from_rgb(r, g, b)

        ry, gy, by, _ = color_calibration["yellow"]
        ro, go, bo, _ = color_calibration["orange"]

        hy = _hue_deg_from_rgb(ry, gy, by)
        ho = _hue_deg_from_rgb(ro, go, bo)

        dy = _circular_dist_deg(h, hy)
        do = _circular_dist_deg(h, ho)

        if debug_hsv:
            print(f"[HSV YO] best={best} RGB=({r:.0f},{g:.0f},{b:.0f}) "
                  f"h={h:.1f} hy={hy:.1f} ho={ho:.1f} dy={dy:.1f} do={do:.1f}")

        best = "yellow" if dy <= do else "orange"
        return best

    # b) red vs orange
    if best in ("red", "orange") and "red" in color_calibration and "orange" in color_calibration:
        h = _hue_deg_from_rgb(r, g, b)

        rr, gr, br, _ = color_calibration["red"]
        ro, go, bo, _ = color_calibration["orange"]

        hr = _hue_deg_from_rgb(rr, gr, br)
        ho = _hue_deg_from_rgb(ro, go, bo)

        dr = _circular_dist_deg(h, hr)
        do = _circular_dist_deg(h, ho)

        if debug_hsv:
            print(f"[HSV RO] best={best} RGB=({r:.0f},{g:.0f},{b:.0f}) "
                  f"h={h:.1f} hr={hr:.1f} ho={ho:.1f} dr={dr:.1f} do={do:.1f}")

        best = "red" if dr <= do else "orange"
        return best

    return best



def is_white_lab(roi_bgr: np.ndarray, frac: float = 0.35,
                 L_min: float = 40.0, chroma_max: float = 28.0) -> bool:
    """
    Détecte blanc/gris via Lab (robuste aux ombres).
    - ROI OpenCV = BGR
    - a,b neutres ~128 => faible chroma
    """
    h, w = roi_bgr.shape[:2]
    ch, cw = int(h * frac), int(w * frac)
    y0 = (h - ch) // 2
    x0 = (w - cw) // 2
    patch = roi_bgr[y0:y0+ch, x0:x0+cw]

    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
    L, a, b = lab.reshape(-1, 3).mean(axis=0)

    chroma = math.sqrt((a - 128.0)**2 + (b - 128.0)**2)

    return (L >= L_min) and (chroma <= chroma_max)

def analyze_colors_with_calibration(
    cells,
    color_calibration: Dict[str, Tuple[float, float, float, float]],
    margin: float = 0.25,
    debug: bool = False
) -> List[str]:
    """
    cells: liste de ((i,j), cell_roi_bgr)
    color_calibration: dict[name] = (r,g,b,tol)
    """
    out = []

    for idx, ((i, j), cell_roi) in enumerate(cells):
        r, g, b = sample_rgb_from_cell_bgr(cell_roi, margin=margin)

        col = classify_with_calibration(r, g, b, color_calibration,debug_hsv=True)
        out.append(col)

        if debug:
            print(f"[CALIB] cell {idx+1} ({i},{j}) RGB=({r:.0f},{g:.0f},{b:.0f}) -> {col}")

=======
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
>>>>>>> screen-gui
    return out


def analyze_colors(cells) -> List[str]:
    calib = load_color_calibration()
<<<<<<< HEAD
    return analyze_colors_with_calibration(cells, calib, debug=True)

=======
    return analyze_colors_with_calibration(cells, calib)
>>>>>>> screen-gui

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
<<<<<<< HEAD
        """Retourne l'index cellule 0..8 à partir d'un clic (x,y).

        Supporte :
          - bbox (x1,y1,x2,y2)
          - quad ((xTL,yTL),(xTR,yTR),(xBR,yBR),(xBL,yBL))
        """
        if face not in self.roi_data:
            return None

        roi = self.roi_data[face]
        print(f"DEBUG click face={face} x={x:.1f} y={y:.1f} roi={roi} "f"type={type(roi)} is_bbox={is_bbox_roi(roi)} is_quad={is_quad_roi(roi)}")


        # ---------- BBOX (legacy) ----------
        if is_bbox_roi(roi):
            x1, y1, x2, y2 = [float(v) for v in _as_list(roi)]
            if not (x1 <= x <= x2 and y1 <= y <= y2):
                return None
            cw = (x2 - x1) / 3.0
            ch = (y2 - y1) / 3.0
            col = int((x - x1) / cw)
            row = int((y - y1) / ch)
            col = max(0, min(2, col))
            row = max(0, min(2, row))
            return row * 3 + col

        # ---------- QUAD (redressement) ----------
        if is_quad_roi(roi):
            quad = quad_to_np(roi)
            dst = np.array([[0, 0], [299, 0], [299, 299], [0, 299]], dtype=np.float32)

            # (x,y) -> (u,v) dans le carré 300x300
            M = cv2.getPerspectiveTransform(quad, dst)
            pt = np.array([[[float(x), float(y)]]], dtype=np.float32)
            uv = cv2.perspectiveTransform(pt, M)[0, 0]
            u, v = float(uv[0]), float(uv[1])
            if not (0 <= u < 300 and 0 <= v < 300):
                return None
            col = int(u / 100.0)
            row = int(v / 100.0)
            col = max(0, min(2, col))
            row = max(0, min(2, row))
            return row * 3 + col

        return None
=======
        if face not in self.roi_data: return None
        x1,y1,x2,y2 = self.roi_data[face]
        if not (x1 <= x <= x2 and y1 <= y <= y2): return None
        cw = (x2-x1)/3.0; ch = (y2-y1)/3.0
        col = int((x-x1)/cw); row = int((y-y1)/ch)
        col = max(0, min(2, col)); row = max(0, min(2, row))
        return row*3 + col
>>>>>>> screen-gui

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
<<<<<<< HEAD
        from matplotlib.patches import Rectangle, Polygon
=======
        from matplotlib.patches import Rectangle
>>>>>>> screen-gui

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
<<<<<<< HEAD

                roi = self.roi_data[face]
                print(f"DEBUG show face={face} roi={roi} type={type(roi)} "f"is_bbox={is_bbox_roi(roi)} is_quad={is_quad_roi(roi)}")

                # --- BBOX (legacy)
                if is_bbox_roi(roi):
                    x1, y1, x2, y2 = [float(v) for v in _as_list(roi)]
                    ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1,
                                           linewidth=2, edgecolor="lime", facecolor="none"))
                    cw, ch = (x2 - x1) / 3.0, (y2 - y1) / 3.0
                    for i in range(1, 3):
                        ax.axvline(x=x1 + i * cw, color="white", linewidth=1, alpha=0.7)
                        ax.axhline(y=y1 + i * ch, color="white", linewidth=1, alpha=0.7)

                # --- QUAD (redressement)
                elif is_quad_roi(roi):
                    quad = quad_to_np(roi)
                    ax.add_patch(Polygon(quad, closed=True, fill=False,
                                         linewidth=2, edgecolor="lime"))

                    # Dessine une grille 3x3 "dans" le quad en interpolant sur les bords
                    tl, tr, br, bl = quad
                    for t in (1/3, 2/3):
                        # lignes verticales
                        p_top = tl + t * (tr - tl)
                        p_bot = bl + t * (br - bl)
                        ax.plot([p_top[0], p_bot[0]], [p_top[1], p_bot[1]],
                                color="white", linewidth=1, alpha=0.7)
                        # lignes horizontales
                        p_left = tl + t * (bl - tl)
                        p_right = tr + t * (br - tr)
                        ax.plot([p_left[0], p_right[0]], [p_left[1], p_right[1]],
                                color="white", linewidth=1, alpha=0.7)
=======
                x1, y1, x2, y2 = self.roi_data[face]

                # Grille verte + lignes blanches
                ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1,
                                    linewidth=2, edgecolor="lime", facecolor="none"))
                cw, ch = (x2 - x1) / 3.0, (y2 - y1) / 3.0
                for i in range(1, 3):
                    ax.axvline(x=x1 + i * cw, color="white", linewidth=1, alpha=0.7)
                    ax.axhline(y=y1 + i * ch, color="white", linewidth=1, alpha=0.7)
>>>>>>> screen-gui

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
<<<<<<< HEAD
    import traceback
    print("DEBUG: calibration_colors.py =", __file__)

=======
>>>>>>> screen-gui
    roi_data = load_calibration()
    if roi_data is None:
        print("Aucune calibration ROI trouvée. Calibrez d'abord les positions.")
        return None

    calib: Dict[str, Tuple[float,float,float,float]] = {}
    for color_name in ["red","orange","yellow","green","blue","white"]:
        print(f"\n=== Calibration couleur: {color_name.upper()} ===")
<<<<<<< HEAD
        try:
            face, cell_idx = display_and_select_cell(roi_data, color_name)
        except Exception:
            print("DEBUG: exception dans display_and_select_cell()")
            traceback.print_exc()
            raise
=======
        face, cell_idx = display_and_select_cell(roi_data, color_name)
>>>>>>> screen-gui
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

<<<<<<< HEAD
# ============================================================================
# Cubotino-like
# ============================================================================

# --- Cubotino-like: simple HSV thresholds, no color calibration ----------------


# --- Cache calibration couleurs + centres Lab YO ---
_COLOR_CALIB_CACHE = None
_YO_LAB_CENTERS_CACHE = None

def _get_color_calib_cached(path="rubiks_color_calibration.json"):
    global _COLOR_CALIB_CACHE
    if _COLOR_CALIB_CACHE is None:
        try:
            _COLOR_CALIB_CACHE = load_color_calibration(path)
        except Exception:
            _COLOR_CALIB_CACHE = None
    return _COLOR_CALIB_CACHE

def _rgb_to_lab_ab(r: float, g: float, b: float):
    px = np.uint8([[[int(b), int(g), int(r)]]])  # BGR pour OpenCV
    lab = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)[0, 0]
    return float(lab[1]), float(lab[2])  # a, b

def _get_yo_lab_centers_cached():
    """
    Construit et met en cache les centres (a,b) de yellow/orange à partir
    de rubiks_color_calibration.json (tes centres RGB).
    """
    global _YO_LAB_CENTERS_CACHE
    if _YO_LAB_CENTERS_CACHE is not None:
        return _YO_LAB_CENTERS_CACHE

    calib = _get_color_calib_cached()
    if not calib or "yellow" not in calib or "orange" not in calib:
        _YO_LAB_CENTERS_CACHE = None
        return None

    ry, gy, by, _ = calib["yellow"]
    ro, go, bo, _ = calib["orange"]

    ay, by2 = _rgb_to_lab_ab(ry, gy, by)
    ao, bo2 = _rgb_to_lab_ab(ro, go, bo)

    _YO_LAB_CENTERS_CACHE = {"yellow": (ay, by2), "orange": (ao, bo2)}
    return _YO_LAB_CENTERS_CACHE

def _lab_Lab_from_rgb_sample(r: float, g: float, b: float):
    # OpenCV attend BGR en uint8
    px = np.uint8([[[int(b), int(g), int(r)]]])
    lab = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)[0, 0]
    L, a, bb = lab
    return float(L), float(a), float(bb)

def _decide_yellow_orange_lab(cell_bgr, margin=0.25, yo_centers=None, debug=False, bias_to_orange=1.05):
    if yo_centers is None:
        yo_centers = _get_yo_lab_centers_cached()
    if not yo_centers:
        return "orange"

    # ✅ RGB robuste (médiane + rejet specular)
    r, g, b = sample_rgb_from_cell_bgr(cell_bgr, margin=margin)
    L, a, bb = _lab_Lab_from_rgb_sample(r, g, b)

    ay, by2 = yo_centers["yellow"]
    ao, bo2 = yo_centers["orange"]

    dy = (a - ay) ** 2 + (bb - by2) ** 2
    do = (a - ao) ** 2 + (bb - bo2) ** 2

    if debug:
        print(f"[YO LAB] L={L:.1f} a={a:.1f} b={bb:.1f} | dy={dy:.1f} do={do:.1f}")

    # ✅ Biais anti-faux-yellow : si c'est trop proche, on choisit ORANGE
    return "yellow" if dy <= (do / bias_to_orange) else "orange"


def fix_center_by_majority(colors):
    # colors = liste de 9 couleurs
    others = [c for i,c in enumerate(colors) if i != 4]
    maj = Counter(others).most_common(1)[0][0]
    colors[4] = maj
    return colors
    

def _specular_score_cell(cell_bgr: np.ndarray, margin: float = 0.25) -> float:
    """
    Retourne un score [0..1] = proportion de pixels "specular" (reflets blancs)
    dans la zone interne de la cellule.
    """
    if cell_bgr is None or cell_bgr.size == 0:
        return 0.0

    h, w = cell_bgr.shape[:2]
    mh, mw = int(h * margin), int(w * margin)
    inner = cell_bgr[mh:h-mh, mw:w-mw]
    if inner.size == 0:
        inner = cell_bgr

    hsv = cv2.cvtColor(inner, cv2.COLOR_BGR2HSV)
    S = hsv[..., 1].astype(np.float32)
    V = hsv[..., 2].astype(np.float32)

    # pixels "reflet" = très lumineux et peu saturés
    mask = (V > 235) & (S < 120)
    return float(mask.mean())

def detect_shiny_face(cells, margin: float = 0.25, debug: bool = False) -> bool:
    """
    Détecte si la face est "brillante" (reflets) en moyenne sur les 9 cellules.
    """
    scores = []
    for (_, _), cell in cells:
        scores.append(_specular_score_cell(cell, margin=margin))
    avg = float(np.mean(scores)) if scores else 0.0

    # seuils à peu près stables : 0.01 = 1% de pixels specular en moyenne
    shiny = avg >= 0.005

    if debug:
        print(f"[SIMPLE] shiny_score(avg)={avg:.4f} => shiny_mode={shiny}")
    return shiny

def _lab_ab_from_cell(cell_bgr: np.ndarray, margin: float = 0.25):
    h, w = cell_bgr.shape[:2]
    mh, mw = int(h * margin), int(w * margin)
    inner = cell_bgr[mh:h-mh, mw:w-mw]
    if inner.size == 0:
        inner = cell_bgr
    lab = cv2.cvtColor(inner, cv2.COLOR_BGR2LAB).reshape(-1, 3)
    L, a, b = lab.mean(axis=0)
    return float(L), float(a), float(b)

def _lab_b_from_cell(cell_bgr: np.ndarray, margin: float = 0.25) -> float:
    h, w = cell_bgr.shape[:2]
    mh, mw = int(h * margin), int(w * margin)
    inner = cell_bgr[mh:h-mh, mw:w-mw]
    if inner.size == 0:
        inner = cell_bgr
    lab = cv2.cvtColor(inner, cv2.COLOR_BGR2LAB)
    # retourne b moyen (0..255), 128 = neutre, plus haut = plus jaune
    return float(lab.reshape(-1, 3)[:, 2].mean())

def _hsv_from_rgb(r: float, g: float, b: float):
    """Return (h_deg, s, v). h in degrees [0..360). s,v in [0..255]."""
    px = np.uint8([[[int(r), int(g), int(b)]]])  # RGB
    h, s, v = cv2.cvtColor(px, cv2.COLOR_RGB2HSV)[0, 0]
    return float(h) * 2.0, float(s), float(v)

# -----------------------------
# Helper: faux rouge (orange collapse)
# -----------------------------
def _is_fake_red_that_should_be_orange(cell_bgr: np.ndarray, margin: float = 0.25) -> bool:
    r, g, b = sample_rgb_from_cell_bgr(cell_bgr, margin=margin)
    h_deg, s, v = _hsv_from_rgb(r, g, b)

    # On ne traite QUE les "rouges wrap" (près de 0°) bien saturés, pas sombres
    if not ((h_deg >= 340 or h_deg < 12) and s > 140 and v > 90):
        return False

    # Orange qui s'effondre vers 0° => Lab(b-a) moins négatif que le vrai rouge
    _, a_lab, b_lab = _lab_ab_from_cell(cell_bgr, margin=margin)
    score = b_lab - a_lab  # plus haut => plus jaune/orange

    # Très conservateur : si c'est encore très négatif => vrai rouge
    return score >= -8.0


# -----------------------------
# 1) Detect risky face (shiny fallback)
# -----------------------------
def detect_risky_face(cells, margin: float = 0.25, debug: bool = False) -> bool:
    """
    Active le mode "shiny" seulement si:
    - assez de cellules dans bandes à risque (rouge wrap / zone orange-jaune),
    - ET présence d'un peu de specular (reflet blanc).
    """
    risky = 0
    shiny_scores = []

    for (_, _), cell in cells:
        r, g, b = sample_rgb_from_cell_bgr(cell, margin=margin)
        h_deg, s, v = _hsv_from_rgb(r, g, b)

        # bandes "à risque"
        is_red_wrap = (h_deg >= 350 or h_deg < 8) and (s > 160) and (v > 140)
        is_yorange_band = (40 <= h_deg < 55) and (s > 140) and (v > 170)
        if is_red_wrap or is_yorange_band:
            risky += 1

        # specular : pixels très clairs ET peu saturés (reflets)
        hh, ww = cell.shape[:2]
        mh, mw = int(hh * margin), int(ww * margin)
        inner = cell[mh:hh-mh, mw:ww-mw]
        if inner.size == 0:
            inner = cell

        hsv = cv2.cvtColor(inner, cv2.COLOR_BGR2HSV)
        S = hsv[..., 1].astype(np.float32)
        V = hsv[..., 2].astype(np.float32)

        shiny_mask = (V > 245) & (S < 80)   # plus strict = moins de faux "shiny"
        shiny_scores.append(float(shiny_mask.mean()))

    avg_shiny = float(np.mean(shiny_scores)) if shiny_scores else 0.0
    shiny = avg_shiny >= 0.003   # 0.3% en moyenne

    fallback = (risky >= 2) and shiny

    if debug:
        print(f"[SIMPLE] risky_cells={risky} avg_shiny={avg_shiny:.4f} => fallback={fallback}")

    return fallback


# -----------------------------
# 2) Classify (Cubotino-like, simple)
# -----------------------------
def classify_color_cubotino_like(cell_bgr, mode: str, margin=0.25, debug=False, shiny=False, yo_centers=None) -> str:
    if mode == "night":
        return classify_color_cubotino_like_night(cell_bgr, margin, debug, shiny, yo_centers)
    return classify_color_cubotino_like_day(cell_bgr, margin, debug, shiny, yo_centers)

# -----------------------------
# 3) Analyze face (centre-fix + face-fix ultra conservateur)
# -----------------------------

def _rgb_dist(a, b):
    return float(np.linalg.norm(np.array(a, dtype=np.float32) - np.array(b, dtype=np.float32)))

def _get_calib_rgb(color_name: str):
    calib = _get_color_calib_cached()
    if not calib or color_name not in calib:
        return None
    r, g, b, _ = calib[color_name]
    return (r, g, b)

def analyze_colors_simple(cells, margin: float = 0.25, debug: bool = False):
    shiny = detect_risky_face(cells, margin=margin, debug=debug)
    yo_centers = _get_yo_lab_centers_cached()

    mode = _get_vision_mode()
    if debug:
        print(f"[SIMPLE] mode={mode}")

    raw = []
    for ((i, j), cell) in cells:
        raw.append(classify_color_cubotino_like(
            cell,
            mode=mode,
            margin=margin,
            debug=debug,
            shiny=shiny,
            yo_centers=yo_centers
        ))

    raw2 = raw[:]  # copie

    # center fix uniquement si unknown
    if raw2[4] == "unknown":
        before = raw2[4]
        raw2 = fix_center_by_majority(raw2)
        if debug and raw2[4] != before:
            print(f"[SIMPLE] CENTER-FIX: {before} -> {raw2[4]}")

    # uniform fix ultra conservateur: 8 vs 1
    cnt = Counter(raw2)
    if len(cnt) == 2:
        (maj, nmaj), (minc, nmin) = cnt.most_common(2)
        if nmaj == 8 and nmin == 1 and maj != "unknown" and minc != "unknown":
            bad_idx = next(i for i, c in enumerate(raw2) if c == minc)

            bad_cell = cells[bad_idx][1]
            r, g, b = sample_rgb_from_cell_bgr(bad_cell, margin=margin)

            maj_rgb = _get_calib_rgb(maj)
            min_rgb = _get_calib_rgb(minc)

            if maj_rgb and min_rgb:
                dmaj = _rgb_dist((r, g, b), maj_rgb)
                dmin = _rgb_dist((r, g, b), min_rgb)

                if dmaj + 10 < dmin:  # marge conservative
                    if debug:
                        print(f"[AUTO UNIFORM-FIX] cell {bad_idx+1}: {minc}->{maj} (dmaj={dmaj:.1f} < dmin={dmin:.1f})")
                    raw2[bad_idx] = maj

    # recalc après fix
    cnt = Counter(raw2)

    # face-fix YO (ton truc existant)
    if (cnt["yellow"] + cnt["orange"]) >= 7 and 1 <= cnt["red"] <= 2:
        fixed = []
        for k, (((i, j), cell), col) in enumerate(zip(cells, raw2)):
            if col == "red" and _is_fake_red_that_should_be_orange(cell, margin=margin):
                fixed.append("orange")
                if debug:
                    print(f"[SIMPLE] FACE-FIX: red->orange on cell {k+1} (fake red)")
            else:
                fixed.append(col)
        return fixed

    return raw2

#############################################################################
# LEGACY
#############################################################################

def classify_color_cubotino_like_night(
    cell_bgr: np.ndarray,
    margin: float = 0.25,
    debug: bool = False,
    shiny: bool = False,
    yo_centers=None,
) -> str:
    r, g, b = sample_rgb_from_cell_bgr(cell_bgr, margin=margin)
    h_deg, s, v = _hsv_from_rgb(r, g, b)

    # 1) WHITE
    if s < 75 and v > 60:
        if debug:
            print(f"[SIMPLE] white via HSV | h={h_deg:.1f} s={s:.0f} v={v:.0f}")
        return "white"

    # Dark fallback
    if v < 40:
        if 80 <= h_deg < 170 and s > 80:
            return "green"
        return "unknown"

    # 2) RED wrap (version NUIT: récupère h~344-349 sans casser l'orange)
    # - Rouge "haut": h>=340
    # - Rouge "bas": h<8 (comme avant)
    # - Garde-fou orange: près de 0°, si le vert est trop présent -> orange
    if h_deg >= 340 or h_deg < 8:
        if h_deg < 8:
            # orange typique: g relativement présent vs r
            # (ratio plus robuste que seuil absolu)
            if (g / max(r, 1)) > 0.22 and b < 110:
                return "orange"

        if not shiny:
            return "red"

        _, a_lab, b_lab = _lab_ab_from_cell(cell_bgr, margin=margin)
        score = b_lab - a_lab
        if debug:
            print(f"[SIMPLE] red-zone shiny h={h_deg:.1f} Lab(a)={a_lab:.1f} Lab(b)={b_lab:.1f} (b-a)={score:.1f}")
        return "orange" if score >= -8.0 else "red"

    # 3) ORANGE / YELLOW
    if 8 <= h_deg < 80:
        if (yo_centers is not None) or shiny or (b < 25 and r > 220):
            return _decide_yellow_orange_lab(cell_bgr, margin=margin, yo_centers=yo_centers, debug=debug)

        if h_deg < 40:
            return "orange"
        if h_deg >= 55:
            return "yellow"

        rg = abs(r - g)
        if (b < 20 and g > 170):
            return "yellow"
        if (rg < 35) and (b < 95):
            return "yellow"
        return "orange"

    # 4) GREEN
    if 80 <= h_deg < 170:
        return "green"

    # 5) BLUE
    if 170 <= h_deg < 260:
        if s < 115:
            if debug:
                print(f"[SIMPLE] blue-zone but low S={s:.0f} => WHITE")
            return "white"
        return "blue"

    return "unknown"

def classify_color_cubotino_like_day(
    cell_bgr: np.ndarray,
    margin: float = 0.25,
    debug: bool = False,
    shiny: bool = False,
    yo_centers=None,   # <-- NOUVEAU
) -> str:
    r, g, b = sample_rgb_from_cell_bgr(cell_bgr, margin=margin)
    h_deg, s, v = _hsv_from_rgb(r, g, b)

    # 1) WHITE
    if s < 75 and v > 60:
        if debug:
            print(f"[SIMPLE] white via HSV | h={h_deg:.1f} s={s:.0f} v={v:.0f}")
        return "white"

    # Dark fallback: keep obvious greens (shadowed corner) instead of "unknown"
    if v < 40:
        if 80 <= h_deg < 170 and s > 80:   # vert évident même sombre
            return "green"
        return "unknown"

    # 2) RED wrap
    if h_deg >= 350 or h_deg < 8:
        if not shiny:
            return "red"

        _, a_lab, b_lab = _lab_ab_from_cell(cell_bgr, margin=margin)
        score = b_lab - a_lab
        if debug:
            print(f"[SIMPLE] red-zone shiny h={h_deg:.1f} Lab(a)={a_lab:.1f} Lab(b)={b_lab:.1f} (b-a)={score:.1f}")
        return "orange" if score >= -8.0 else "red"

    # 3) ORANGE / YELLOW
    if 8 <= h_deg < 80:
        # ✅ CHANGEMENT: décision YO via Lab (beaucoup plus stable que Hue)
        # On l'applique surtout quand ça brille OU quand c'est "jaune/orange saturé"
        if (yo_centers is not None) or shiny or (b < 25 and r > 220):
            return _decide_yellow_orange_lab(cell_bgr, margin=margin, yo_centers=yo_centers, debug=debug)

        # fallback si pas de centres Lab dispo (ton ancien code)
        if h_deg < 40:
            return "orange"
        if h_deg >= 55:
            return "yellow"

        rg = abs(r - g)
        if (b < 20 and g > 170):
            return "yellow"
        if (rg < 35) and (b < 95):
            return "yellow"
        return "orange"

    # 4) GREEN
    if 80 <= h_deg < 170:
        return "green"

    # 5) BLUE
    if 170 <= h_deg < 260:
        if s < 115:
            if debug:
                print(f"[SIMPLE] blue-zone but low S={s:.0f} => WHITE")
            return "white"
        return "blue"

    return "unknown"


def classify_color_cubotino_like_legacy1(
    cell_bgr: np.ndarray,
    margin: float = 0.25,
    debug: bool = False,
    shiny: bool = False
) -> str:
    r, g, b = sample_rgb_from_cell_bgr(cell_bgr, margin=margin)
    h_deg, s, v = _hsv_from_rgb(r, g, b)

    # 1) WHITE en priorité : low saturation + pas sombre
    # (ton cas "blanc un peu jaune" doit RESTER blanc)
    if s < 75 and v > 60:
        if debug:
            print(f"[SIMPLE] white via HSV | h={h_deg:.1f} s={s:.0f} v={v:.0f}")
        return "white"

    if v < 40:
        return "unknown"

    # 2) RED wrap (0°)
    if h_deg >= 350 or h_deg < 8:
        if not shiny:
            return "red"

        # mode shiny : garde-fou orange collapse via Lab(b-a)
        _, a_lab, b_lab = _lab_ab_from_cell(cell_bgr, margin=margin)
        score = b_lab - a_lab
        if debug:
            print(f"[SIMPLE] red-zone shiny h={h_deg:.1f} Lab(a)={a_lab:.1f} Lab(b)={b_lab:.1f} (b-a)={score:.1f}")

        # seuil CONSERVATEUR: on convertit moins de rouges en orange
        return "orange" if score >= -8.0 else "red"

    # 3) ORANGE / YELLOW
    if 8 <= h_deg < 80:
        # version simple et stable (même en shiny)
        if h_deg < 40:
            return "orange"
        if h_deg >= 55:
            return "yellow"

        # bande borderline 40..55 : petit test RGB (stable)
        rg = abs(r - g)

        # ✅ Garde-fou "jaune saturé" (typiquement: B très bas + G élevé)
        # évite de classer en orange des jaunes chauds type (255,218,0)
        if (b < 20 and g > 170):
            return "yellow" 
        # jaune : R~G et B bas ; orange : R>>G ou B plus haut
        if (rg < 35) and (b < 95):
            return "yellow"
        return "orange"

    # 4) GREEN
    if 80 <= h_deg < 170:
        return "green"

    # 5) BLUE (évite gris/blanc bleuté)
    if 170 <= h_deg < 260:
        if s < 115:
            if debug:
                print(f"[SIMPLE] blue-zone but low S={s:.0f} => WHITE")
            return "white"
        return "blue"

    return "unknown"

=======
>>>>>>> screen-gui

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


