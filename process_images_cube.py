#!/usr/bin/env python3
# ============================================================================
#  process_images_cube.py
#  ----------------------
#  Objectif :
#     Pipeline de **reconnaissance visuelle** d’un Rubik’s Cube à partir d’images
#     (faces photographiées). Le module :
#       - extrait la face du cube (via ROI calibrée ou détection auto),
#       - redresse/normalise la face en 300×300,
#       - découpe la face en 9 cellules (3×3),
#       - analyse les couleurs (mode “simple” robuste aux reflets),
#       - retourne un dictionnaire `FacesDict` (Face -> FaceResult).
#
#  Entrées principales :
#     - detect_colors_for_faces(image_folder, roi_data, color_calibration=None,
#                               debug="text", strict=False) -> FacesDict
#         Point d’entrée principal “production” :
#           * parcourt l’ordre canonique ["F","R","B","L","U","D"]
#           * charge chaque image <folder>/<FACE>.jpg
#           * extrait `warped` + `cells` via process_face_with_roi(...)
#           * classe les 9 couleurs via analyze_colors_simple(...)
#           * normalise les labels via _norm(...)
#           * en mode strict : lève si fichier/ROI/extraction/couleurs incomplètes.
#
#     - detect_colors_for_faces_legacy(...)
#         Variante historique (asserts) conservée pour comparaison / debug.
#
#  Extraction d’une face (ROI calibrée) :
#     - process_face_with_roi(image_path, roi_coords, face_name,
#                             show=False, save_intermediates=True) -> (warped, cells)
#         Gère 2 formats de ROI :
#           * bbox : (x1,y1,x2,y2) -> crop + resize 300×300
#           * quad : 4 points TL,TR,BR,BL -> perspective warp (warp_face)
#         Option debug : sauvegarde intermédiaires dans tmp/ :
#           {FACE}_1_original_with_roi.jpg / _2_roi_extracted.jpg / _3_warped_300x300.jpg / _4_grid_3x3.jpg
#
#  Pipeline “détection auto” (optionnel / debug) :
#     - process_one_face(image, ...) -> dict
#         Prétraitement + edges + Hough lines -> sélection lignes -> quad -> warp -> grid.
#     - process_one_face_debug(image, ...) -> dict
#         Variante très verbosée : tente d’abord contours (detect_cube_boundary / simple),
#         puis fallback lignes si besoin, avec visualisations Matplotlib.
#
#  Étapes principales / fonctions clés :
#     1) Prétraitement :
#        - prepare_image(...) : grayscale + blur (optionnel) + CLAHE
#        - create_cube_mask(...) : masque centré pour limiter la détection
#        - detect_edges(...) : Canny + application du masque
#
#     2) Détection géométrie (lignes / contours) :
#        - detect_lines(...) : HoughLinesP adaptatif (selon densité d’edges)
#        - classify_lines(...) : séparation horizontales / verticales (tolérance angle)
#        - filter_and_group_lines(...) : regroupe lignes proches, garde les plus longues
#        - select_main_lines(...) : déduit 4 bords externes (stratégie “lignes internes 3×3”)
#        - line_intersection(...) : intersection stable de 2 droites
#        - build_quad(...) : intersections -> quadrilatère -> validate_quad(...)
#        - detect_cube_boundary(...) / detect_cube_simple(...) : alternatives par contour
#        - order_quad_points(...) : remet les points en ordre TL,TR,BR,BL
#        - validate_quad(...) : vérifie points dans l’image + ratio carré + tailles min/max
#
#     3) Normalisation + découpe grille :
#        - warp_face(image, quad, size=300) : perspective transform vers 300×300
#        - extract_grid(warped, save_prefix=None) : découpe en 9 cellules + debug overlays
#
#     4) Analyse des couleurs :
#        - analyze_colors_simple(cells, debug=...) (depuis calibration_colors)
#        - _norm(label) : normalisation des labels vers {red, orange, yellow, green, blue, white}
#
#  Visualisation / debug couleurs :
#     - visualize_color_grid(colors, face_name, save_to_tmp=True)
#         Génère une grille 3×3 “couleurs Rubik’s” (image) + légende + sauvegarde tmp/.
#     - test_single_face_debug(face_name, roi_coords, color_calibration=None)
#         Test complet d’une seule face : extraction ROI + classification + grille colorée
#         + logs RGB/HSV/Lab par cellule (diagnostic yellow/orange/reflets).
#
#  Batch / utilitaires :
#     - f(files, ...) : traite une liste d’images et affiche des stats de réussite.
#
#  Dépendances / intégration :
#     - OpenCV (cv2), NumPy, Matplotlib
#     - calibration_rubiks.load_calibration (ROI)
#     - calibration_colors.analyze_colors_simple + sampling/debug HSV/Lab
#     - types_shared : FaceResult, FacesDict
#
#  Conventions fichiers :
#     - Images attendues : <image_folder>/{F,R,B,L,U,D}.jpg
#     - Dossier debug : tmp/ (intermédiaires + cellules + grilles colorées)
# ============================================================================

import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from calibration_rubiks import load_calibration
from types_shared import FaceResult, FacesDict
from matplotlib.patches import Rectangle, Polygon
from collections import Counter
import json
from calibration_colors import (
    analyze_colors,
    #analyze_colors_with_calibration,
    sample_rgb_from_cell_bgr,
    _hue_deg_from_rgb,
    analyze_colors_simple,
    _hsv_from_rgb
)

import calibration_colors
print("### calibration_colors imported from:", calibration_colors.__file__)

# --- couleurs canoniques & normalisation ---
CANON = {"red", "orange", "yellow", "green", "blue", "white"}

def _norm(c: str) -> str:
    c = (c or "").strip().lower()
    # tolère les abréviations
    if c.startswith("whi"): return "white"
    if c.startswith("ora"): return "orange"
    if c.startswith("yel"): return "yellow"
    if c.startswith("gre"): return "green"
    if c.startswith("blu"): return "blue"
    if c.startswith("red"): return "red"
    return c  # ex: "rgb(...)" / "hsv(...)" si non classé

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

# FACADE du fichier detect_colors_for_faces renvoie un cube dont les oculeurs ont été identifiées

