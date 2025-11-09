# process_images_cube.py - Version améliorée
# RESUME : Prcoessus de reconnsainces des images et encode du cube dans un format FacesDict
# FacesDict permet d'encoder le cube en colueurs (c'est un tableau 3x3 dans ce cas)
# Le point d'entrée principal est detect_colors_for_faces qui est la fonction 
# detect_colors_for_faces
#
# ============================================================================
#  process_images_cube.py
#  ----------------------
#  Objectif :
#     Pipeline de reconnaissance visuelle d’un Rubik’s Cube à partir d’images.
#     Le code détecte les faces, extrait les 9 cases (3x3), identifie les couleurs,
#     et encode le résultat sous forme de dictionnaire FacesDict.
#
#  Entrée principale :
#     - detect_colors_for_faces(image_folder, roi_data, color_calibration=None, debug="text")
#       -> Retourne un FacesDict avec les 6 faces reconnues.
#
#  Étapes principales du pipeline :
#     1) Prétraitement image :
#        - prepare_image : conversion N&B, flou, CLAHE
#        - detect_edges : contours Canny + masque
#     2) Détection cube :
#        - detect_lines / classify_lines / select_main_lines : détection des lignes
#        - detect_cube_boundary / detect_cube_simple : alternatives par contour
#        - build_quad / validate_quad / warp_face : construction & normalisation d’un carré
#     3) Extraction grille :
#        - extract_grid : découpe en 9 cellules (3x3)
#     4) Analyse des couleurs :
#        - analyze_colors / analyze_colors_with_calibration : classification par défaut ou calibrée
#        - visualize_color_grid : affichage et sauvegarde de la grille colorée
#
#  Fonctions de support :
#     - process_one_face / process_one_face_debug : pipeline complet pour une face
#     - process_face_with_roi : traitement direct d’une ROI calibrée
#     - f : traitement batch d’une liste d’images avec stats
#
#  Calibration & debug :
#     - test_single_face_debug : test complet avec affichage
#     - calibrate_colors_interactive : calibration manuelle des couleurs
#     - save_color_calibration / load_color_calibration : gestion calibration JSON
#     - FaceSelector / display_and_select_cell : interface clic pour choisir une cellule
#
# ============================================================================




import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from calibration_rubiks import load_calibration
from types_shared import FaceResult, FacesDict

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

# FACADE du fichier detect_colors_for_faces renvoie un cube dont les oculeurs ont été identifiées