def detect_colors_for_faces(image_folder, roi_data, color_calibration=None, debug="text", strict=False) -> FacesDict:
    order = ["F","R","B","L","U","D"]
    results: FacesDict = {}
    errors = {}

    for face in order:
        try:
            fp = os.path.join(image_folder, f"{face}.jpg")

            # 1) Prérequis
            if not os.path.exists(fp):
                msg = f"{face}: fichier manquant: {fp}"
                if strict: raise FileNotFoundError(msg)
                errors[face] = msg
                continue

            if face not in roi_data:
                msg = f"{face}: ROI manquante"
                if strict: raise KeyError(msg)
                errors[face] = msg
                continue

            # 2) Extraction
            warped, cells = process_face_with_roi(
                fp, roi_data[face], face,
                show=(debug == "both"),
                save_intermediates=(debug != "none")
            )
            if warped is None or not cells:
                msg = f"{face}: extraction KO"
                if strict: raise RuntimeError(msg)
                errors[face] = msg
                continue

            # 3) Analyse couleurs
            cols = analyze_colors_simple(cells, debug=(debug in ["text", "both"]))
            cols = [_norm(c) for c in cols]

            # 4) Remplacer les assert par des raise (assert peut être désactivé en prod)
            expected_ij = [(i, j) for i in range(3) for j in range(3)]
            got_ij = [ij for (ij, _roi) in cells]
            if got_ij != expected_ij:
                raise ValueError(f"{face}: ordre (i,j) inattendu: {got_ij}")

            if len(cells) != 9:
                raise ValueError(f"{face}: cells doit contenir 9 tuiles (got {len(cells)})")
            if len(cols) != 9:
                raise ValueError(f"{face}: colors doit contenir 9 labels (got {len(cols)})")

            results[face] = FaceResult(colors=cols, cells=cells, warped=warped, roi=roi_data[face])

            if debug in ["text","both"]:
                print(f"{face}: OK -> {cols} (centre {cols[4]})")

        except Exception as e:
            # Ici tu catches uniquement pour contextualiser
            errors[face] = repr(e)
            if strict:
                raise RuntimeError(f"VISION_FAILED face={face}: {e}") from e
            # sinon on continue (mode debug)

    # 5) En strict: si pas 6 faces -> échec global
    if strict and len(results) != 6:
        raise RuntimeError(f"VISION_INCOMPLETE {len(results)}/6 faces. errors={errors}")

    return results

def detect_colors_for_faces_legacy(image_folder, roi_data, color_calibration=None, debug="text") -> FacesDict:
    order = ["F","R","B","L","U","D"]
    results: FacesDict = {}
    for face in order:
        fp = os.path.join(image_folder, f"{face}.jpg")
        if not os.path.exists(fp) or face not in roi_data:
            if debug in ["text","both"]:
                print(f"{face}: fichier/ROI manquant(e)")
            continue

        warped, cells = process_face_with_roi(fp, roi_data[face], face,
                                              show=(debug=="both"),
                                              save_intermediates=(debug!="none"))
        if warped is None or not cells:
            if debug in ["text","both"]:
                print(f"{face}: extraction KO")
            continue

        # Utilise calibration si dispo
        cols = analyze_colors_simple(cells, debug=(debug in ["text", "both"]))
        #cols = (analyze_colors_with_calibration(cells, color_calibration)
        #        if color_calibration is not None
        #        else analyze_colors(cells))

        # --- AJOUT 1 : vérifier l'ordre row-major des (i,j) ---
        expected_ij = [(i, j) for i in range(3) for j in range(3)]
        got_ij      = [ij for (ij, _roi) in cells]
        assert got_ij == expected_ij, f"ordre (i,j) inattendu: {got_ij}"

        # --- AJOUT 2 : normaliser les labels couleur ---
        cols = [_norm(c) for c in cols]

        # --- AJOUT 3 : asserts existants (restent à leur place) ---
        assert len(cells) == 9, "cells doit contenir 9 tuiles"
        assert len(cols) == 9, "colors doit contenir 9 labels"
        
        # cells et colors doivent être dans le même ordre row-major

        results[face] = FaceResult(
            colors=cols,
            cells=cells,
            warped=warped,
            roi=roi_data[face],
        )

        if debug in ["text","both"]:
            print(f"{face}: OK -> {cols}")
            print(f"{face}: centre visuel = {cols[4]}")

    if debug in ["text","both"]:
        print(f"\nRÉSUMÉ PHASE VISION: {len(results)}/6 faces")
        all_cols = [c for fr in results.values() for c in fr.colors]
        cnt = Counter(all_cols)
        print("Comptage couleurs (vision brute):", dict(cnt))

    return results

# -----------------------
# 1) Préparation image
# -----------------------
def prepare_image(image, auto=True, settings=None):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if auto:
        settings = {"blur": 3, "canny1": 50, "canny2": 150}

    if settings.get("blur", 0) >= 3:
        k = settings["blur"] if settings["blur"] % 2 == 1 else settings["blur"] + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)

    # CLAHE au lieu d'equalizeHist pour un contraste plus localisé
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    return gray, settings