def detect_colors_for_faces(image_folder, roi_data, color_calibration=None, debug="text") -> FacesDict:
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
        cols = (analyze_colors_with_calibration(cells, color_calibration)
                if color_calibration is not None
                else analyze_colors(cells))

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

        from collections import Counter
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
    """Traite une face en utilisant la ROI calibrée"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"Erreur: impossible de charger {image_path}")
        return None, None
    
    x1, y1, x2, y2 = roi_coords
    
    # Vérifier que la ROI est dans les limites de l'image
    h, w = image.shape[:2]
    if x2 > w or y2 > h or x1 < 0 or y1 < 0:
        print(f"Attention: ROI hors limites pour {face_name}: ({x1}, {y1}) -> ({x2}, {y2}) pour image {w}x{h}")
        # Ajuster les coordonnées
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        print(f"ROI ajustée: ({x1}, {y1}) -> ({x2}, {y2})")
    
    # Créer une image avec la ROI marquée
    image_with_roi = image.copy()
    cv2.rectangle(image_with_roi, (x1, y1), (x2, y2), (0, 0, 255), 3)
    cv2.putText(image_with_roi, f'ROI {face_name}', (x1, y1-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Extraire la ROI
    cube_roi = image[y1:y2, x1:x2]
    
    if cube_roi.size == 0:
        print(f"Erreur: ROI vide pour {face_name}")
        return None, None
    
    print(f"Face {face_name}: ROI extraite ({x2-x1}x{y2-y1} pixels)")
    
    # Redimensionner à 300x300 pour standardiser
    warped = cv2.resize(cube_roi, (300, 300))
    
    # Extraire la grille 3x3
    grid_dbg, cells = extract_grid(warped, save_prefix=f"tmp/calibrated_{face_name}")
    
    # Sauvegarder les images intermédiaires
    if save_intermediates:
        try:
            cv2.imwrite(f"tmp/{face_name}_1_original_with_roi.jpg", image_with_roi)
            cv2.imwrite(f"tmp/{face_name}_2_roi_extracted.jpg", cube_roi)
            cv2.imwrite(f"tmp/{face_name}_3_warped_300x300.jpg", warped)
            if grid_dbg is not None:
                cv2.imwrite(f"tmp/{face_name}_4_grid_3x3.jpg", grid_dbg)
            print(f"Images intermédiaires sauvegardées pour {face_name}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des images intermédiaires: {e}")
    
    if show:
        plt.figure(figsize=(15, 5))
        
        plt.subplot(1, 4, 1)
        plt.imshow(cv2.cvtColor(image_with_roi, cv2.COLOR_BGR2RGB))
        plt.title(f"{face_name} - Image avec ROI")
        plt.axis('off')
        
        plt.subplot(1, 4, 2)
        plt.imshow(cv2.cvtColor(cube_roi, cv2.COLOR_BGR2RGB))
        plt.title(f"{face_name} - ROI extraite")
        plt.axis('off')
        
        plt.subplot(1, 4, 3)
        plt.imshow(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
        plt.title(f"{face_name} - Face 300x300")
        plt.axis('off')
        
        plt.subplot(1, 4, 4)
        plt.imshow(cv2.cvtColor(grid_dbg, cv2.COLOR_BGR2RGB))
        plt.title(f"{face_name} - Grille 3x3")
        plt.axis('off')
        
        plt.tight_layout()
        plt.show()
    
    return warped, cells

# Fonctions liées à la calibration

def load_color_calibration(filename="rubiks_color_calibration.json"):
    """Charge la calibration des couleurs"""
    if not os.path.exists(filename):
        return None
    
    try:
        import json
        with open(filename, 'r') as f:
            data = json.load(f)
        
        color_data = data.get("color_data", data)  # Support ancien format
        
        # Convertir en format interne
        color_calibration = {}
        for color_name, [r, g, b, tolerance] in color_data.items():
            color_calibration[color_name] = (r, g, b, tolerance)
        
        print(f"Calibration couleurs chargée: {list(color_calibration.keys())}")
        return color_calibration
    
    except Exception as e:
        print(f"Erreur lors du chargement des couleurs: {e}")
        return None

def classify_color_default(r, g, b):
    """Classification par défaut avec meilleure séparation jaune/orange"""
    # Convertir en HSV pour une meilleure classification
    rgb_normalized = np.array([[[r, g, b]]], dtype=np.uint8)
    hsv = cv2.cvtColor(rgb_normalized, cv2.COLOR_RGB2HSV)[0, 0]
    h, s, v = hsv
    
    # Classification basée sur HSV (plus robuste)
    if s < 50 and v > 200:  # Faible saturation, haute luminosité
        return "white"
    elif s < 50 and v < 50:  # Faible saturation, faible luminosité  
        return "black"
    elif h < 10 or h > 170:  # Rouge
        return "red"
    elif 10 <= h < 25:  # Orange (plage plus étroite)
        return "orange"
    elif 25 <= h < 35:  # Jaune (plage plus étroite) 
        return "yellow"
    elif 35 <= h < 85:  # Vert
        return "green"
    elif 85 <= h < 125:  # Cyan/Bleu
        return "blue"
    elif 125 <= h < 170:  # Magenta
        return "blue"  # Souvent perçu comme bleu sur un Rubik's
    else:
        return f"hsv({h},{s},{v})"

def classify_with_calibration(r, g, b, color_calibration):
    """Classification avec couleurs de référence calibrées"""
    min_distance = float('inf')
    best_color = "unknown"
    
    for color_name, (ref_r, ref_g, ref_b, tolerance) in color_calibration.items():
        # Distance euclidienne dans l'espace RGB
        distance = np.sqrt((r - ref_r)**2 + (g - ref_g)**2 + (b - ref_b)**2)
        
        if distance < tolerance and distance < min_distance:
            min_distance = distance
            best_color = color_name
    
    return best_color if best_color != "unknown" else f"rgb({r:.0f},{g:.0f},{b:.0f})"

def analyze_colors_with_calibration(cells, color_calibration=None):
    """Analyse les couleurs avec calibration optionnelle"""
    colors = []
    
    for (_i, _j), cell_roi in cells:
        if cell_roi.size == 0:
            colors.append("unknown")
            continue
        
        # Prendre la région centrale de la cellule (80% du centre)
        h, w = cell_roi.shape[:2]
        center_h, center_w = int(h * 0.1), int(w * 0.1)
        center_roi = cell_roi[center_h:h-center_h, center_w:w-center_w]
        
        if center_roi.size == 0:
            colors.append("unknown")
            continue
        
        # Couleur moyenne en BGR puis RGB
        mean_color = np.mean(center_roi, axis=(0, 1))
        b, g, r = mean_color
        
        if color_calibration is not None:
            # Utiliser la calibration pour classifier
            color = classify_with_calibration(r, g, b, color_calibration)
        else:
            # Classification par défaut améliorée
            color = classify_color_default(r, g, b)
        
        colors.append(color)
    
    return colors

def analyze_colors(cells):
    """Version de compatibilité qui charge automatiquement la calibration couleurs"""
    color_calibration = load_color_calibration()
    return analyze_colors_with_calibration(cells, color_calibration)

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
    
    if warped is not None and cells is not None:
        colors = analyze_colors_with_calibration(cells, color_calibration) \
                if color_calibration is not None else analyze_colors(cells)
        print(f"Face {face_name} testée avec succès")
        print(f"Couleurs détectées: {colors}")
        
        # Afficher la grille colorée
        visualize_color_grid(colors, face_name)
        
        # Afficher les valeurs RGB de chaque cellule
        print("\nDétail des couleurs par cellule:")
        for idx, ((i, j), cell_roi) in enumerate(cells):
            if cell_roi.size > 0:
                h, w = cell_roi.shape[:2]
                center_h, center_w = int(h * 0.1), int(w * 0.1)
                center_roi = cell_roi[center_h:h-center_h, center_w:w-center_w]
                if center_roi.size > 0:
                    mean_color = np.mean(center_roi, axis=(0, 1))
                    b, g, r = mean_color
                    print(f"  Cellule {idx+1} ({i},{j}): RGB({r:.0f},{g:.0f},{b:.0f}) -> {colors[idx]}")
        
        return {
            "warped": warped,
            "cells": cells,
            "colors": colors,
            "roi": roi_coords
        }
    else:
        print(f"Échec du test de la face {face_name}")
        return None

def calibrate_colors_interactive():
    """Mode interactif pour calibrer les couleurs avec interface cliquable"""
    print("\nMODE CALIBRATION DES COULEURS")
    print("Vous allez définir les couleurs de référence pour chaque couleur du Rubik's cube")
    
    # Charger la calibration ROI existante
    roi_data = load_calibration()
    if roi_data is None:
        print("Aucune calibration ROI trouvée. Calibrez d'abord les positions.")
        return None
    
    color_calibration = {}
    rubiks_colors = ["red", "orange", "yellow", "green", "blue", "white"]
    
    for color_name in rubiks_colors:
        print(f"\n=== Calibration couleur: {color_name.upper()} ===")
        
        # Afficher les faces et permettre la sélection par clic
        selected_face, selected_cell = display_and_select_cell(roi_data, color_name)
        
        if selected_face is None or selected_cell is None:
            print(f"Couleur {color_name} ignorée")
            continue
        
        # Extraire la couleur de la cellule sélectionnée
        file_path = f"tmp/{selected_face}.jpg"
        warped, cells = process_face_with_roi(file_path, roi_data[selected_face], selected_face, show=False)
        
        if warped is not None and cells is not None and selected_cell < len(cells):
            (_i, _j), cell_roi = cells[selected_cell]
            
            # Extraire la couleur moyenne
            h, w = cell_roi.shape[:2]
            center_h, center_w = int(h * 0.1), int(w * 0.1)
            center_roi = cell_roi[center_h:h-center_h, center_w:w-center_w]
            
            if center_roi.size > 0:
                mean_color = np.mean(center_roi, axis=(0, 1))
                b, g, r = mean_color
                
                # Demander la tolérance
                tolerance = input(f"Tolérance pour {color_name} (défaut: 50)? ").strip()
                try:
                    tolerance = float(tolerance) if tolerance else 50.0
                except ValueError:
                    tolerance = 50.0
                
                color_calibration[color_name] = (r, g, b, tolerance)
                print(f"Couleur {color_name} calibrée: RGB({r:.0f},{g:.0f},{b:.0f}) ±{tolerance}")
    
    # Sauvegarder la calibration
    if color_calibration:
        save_color_calibration(color_calibration)
        print(f"\nCalibration des couleurs sauvegardée")
        print(f"Couleurs calibrées: {list(color_calibration.keys())}")
    
    return color_calibration


class FaceSelector:
    """Classe pour gérer la sélection interactive des cellules"""
    
    def __init__(self, roi_data, color_name):
        self.roi_data = roi_data
        self.color_name = color_name
        self.selected_face = None
        self.selected_cell = None
        self.face_images = {}
        self.face_positions = {}
        
    def load_face_images(self):
        """Charge toutes les images des faces"""
        faces_order = ["F", "R", "B", "L", "U", "D"]
        
        for face in faces_order:
            file_path = f"tmp/{face}.jpg"
            if os.path.exists(file_path) and face in self.roi_data:
                image = cv2.imread(file_path)
                if image is not None:
                    # Convertir BGR vers RGB
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    self.face_images[face] = image_rgb
    
    def on_click(self, event):
        """Gestionnaire de clic sur l'image"""
        if event.inaxes is None:
            return
        
        # Identifier sur quelle face on a cliqué
        for face, ax in self.face_positions.items():
            if event.inaxes == ax:
                # Calculer quelle cellule a été cliquée
                x, y = event.xdata, event.ydata
                cell = self.get_cell_from_coordinates(face, x, y)
                
                if cell is not None:
                    self.selected_face = face
                    self.selected_cell = cell
                    print(f"\nSélectionné: Face {face}, Cellule {cell + 1}")
                    
                    # Fermer la fenêtre matplotlib
                    plt.close('all')
                break
    
    def get_cell_from_coordinates(self, face, x, y):
        """Détermine quelle cellule (0-8) correspond aux coordonnées cliquées"""
        if face not in self.roi_data:
            return None
        
        x1, y1, x2, y2 = self.roi_data[face]
        
        # Vérifier si le clic est dans la ROI
        if not (x1 <= x <= x2 and y1 <= y <= y2):
            return None
        
        # Calculer la cellule (grille 3x3)
        cell_width = (x2 - x1) / 3
        cell_height = (y2 - y1) / 3
        
        col = int((x - x1) / cell_width)
        row = int((y - y1) / cell_height)
        
        # S'assurer qu'on reste dans les limites
        col = max(0, min(2, col))
        row = max(0, min(2, row))
        
        return row * 3 + col
    
    def display_faces(self):
        """Affiche les faces dans une grille cliquable"""
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Sélectionnez une cellule contenant du {self.color_name.upper()}', 
                     fontsize=16, fontweight='bold')
        
        faces_order = ["F", "R", "B", "L", "U", "D"]
        face_names = {
            "F": "Front", "R": "Right", "B": "Back", 
            "L": "Left", "U": "Up", "D": "Down"
        }
        
        for idx, face in enumerate(faces_order):
            row = idx // 3
            col = idx % 3
            ax = axes[row, col]
            self.face_positions[face] = ax
            
            if face in self.face_images:
                image = self.face_images[face]
                ax.imshow(image)
                
                # Dessiner la ROI (rectangle vert semi-transparent)
                x1, y1, x2, y2 = self.roi_data[face]
                from matplotlib.patches import Rectangle
                rect = Rectangle((x1, y1), x2-x1, y2-y1, 
                               linewidth=3, edgecolor='lime', facecolor='none')
                ax.add_patch(rect)
                
                # Dessiner la grille des cellules (lignes fines)
                cell_width = (x2 - x1) / 3
                cell_height = (y2 - y1) / 3
                
                for i in range(1, 3):
                    # Lignes verticales
                    ax.axvline(x=x1 + i * cell_width, ymin=(y1/image.shape[0]), 
                              ymax=(y2/image.shape[0]), color='white', linewidth=1, alpha=0.7)
                    # Lignes horizontales
                    ax.axhline(y=y1 + i * cell_height, xmin=(x1/image.shape[1]), 
                              xmax=(x2/image.shape[1]), color='white', linewidth=1, alpha=0.7)
                
                ax.set_title(f'Face {face} ({face_names[face]})', fontsize=12, fontweight='bold')
            else:
                ax.text(0.5, 0.5, f'Face {face}\nnon trouvée', 
                       ha='center', va='center', transform=ax.transAxes,
                       fontsize=12, color='red')
            
            ax.axis('off')
        
        # Connecter l'événement de clic
        fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Ajouter les instructions
        fig.text(0.5, 0.02, 'Cliquez sur une cellule dans la zone verte pour la sélectionner', 
                ha='center', fontsize=12, style='italic')
        
        plt.tight_layout()
        plt.show()


def display_and_select_cell(roi_data, color_name):
    """Affiche les faces et permet la sélection d'une cellule par clic"""
    selector = FaceSelector(roi_data, color_name)
    selector.load_face_images()
    
    if not selector.face_images:
        print("Aucune image de face trouvée")
        return None, None
    
    print(f"\nSélectionnez une cellule contenant du {color_name}")
    print("Cliquez sur une cellule dans la zone verte de n'importe quelle face")
    print("Fermez la fenêtre pour annuler")
    
    selector.display_faces()
    
    return selector.selected_face, selector.selected_cell


def save_color_calibration(color_calibration):
    """Sauvegarde la calibration des couleurs"""
    color_filename = "rubiks_color_calibration.json"
    
    # Convertir en format JSON serializable
    color_data = {}
    for color_name, (r, g, b, tolerance) in color_calibration.items():
        color_data[color_name] = [float(r), float(g), float(b), float(tolerance)]
    
    import json
    with open(color_filename, 'w') as f:
        json.dump({
            "metadata": {
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "colors_count": len(color_data),
                "version": "1.0"
            },
            "color_data": color_data
        }, f, indent=2)