# -----------------------
# 2) Masque pour zone cube
# -----------------------
def create_cube_mask(img_shape, roi_factor=0.6):
    """Crée un masque centré pour limiter la détection à la zone du cube"""
    h, w = img_shape[:2]
    center_x, center_y = w//2, h//2
    
    # Taille de la ROI basée sur la plus petite dimension - ÉLARGIE
    roi_size = int(min(w, h) * roi_factor)
    
    mask = np.zeros((h, w), dtype=np.uint8)
    x1 = max(0, center_x - roi_size//2)
    x2 = min(w, center_x + roi_size//2)
    y1 = max(0, center_y - roi_size//2)
    y2 = min(h, center_y + roi_size//2)
    
    mask[y1:y2, x1:x2] = 255
    return mask

# -----------------------
# 3) Edges avec masque
# -----------------------
def detect_edges(gray, settings, use_mask=True):
    edges = cv2.Canny(gray, settings["canny1"], settings["canny2"])
    
    if use_mask:
        mask = create_cube_mask(gray.shape)
        edges = cv2.bitwise_and(edges, mask)
    
    return edges

# -----------------------
# 4) Détection des lignes (Hough) - restaurée
# -----------------------
def detect_lines(edges, adaptive=True):
    if adaptive:
        # Paramètres adaptatifs selon la densité de contours
        non_zero_pixels = cv2.countNonZero(edges)
        img_area = edges.shape[0] * edges.shape[1]
        density = non_zero_pixels / img_area
        
        if density > 0.1:  # Beaucoup de contours
            threshold = 50
            min_length = 30
            max_gap = 10
        elif density > 0.05:  # Densité moyenne
            threshold = 40
            min_length = 25
            max_gap = 15
        else:  # Peu de contours
            threshold = 30
            min_length = 20
            max_gap = 20
    else:
        # Paramètres par défaut - plus sensibles
        threshold, min_length, max_gap = 40, 25, 15
    
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 
                           threshold=threshold,
                           minLineLength=min_length, 
                           maxLineGap=max_gap)
    return lines

# -----------------------
# 5) Détection combinée : contours + lignes AVEC DEBUG
# -----------------------
def detect_cube_boundary(edges):
    """Détecte d'abord le contour externe du cube"""
    print("DEBUG: Tentative de détection par contour...")
    
    # Fermer les gaps pour former des contours complets
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
    dilated = cv2.dilate(closed, kernel, iterations=1)
    
    # Trouver les contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"DEBUG: {len(contours)} contours trouvés")
    
    if not contours:
        print("DEBUG: Aucun contour trouvé")
        return None
        
    # Trier les contours par aire décroissante
    contours_sorted = sorted(contours, key=cv2.contourArea, reverse=True)
    
    for i, contour in enumerate(contours_sorted[:3]):  # Tester les 3 plus grands
        area = cv2.contourArea(contour)
        print(f"DEBUG: Contour {i}: aire = {area}")
        
        # Vérifier que c'est suffisamment grand
        if area < 500:  # Seuil abaissé
            print(f"DEBUG: Contour {i} trop petit (aire: {area})")
            continue
        
        # Approximer par un polygone
        epsilon = 0.01 * cv2.arcLength(contour, True)  # Plus strict
        approx = cv2.approxPolyDP(contour, epsilon, True)
        print(f"DEBUG: Contour {i} approximé en {len(approx)} points")
        
        # Accepter entre 4 et 8 points et prendre les 4 coins principaux
        if 4 <= len(approx) <= 8:
            if len(approx) == 4:
                points = approx.reshape(4, 2).astype(np.float32)
            else:
                # Si plus de 4 points, prendre le rectangle englobant
                rect = cv2.minAreaRect(contour)
                points = cv2.boxPoints(rect).astype(np.float32)
            
            # Vérifier que c'est raisonnablement carré
            rect = cv2.boundingRect(contour)
            w, h = rect[2], rect[3]
            aspect_ratio = abs(w - h) / max(w, h)
            print(f"DEBUG: Rectangle englobant: {w}x{h}, aspect ratio: {aspect_ratio:.3f}")
            
            if aspect_ratio < 0.8:  # Tolérance très large
                print(f"DEBUG: Contour {i} accepté comme quadrilatère")
                return points
            else:
                print(f"DEBUG: Contour {i} rejeté - pas assez carré")
    
    print("DEBUG: Aucun contour carré trouvé")
    return None

# Version simplifiée pour débugger
def detect_cube_simple(edges):
    """Version ultra-simple : juste le plus grand rectangle"""
    print("DEBUG: Méthode simple - plus grand rectangle...")
    
    # Trouver tous les contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
    
    # Prendre le plus grand
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    
    if area < 100:
        print(f"DEBUG: Plus grand contour trop petit: {area}")
        return None
    
    # Rectangle englobant orienté
    rect = cv2.minAreaRect(largest)
    points = cv2.boxPoints(rect).astype(np.float32)
    
    print(f"DEBUG: Rectangle simple trouvé, aire: {area}")
    return points

# -----------------------
# Pipeline modifié - FORCER la détection de contour pour debug
# -----------------------
def process_one_face_debug(image, auto=True, settings=None, show=False, name="", save_prefix=None):
    gray, settings = prepare_image(image, auto, settings)
    edges = detect_edges(gray, settings, use_mask=True)
    
    print(f"DEBUG: Traitement de {name}")
    print(f"DEBUG: Edges shape: {edges.shape}, non-zero pixels: {cv2.countNonZero(edges)}")
    
    quad = None
    detection_method = "failed"
    
    # FORCER la méthode contour pour debug
    try:
        quad = detect_cube_boundary(edges)
        if quad is not None:
            detection_method = "contour"
            print(f"DEBUG: Contour réussi pour {name}")
        else:
            print(f"DEBUG: Contour échoué pour {name}, essai méthode simple")
            quad = detect_cube_simple(edges)
            if quad is not None:
                detection_method = "simple"
                print(f"DEBUG: Méthode simple réussie pour {name}")
            else:
                print(f"DEBUG: Toutes les méthodes de contour ont échoué pour {name}")
    except Exception as e:
        print(f"DEBUG: Erreur dans détection contour: {e}")
    
    # Si toujours rien, utiliser les lignes
    if quad is None:
        print(f"DEBUG: Fallback vers méthode lignes pour {name}")
        lines = detect_lines(edges, adaptive=True)
        h_lines, v_lines = classify_lines(lines, angle_tol=15)
        main_lines = select_main_lines(h_lines, v_lines, image.shape)
        quad = build_quad(main_lines, image.shape)
        detection_method = "lines"
    
    warped, grid_dbg, cells = None, None, []
    lines_dbg = image.copy()
    
    # Dessiner le quad détecté
    if quad is not None:
        # Réorganiser les points dans l'ordre TL, TR, BR, BL
        try:
            quad = order_quad_points(quad)
            cv2.polylines(lines_dbg, [quad.astype(int)], True, (0,0,255), 3)
            
            # Valider et traiter
            if validate_quad(quad, image.shape):
                warped = warp_face(image, quad, 300)
                grid_dbg, cells = extract_grid(warped, save_prefix)
            else:
                quad = None
                detection_method = "failed"
        except Exception as e:
            print(f"DEBUG: Erreur dans traitement quad: {e}")
            quad = None
            detection_method = "failed"

    if show:
        plt.figure(figsize=(16,8))
        plt.subplot(2,3,1); plt.imshow(gray, cmap="gray"); plt.title(f"{name}-gray"); plt.axis("off")
        plt.subplot(2,3,2); plt.imshow(edges, cmap="gray"); plt.title(f"{name}-edges+mask"); plt.axis("off")
        plt.subplot(2,3,3); plt.imshow(cv2.cvtColor(lines_dbg, cv2.COLOR_BGR2RGB)); plt.title(f"{name}-{detection_method}"); plt.axis("off")
        if warped is not None:
            plt.subplot(2,3,4); plt.imshow(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)); plt.title(f"{name}-warped"); plt.axis("off")
            plt.subplot(2,3,5); plt.imshow(cv2.cvtColor(grid_dbg, cv2.COLOR_BGR2RGB)); plt.title(f"{name}-grid"); plt.axis("off")
        plt.tight_layout(); plt.show()

    return {
        "quad": quad,
        "warped": warped,
        "cells": cells,
        "settings": settings,
        "detection_method": detection_method
    }

def order_quad_points(points):
    """Ordonne les points dans l'ordre TL, TR, BR, BL"""
    # Calculer le centre
    center = np.mean(points, axis=0)
    
    # Trier par angle par rapport au centre
    def angle_from_center(point):
        return np.arctan2(point[1] - center[1], point[0] - center[0])
    
    sorted_points = sorted(points, key=angle_from_center)
    
    # Identifier TL (top-left) comme le point avec la plus petite somme x+y
    sums = [p[0] + p[1] for p in sorted_points]
    tl_idx = np.argmin(sums)
    
    # Réorganiser pour commencer par TL et aller dans le sens horaire
    ordered = sorted_points[tl_idx:] + sorted_points[:tl_idx]
    
    return np.array(ordered, dtype=np.float32)

# -----------------------
# 5) Classification lignes H/V améliorée
# -----------------------
def classify_lines(lines, angle_tol=15):
    horizontales, verticales = [], []
    if lines is None:
        return horizontales, verticales

    for l in lines:
        x1, y1, x2, y2 = l[0]
        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        angle = np.degrees(np.arctan2(y2-y1, x2-x1))
        
        # Normaliser l'angle entre -90 et 90
        if angle > 90:
            angle -= 180
        elif angle < -90:
            angle += 180
            
        if abs(angle) < angle_tol:  # horizontale
            horizontales.append((x1, y1, x2, y2, length))
        elif abs(abs(angle) - 90) < angle_tol:  # verticale
            verticales.append((x1, y1, x2, y2, length))
    
    return horizontales, verticales

# -----------------------
# 6) Filtrage et regroupement des lignes
# -----------------------
def filter_and_group_lines(lines, axis='horizontal', tolerance=20):
    """Regroupe les lignes parallèles proches et garde les plus longues"""
    if not lines:
        return []
    
    # Trier par longueur décroissante
    lines_sorted = sorted(lines, key=lambda x: x[4], reverse=True)
    
    grouped = []
    used = set()
    
    for i, line1 in enumerate(lines_sorted):
        if i in used:
            continue
            
        group = [line1]
        x1, y1, x2, y2, _length1 = line1
        
        # Position de référence (y pour horizontales, x pour verticales)
        if axis == 'horizontal':
            ref_pos = (y1 + y2) / 2
        else:
            ref_pos = (x1 + x2) / 2
            
        for j, line2 in enumerate(lines_sorted[i+1:], i+1):
            if j in used:
                continue
                
            x1_2, y1_2, x2_2, y2_2, _length2 = line2
            if axis == 'horizontal':
                pos2 = (y1_2 + y2_2) / 2
            else:
                pos2 = (x1_2 + x2_2) / 2
                
            if abs(ref_pos - pos2) < tolerance:
                group.append(line2)
                used.add(j)
        
        # Garder la ligne la plus longue du groupe
        best_line = max(group, key=lambda x: x[4])
        grouped.append(best_line[:4])  # Enlever la longueur
        used.add(i)
    
    return grouped

# -----------------------
# 7) Construire le carré à partir des lignes internes
# -----------------------
def select_main_lines(h_lines, v_lines, img_shape):
    h, w = img_shape[:2]
    
    # Filtrer et regrouper les lignes
    h_filtered = filter_and_group_lines(h_lines, 'horizontal')
    v_filtered = filter_and_group_lines(v_lines, 'vertical')
    
    print(f"DEBUG: {len(h_lines)} lignes H -> {len(h_filtered)} filtrées")
    print(f"DEBUG: {len(v_lines)} lignes V -> {len(v_filtered)} filtrées")
    
    if len(h_filtered) < 2 or len(v_filtered) < 2:
        print(f"DEBUG: Pas assez de lignes (H:{len(h_filtered)}, V:{len(v_filtered)})")
        return None
    
    # NOUVELLE STRATÉGIE: Utiliser les lignes internes pour déduire le carré externe
    # Trier toutes les lignes par position
    h_sorted = sorted(h_filtered, key=lambda l: (l[1] + l[3]) / 2)
    v_sorted = sorted(v_filtered, key=lambda l: (l[0] + l[2]) / 2)
    
    # Si on a exactement 2 lignes H et 2 lignes V (lignes internes de la grille 3x3)
    if len(h_filtered) >= 2 and len(v_filtered) >= 2:
        # Prendre les lignes médianes comme références
        if len(h_filtered) >= 3:
            # On a les 2 lignes internes + peut-être les bords, prendre les internes
            h_top_internal = h_sorted[0] if len(h_sorted) > 2 else h_sorted[0]  
            h_bottom_internal = h_sorted[1] if len(h_sorted) > 2 else h_sorted[1]
        else:
            # On n'a que 2 lignes horizontales
            h_top_internal = h_sorted[0]
            h_bottom_internal = h_sorted[1]
            
        if len(v_filtered) >= 3:
            v_left_internal = v_sorted[0] if len(v_sorted) > 2 else v_sorted[0]
            v_right_internal = v_sorted[1] if len(v_sorted) > 2 else v_sorted[1]
        else:
            v_left_internal = v_sorted[0]  
            v_right_internal = v_sorted[1]
        
        # Calculer les positions des lignes internes
        h_top_y = (h_top_internal[1] + h_top_internal[3]) / 2
        h_bottom_y = (h_bottom_internal[1] + h_bottom_internal[3]) / 2
        v_left_x = (v_left_internal[0] + v_left_internal[2]) / 2
        v_right_x = (v_right_internal[0] + v_right_internal[2]) / 2
        
        print(f"DEBUG: Lignes internes - H: {h_top_y:.1f}, {h_bottom_y:.1f} - V: {v_left_x:.1f}, {v_right_x:.1f}")
        
        # DÉDUIRE les bords externes du carré :
        # Si les lignes internes divisent un carré 3x3, alors :
        # - La distance entre les 2 lignes internes = 1/3 de la taille du carré
        # - Les bords externes sont à 1/6 de taille de chaque côté
        
        h_spacing = abs(h_bottom_y - h_top_y)  # Espacement entre lignes horizontales internes
        v_spacing = abs(v_right_x - v_left_x)   # Espacement entre lignes verticales internes
        
        # FORCER UN CARRÉ : Prendre la moyenne des deux espacements
        avg_spacing = (h_spacing + v_spacing) / 2
        print(f"DEBUG: Espacements - H: {h_spacing:.1f}, V: {v_spacing:.1f}, Moyenne: {avg_spacing:.1f}")
        
        # CORRECTION : Utiliser un facteur plus réaliste
        # Au lieu de supposer que l'espacement = 1/3 du cube total,
        # supposer que l'espacement = 1/2 du cube total (plus conservateur)
        cell_size = avg_spacing * 0.6  # Facteur correctif
        
        print(f"DEBUG: Taille de cellule corrigée: {cell_size:.1f} x {cell_size:.1f}")
        
        # Calculer les centres des lignes internes
        h_center = (h_top_y + h_bottom_y) / 2
        v_center = (v_left_x + v_right_x) / 2
        
        # Calculer les positions des bords externes pour un carré plus réaliste
        # Total size = 2.5 * cell_size (au lieu de 3 * cell_size)
        total_size = 2.5 * cell_size
        half_size = total_size / 2
        
        # SÉCURITÉ : S'assurer que le carré reste dans les limites de l'image
        h, w = img_shape[:2]
        max_size = min(w, h) * 0.8  # Maximum 80% de l'image
        if total_size > max_size:
            total_size = max_size
            half_size = total_size / 2
            print(f"DEBUG: Taille limitée à {total_size:.1f} pour rester dans l'image")
        
        external_top_y = max(10, h_center - half_size)
        external_bottom_y = min(h - 10, h_center + half_size)  
        external_left_x = max(10, v_center - half_size)
        external_right_x = min(w - 10, v_center + half_size)
        
        print(f"DEBUG: Carré parfait calculé - Centre: ({v_center:.1f}, {h_center:.1f}), Taille: {total_size:.1f}")
        print(f"DEBUG: Bords externes sécurisés - H: {external_top_y:.1f}, {external_bottom_y:.1f} - V: {external_left_x:.1f}, {external_right_x:.1f}")
        
        # Créer les lignes externes
        top_line = (int(external_left_x), int(external_top_y), int(external_right_x), int(external_top_y))
        bottom_line = (int(external_left_x), int(external_bottom_y), int(external_right_x), int(external_bottom_y))
        left_line = (int(external_left_x), int(external_top_y), int(external_left_x), int(external_bottom_y))
        right_line = (int(external_right_x), int(external_top_y), int(external_right_x), int(external_bottom_y))
        
        return [top_line, bottom_line, left_line, right_line]
    
    # Fallback: méthode ancienne
    print("DEBUG: Fallback vers méthode ancienne")
    top, bottom = h_sorted[0], h_sorted[-1]
    left, right = v_sorted[0], v_sorted[-1]
    return [top, bottom, left, right]

# -----------------------
# 8) Intersection de 2 lignes (inchangé)
# -----------------------
def line_intersection(l1, l2):
    x1, y1, x2, y2 = l1
    x3, y3, x4, y4 = l2
    A1, B1, C1 = y2-y1, x1-x2, x2*y1 - x1*y2
    A2, B2, C2 = y4-y3, x3-x4, x4*y3 - x3*y4
    det = A1*B2 - A2*B1
    if abs(det) < 1e-10:  # Amélioration: tolérance numérique
        return None
    x = (B1*C2 - B2*C1) / det
    y = (C1*A2 - C2*A1) / det
    return int(x), int(y)

# -----------------------
# 9) Validation du quadrilatère
# -----------------------
def validate_quad(quad, img_shape):
    """Valide que le quadrilatère est un carré raisonnable"""
    if quad is None:
        return False
    
    h, w = img_shape[:2]
    
    # Vérifier que tous les points sont dans l'image
    for point in quad:
        x, y = point
        if x < 0 or x >= w or y < 0 or y >= h:
            return False
    
    # Vérifier que c'est approximativement un CARRÉ
    tl, tr, br, bl = quad
    
    # Calculer les côtés
    top_length = np.linalg.norm(tr - tl)
    bottom_length = np.linalg.norm(br - bl)
    left_length = np.linalg.norm(bl - tl)
    right_length = np.linalg.norm(br - tr)
    
    # Vérifier que les côtés opposés ont des longueurs similaires (±20%)
    if (abs(top_length - bottom_length) > 0.2 * max(top_length, bottom_length) or
        abs(left_length - right_length) > 0.2 * max(left_length, right_length)):
        return False
    
    # CONTRAINTE CARRÉ: Vérifier que largeur ≈ hauteur (±20%)
    avg_width = (top_length + bottom_length) / 2
    avg_height = (left_length + right_length) / 2
    aspect_ratio = abs(avg_width - avg_height) / max(avg_width, avg_height)
    
    if aspect_ratio > 0.2:  # Plus de 20% de différence = pas un carré
        print(f"❌ Rejeté: aspect ratio {aspect_ratio:.2f} (largeur: {avg_width:.1f}, hauteur: {avg_height:.1f})")
        return False
    
    # Vérifier la taille minimale (au moins 50x50 pixels)
    if avg_width < 50 or avg_height < 50:
        return False
    
    # Vérifier que ce n'est pas trop grand (max 80% de l'image)
    if avg_width > 0.8 * w or avg_height > 0.8 * h:
        return False
    
    print(f"✅ Carré validé: {avg_width:.1f}x{avg_height:.1f}, ratio: {aspect_ratio:.3f}")
    return True

# -----------------------
# 10) Quadrilatère simple avec extension et DEBUG
# -----------------------
def build_quad(main_lines, img_shape):
    if main_lines is None:
        return None
    
    top, bottom, left, right = main_lines
    
    print(f"DEBUG: Lignes reçues:")
    print(f"  Top: {top}")
    print(f"  Bottom: {bottom}")
    print(f"  Left: {left}")
    print(f"  Right: {right}")
    
    # Intersections
    tl = line_intersection(top, left)
    tr = line_intersection(top, right)
    br = line_intersection(bottom, right)
    bl = line_intersection(bottom, left)
    
    print(f"DEBUG: Intersections calculées:")
    print(f"  TL: {tl}, TR: {tr}, BR: {br}, BL: {bl}")
    
    if None in [tl, tr, br, bl]:
        print("DEBUG: Une intersection est None, échec")
        return None
    
    quad = np.array([tl, tr, br, bl], dtype=np.float32)
    
    print(f"DEBUG: Quadrilatère avant validation:")
    for i, point in enumerate(['TL', 'TR', 'BR', 'BL']):
        print(f"  {point}: ({quad[i][0]:.1f}, {quad[i][1]:.1f})")
    
    # Vérifier que tous les points sont dans l'image
    h, w = img_shape[:2]
    for i, (x, y) in enumerate(quad):
        if x < 0 or x >= w or y < 0 or y >= h:
            print(f"DEBUG: Point {['TL', 'TR', 'BR', 'BL'][i]} hors limites: ({x:.1f}, {y:.1f}) pour image {w}x{h}")
    
    if not validate_quad(quad, img_shape):
        return None
        
    return quad

# -----------------------
# 11) Warp avec debug détaillé
# -----------------------
def warp_face(image, quad, size=300):
    print(f"DEBUG: Warp - image shape: {image.shape}")
    print(f"DEBUG: Warp - quad points:")
    for i, point in enumerate(['TL', 'TR', 'BR', 'BL']):
        print(f"  {point}: ({quad[i][0]:.1f}, {quad[i][1]:.1f})")
    
    dst = np.array([[0,0],[size-1,0],[size-1,size-1],[0,size-1]], dtype=np.float32)
    print(f"DEBUG: Warp - destination: {dst}")
    
    try:
        M = cv2.getPerspectiveTransform(quad, dst)
        print(f"DEBUG: Warp - matrice de transformation calculée")
        warped = cv2.warpPerspective(image, M, (size, size))
        print(f"DEBUG: Warp - image warpée créée, shape: {warped.shape}")
        
        # Vérifier si l'image warpée n'est pas complètement noire
        mean_intensity = np.mean(warped)
        print(f"DEBUG: Warp - intensité moyenne: {mean_intensity:.2f}")
        if mean_intensity < 10:
            print("DEBUG: ATTENTION - Image warpée très sombre!")
        
        return warped
    except Exception as e:
        print(f"DEBUG: Erreur dans warp: {e}")
        return None

def extract_grid(warped, save_prefix=None):
    h, w, _ = warped.shape
    sy, sx = h//3, w//3
    dbg = warped.copy()
    cells = []
    cid = 1
    for i in range(3):
        for j in range(3):
            y1, y2 = i*sy, (i+1)*sy
            x1, x2 = j*sx, (j+1)*sx
            roi = warped[y1:y2, x1:x2]
            cells.append(((i,j), roi))
            cv2.rectangle(dbg, (x1,y1), (x2,y2), (0,255,0), 2)
            cv2.putText(dbg, str(cid), (x1+10,y1+25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            if save_prefix and roi.size > 0:
                cv2.imwrite(f"{save_prefix}_cell_{i}{j}.jpg", roi)
            cid += 1
    return dbg, cells

# -----------------------
# 12) Pipeline amélioré
# -----------------------
def process_one_face(image, auto=True, settings=None, show=False, name="", save_prefix=None):
    gray, settings = prepare_image(image, auto, settings)
    edges = detect_edges(gray, settings, use_mask=True)
    lines = detect_lines(edges, adaptive=True)
    h_lines, v_lines = classify_lines(lines, angle_tol=15)
    main_lines = select_main_lines(h_lines, v_lines, image.shape)
    quad = build_quad(main_lines, image.shape)

    warped, grid_dbg, cells = None, None, []
    lines_dbg = image.copy()
    
    # Visualisation des lignes détectées
    if lines is not None:
        for l in lines:
            x1, y1, x2, y2 = l[0]
            cv2.line(lines_dbg, (x1,y1), (x2,y2), (0,255,0), 1)
    
    # Visualisation des lignes principales sélectionnées
    if main_lines is not None:
        for line in main_lines:
            x1, y1, x2, y2 = line
            cv2.line(lines_dbg, (x1,y1), (x2,y2), (255,0,0), 3)

    if quad is not None:
        cv2.polylines(lines_dbg, [quad.astype(int)], True, (0,0,255), 2)
        warped = warp_face(image, quad, 300)
        grid_dbg, cells = extract_grid(warped, save_prefix)

    if show:
        plt.figure(figsize=(16,8))
        plt.subplot(2,3,1); plt.imshow(gray, cmap="gray"); plt.title(f"{name}-gray"); plt.axis("off")
        plt.subplot(2,3,2); plt.imshow(edges, cmap="gray"); plt.title(f"{name}-edges+mask"); plt.axis("off")
        plt.subplot(2,3,3); plt.imshow(cv2.cvtColor(lines_dbg, cv2.COLOR_BGR2RGB)); plt.title(f"{name}-lines+quad"); plt.axis("off")
        if warped is not None:
            plt.subplot(2,3,4); plt.imshow(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)); plt.title(f"{name}-warped"); plt.axis("off")
            plt.subplot(2,3,5); plt.imshow(cv2.cvtColor(grid_dbg, cv2.COLOR_BGR2RGB)); plt.title(f"{name}-grid"); plt.axis("off")
        plt.tight_layout(); plt.show()

    return {
        "quad": quad,
        "warped": warped,
        "cells": cells,
        "settings": settings,
        "lines_count": len(lines) if lines is not None else 0,
        "h_lines_count": len(h_lines),
        "v_lines_count": len(v_lines)
    }

# -----------------------
# 13) Batch avec statistiques
# -----------------------
def f(files, auto=True, settings=None, show=False):
    results = {}
    success_count = 0
    
    for path in files:
        img = cv2.imread(path)
        if img is None:
            print(f"⚠️ Impossible de lire {path}")
            continue
            
        name = os.path.splitext(os.path.basename(path))[0]
        save_prefix = os.path.join(os.path.dirname(path), name)
        res = process_one_face(img, auto, settings, show, name, save_prefix)
        results[path] = res
        
        if res["warped"] is None:
            print(f"⚠️ {name}: pas de quadrilatère trouvé (lignes: {res['lines_count']}, H: {res['h_lines_count']}, V: {res['v_lines_count']})")
        else:
            print(f"✅ {name}: warp OK, 9 cellules sauvegardées (lignes: {res['lines_count']})")
            success_count += 1
    
    print(f"\n📊 Résumé: {success_count}/{len(files)} faces traitées avec succès")
    return results

def process_face_with_roi(image_path, roi_coords, face_name, show=False, save_intermediates=True):
    """Traite une face en utilisant une ROI calibrée.

    Compatible 2 formats :
      - bbox: (x1,y1,x2,y2)
      - quad: ((xTL,yTL),(xTR,yTR),(xBR,yBR),(xBL,yBL))
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Erreur: impossible de charger {image_path}")
        return None, None

    h, w = image.shape[:2]

    def is_bbox(v):
        return isinstance(v, (list, tuple)) and len(v) == 4 and all(not isinstance(x, (list, tuple)) for x in v)

    def is_quad(v):
        return isinstance(v, (list, tuple)) and len(v) == 4 and all(isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in v)

    # Valeurs de sortie (remplies selon branche)
    image_with_roi = None
    cube_roi = None
    warped = None
    grid_dbg = None
    cells = None

    # --- BBOX mode (legacy) ---
    if is_bbox(roi_coords):
        x1, y1, x2, y2 = map(int, roi_coords)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        image_with_roi = image.copy()
        cv2.rectangle(image_with_roi, (x1, y1), (x2, y2), (0, 0, 255), 3)
        cv2.putText(image_with_roi, f'ROI {face_name}', (x1, max(0, y1-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cube_roi = image[y1:y2, x1:x2]
        if cube_roi.size == 0:
            print(f"Erreur: ROI vide pour {face_name}")
            return None, None

        warped = cv2.resize(cube_roi, (300, 300))
        grid_dbg, cells = extract_grid(warped, save_prefix=f"tmp/calibrated_{face_name}")

        if save_intermediates:
            cv2.imwrite(f"tmp/{face_name}_1_original_with_roi.jpg", image_with_roi)
            cv2.imwrite(f"tmp/{face_name}_2_roi_extracted.jpg", cube_roi)
            cv2.imwrite(f"tmp/{face_name}_3_warped_300x300.jpg", warped)
            if grid_dbg is not None:
                cv2.imwrite(f"tmp/{face_name}_4_grid_3x3.jpg", grid_dbg)

    # --- QUAD mode (redressement) ---
    elif is_quad(roi_coords):
        quad = np.array([(int(px), int(py)) for (px, py) in roi_coords], dtype=np.float32)

        quad[:, 0] = np.clip(quad[:, 0], 0, w-1)
        quad[:, 1] = np.clip(quad[:, 1], 0, h-1)

        image_with_roi = image.copy()
        cv2.polylines(image_with_roi, [quad.astype(int)], True, (0, 0, 255), 3)
        cv2.putText(image_with_roi, f'QUAD {face_name}', (int(quad[0][0]), max(0, int(quad[0][1])-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        warped = warp_face(image, quad, 300)
        if warped is None:
            print(f"Erreur: warp QUAD échoué pour {face_name}")
            return None, None

        grid_dbg, cells = extract_grid(warped, save_prefix=f"tmp/calibrated_{face_name}")

        if save_intermediates:
            cv2.imwrite(f"tmp/{face_name}_1_original_with_roi.jpg", image_with_roi)
            cv2.imwrite(f"tmp/{face_name}_3_warped_300x300.jpg", warped)
            if grid_dbg is not None:
                cv2.imwrite(f"tmp/{face_name}_4_grid_3x3.jpg", grid_dbg)

    else:
        print(f"Erreur: ROI invalide pour {face_name}: {roi_coords}")
        return None, None

    # --- AFFICHAGE DEBUG (COMMUN) ---
    if show and (image_with_roi is not None) and (warped is not None) and (grid_dbg is not None):

        # 3 vignettes communes
        plt.figure(figsize=(12, 4))

        plt.subplot(1, 3, 1)
        plt.imshow(cv2.cvtColor(image_with_roi, cv2.COLOR_BGR2RGB))
        plt.title(f"{face_name} - ROI / QUAD")
        plt.axis("off")

        plt.subplot(1, 3, 2)
        plt.imshow(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
        plt.title(f"{face_name} - Face 300x300")
        plt.axis("off")

        plt.subplot(1, 3, 3)
        plt.imshow(cv2.cvtColor(grid_dbg, cv2.COLOR_BGR2RGB))
        plt.title(f"{face_name} - Grille 3x3")
        plt.axis("off")

        plt.tight_layout()
        plt.show()

    return warped, cells


def visualize_color_grid(colors, face_name, save_to_tmp=True):
    """Affiche une grille 3x3 colorée avec les vraies couleurs Rubik's"""
    # Créer une image 300x300 pour visualiser la grille
    grid_img = np.ones((300, 300, 3), dtype=np.uint8) * 50  # Fond gris
    
    # Couleurs RÉELLES d'un Rubik's cube (en BGR pour OpenCV)
    color_map = {
        "red": (0, 0, 255),        # Rouge pur
        "orange": (0, 127, 255),   # Orange Rubik's
        "yellow": (0, 255, 255),   # Jaune pur
        "green": (0, 255, 0),      # Vert pur
        "blue": (255, 0, 0),       # Bleu pur
        "white": (255, 255, 255),  # Blanc pur
        "black": (0, 0, 0),        # Noir (rare)
        "unknown": (128, 128, 128) # Gris pour inconnu
    }
    
    cell_size = 100
    for idx, color in enumerate(colors):
        i, j = idx // 3, idx % 3
        y1, y2 = i * cell_size, (i + 1) * cell_size
        x1, x2 = j * cell_size, (j + 1) * cell_size
        
        # Couleur de remplissage
        if color in color_map:
            fill_color = color_map[color]
        elif color.startswith("rgb("):
            # Extraire les valeurs RGB du format "rgb(r,g,b)"
            try:
                rgb_str = color[4:-1]  # Enlever "rgb(" et ")"
                r, g, b = map(float, rgb_str.split(','))
                fill_color = (int(b), int(g), int(r))  # Convertir en BGR
            except:
                fill_color = (128, 128, 128)
        elif color.startswith("hsv("):
            # Extraire les valeurs HSV du format "hsv(h,s,v)"
            try:
                hsv_str = color[4:-1]  # Enlever "hsv(" et ")"
                h, s, v = map(float, hsv_str.split(','))
                # Convertir HSV en BGR
                hsv_array = np.uint8([[[h, s, v]]])
                bgr_array = cv2.cvtColor(hsv_array, cv2.COLOR_HSV2BGR)
                fill_color = tuple(map(int, bgr_array[0, 0]))
            except:
                fill_color = (128, 128, 128)
        else:
            fill_color = (128, 128, 128)  # Gris pour inconnu
        
        # Remplir la cellule
        grid_img[y1:y2, x1:x2] = fill_color
        
        # Ajouter le texte avec couleur contrastée
        text_color = (0, 0, 0) if color in ["white", "yellow"] else (255, 255, 255)
        
        # Nom de la couleur (3 premières lettres)
        color_abbrev = color[:3] if len(color) >= 3 else color
        cv2.putText(grid_img, color_abbrev, (x1 + 10, y1 + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        # Numéro de cellule
        cv2.putText(grid_img, f"{idx+1}", (x1 + 10, y1 + 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Dessiner la grille noire
    for i in range(4):
        cv2.line(grid_img, (0, i * cell_size), (300, i * cell_size), (0, 0, 0), 3)
        cv2.line(grid_img, (i * cell_size, 0), (i * cell_size, 300), (0, 0, 0), 3)
    
    # Sauvegarder l'image de la grille colorée
    if save_to_tmp:
        try:
            cv2.imwrite(f"tmp/{face_name}_5_color_grid.jpg", grid_img)
            print(f"Grille colorée sauvegardée: tmp/{face_name}_5_color_grid.jpg")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la grille colorée: {e}")
    
    # Afficher
    plt.figure(figsize=(10, 8))
    plt.imshow(cv2.cvtColor(grid_img, cv2.COLOR_BGR2RGB))
    plt.title(f"Grille des couleurs - Face {face_name}", fontsize=16, fontweight='bold')
    plt.axis('off')
    
    # Ajouter la légende des couleurs à droite
    legend_text = "Légende:\n" + "\n".join([f"{i+1}: {color}" for i, color in enumerate(colors)])
    plt.text(320, 150, legend_text, fontsize=11, verticalalignment='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
    return grid_img

# Fonction de debug (pour le menu)

def test_single_face_debug(face_name, roi_coords, color_calibration=None):
    """Version debug complète avec visualisation des couleurs"""
    file_path = f"tmp/{face_name}.jpg"

    if not os.path.exists(file_path):
        print(f"Fichier {file_path} non trouvé")
        return None

    print(f"TEST DEBUG - Face {face_name} avec ROI {roi_coords}")

    warped, cells = process_face_with_roi(file_path, roi_coords, face_name, show=True)

    if warped is None or cells is None:
        print(f"Échec du test de la face {face_name}")
        return None

    # === Couleurs détectées (la vraie fonction) ===
    colors = (
        #analyze_colors_with_calibration(cells, color_calibration, debug=True)
        #if color_calibration is not None
        # else analyze_colors(cells)
        analyze_colors_simple(cells, debug=True)
    )

    print(f"Face {face_name} testée avec succès")
    print(f"Couleurs détectées: {colors}")

    # Afficher la grille colorée
    visualize_color_grid(colors, face_name)

    # === Logs RGB cohérents avec la classification (marge + médiane) ===
    print("\nDétail des couleurs par cellule (même sampling que la classification):")
    for idx, ((i, j), cell_roi) in enumerate(cells):
        r, g, b = sample_rgb_from_cell_bgr(cell_roi, margin=0.25)
        print(f"  Cellule {idx+1} ({i},{j}): RGB({r:.0f},{g:.0f},{b:.0f}) -> {colors[idx]}")
        if (idx + 1) in (8, 9):
            h = _hue_deg_from_rgb(r, g, b)
            print(f"    ### HSV CELL {idx+1} ### h={h:.1f}")

        # LAB debug (si tu veux) sur LE MÊME ROI interne (marge identique)
        if (idx + 1) in (7, 8, 9) and cell_roi is not None and cell_roi.size > 0:
            h, w = cell_roi.shape[:2]
            mh, mw = int(h * 0.25), int(w * 0.25)
            inner = cell_roi[mh:h-mh, mw:w-mw]
            if inner.size > 0:
                lab = cv2.cvtColor(inner, cv2.COLOR_BGR2LAB)
                L, a, bb = lab.reshape(-1, 3).mean(axis=0)
                chroma = ((a - 128) ** 2 + (bb - 128) ** 2) ** 0.5
                print(f"    ### LAB DEBUG ### Cell {idx+1} L={L:.1f} a={a:.1f} b={bb:.1f} chroma={chroma:.1f}")
        if idx == 8:  # cellule 9 (bas-droite)
            h_deg, s, v = _hsv_from_rgb(r, g, b)
            print(f"### CELL9 HSV ### h={h_deg:.1f} s={s:.0f} v={v:.0f} RGB=({r:.0f},{g:.0f},{b:.0f}) -> {colors[idx]}")


    return {
        "warped": warped,
        "cells": cells,
        "colors": colors,
        "roi": roi_coords
    }
