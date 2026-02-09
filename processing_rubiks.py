# processing_rubiks.py
# Corps princpal permettant d'encoder l'état principal du cube pour que il soit
# interpretable par le solveur kociemba convert_to_kociemba
# il prend en entrée un cube encodé FacesDict
# il contien aussi des fonctions de debug
# ============================================================================
#  processing_rubiks.py
#  --------------------
#  Objectif :
#     Module central pour transformer les résultats de vision (FacesDict)
#     en un encodage standard Singmaster (chaîne 54 URFDLB) utilisable
#     par le solveur de type Kociemba.
#
#  Étapes principales :
#     1) Correction orientation robot :
#        - apply_robot_orientation_corrections
#        - rotate_face_grid / rotate_cells_grid
#     2) Réorientation standard Kociemba :
#        - reorient_cube_for_kociemba
#     3) Encodage des faces :
#        - create_color_mapping : centre → lettre
#        - encode_with_mapping  : couleurs → URFDLB
#        - validate_cube_string : validation basique
#        - opposite_edges / edge_pairs_multiset : diagnostics avancés
#     4) Conversion finale :
#        - convert_to_kociemba : FacesDict → chaîne 54
#     5) Orchestration :
#        - production_mode : Vision + Encodage + Sauvegarde
#        - process_rubiks_to_singmaster : API principale
#
#  Fonctions utilitaires :
#     - save_singmaster_file : sauvegarde txt/json
#     - _normalize_cube / _split_full_urfdlb : formats intermédiaires
#
#  Fonctions debug & test :
#     - quick_pipeline_test_corrected : test pipeline complet + solveur
#     - debug_color_mapping : diagnostic mapping couleur → lettre
#     - debug_vision_step1  : vérification vision (54 stickers, 6×9)
#     - debug_rotation_step2: vérification rotations
#     - print_face_grids    : affichage grilles 3×3
#     - full_debug_pipeline : vision + rotation + comparaison cube réel
#     - debug_compare_with_physical_cube : guide de validation manuelle
#
#  Entrées :
#     - FacesDict issu de process_images_cube.detect_colors_for_faces
#     - Calibration ROI (rubiks_calibration.json)
#     - Calibration couleurs (rubiks_color_calibration.json)
#
#  Sorties :
#     - Chaîne Singmaster 54 caractères (URFDLB)
#     - Fichiers txt/json avec métadonnées
#
# ============================================================================
# ============================================================================
#  Pipeline visuel (schéma simplifié)
#
#         Images (6 faces, F/R/B/L/U/D)
#                       │
#                       ▼
#        detect_colors_for_faces (vision)
#              → FacesDict (couleurs 3×3)
#                       │
#                       ▼
#      apply_robot_orientation_corrections
#        (rotation selon mode robot/phone)
#                       │
#                       ▼
#          reorient_cube_for_kociemba
#       (réordonne les faces pour Kociemba)
#                       │
#                       ▼
#           encode_with_mapping
#      (mapping couleur → URFDLB, 54 chars)
#                       │
#                       ▼
#           validate_cube_string
#       + opposite_edges / edge_pairs_multiset
#         (diagnostic de cohérence)
#                       │
#                       ▼
#         convert_to_kociemba (final)
#          → Chaîne Singmaster 54
#                       │
#                       ▼
#       save_singmaster_file (txt/json)
# ============================================================================

import os, json, datetime as dt
from typing import Dict, Tuple, List, Optional, Any
from collections import Counter
from calibration_rubiks import load_calibration
#from calibration_colors import load_color_calibration
from process_images_cube import detect_colors_for_faces
from types_shared import FaceResult, FacesDict

from solver_wrapper import solve_cube

def apply_robot_orientation_corrections(robot_results: FacesDict, mode: str = "robot_cam") -> FacesDict:
    """Applique les rotations selon le profil robot"""
    tables = {
        "robot_raw": {"F": 0, "R": 0, "B": 0,   "L": 0,   "U": 0, "D": 0},
        #"robot_cam": {"F": 0, "R": 0, "B": 180, "L": 180, "U": 0, "D": 0},
        "robot_cam": {"F":180,"R":180,"B":0,"L":0,"U":180,"D":180},
        "phone_demo":{"F": 0, "R": 90,"B": 180, "L": 270, "U": 0, "D": 0},
    }

    rotations = tables.get(mode, tables["robot_raw"])

    out: FacesDict = {}
    for face_name, fr in robot_results.items():
        rot = rotations.get(face_name, 0) % 360
        
        will_rotate = rot != 0 and len(fr.colors) == 9 and len(fr.cells) == 9
        colors = rotate_face_grid(fr.colors, rot) if will_rotate else fr.colors
        cells = rotate_cells_grid(fr.cells, rot) if will_rotate else fr.cells

        colors = colors[:] if colors is not None else colors
        cells = cells[:] if cells is not None else cells

        out[face_name] = FaceResult(
            colors=colors,
            cells=cells,
            warped=fr.warped,
            roi=fr.roi
        )
    return out


def rotate_face_grid(face_colors, rotation):
    """Tourne une liste de 9 éléments (row-major) de 0/90/180/270° (horaire)"""
    if not face_colors or len(face_colors) != 9:
        return face_colors

    rot = rotation % 360
    if rot == 0:
        idx = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    elif rot == 90:
        idx = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    elif rot == 180:
        idx = [8, 7, 6, 5, 4, 3, 2, 1, 0]
    elif rot == 270:
        idx = [2, 5, 8, 1, 4, 7, 0, 3, 6]
    else:
        raise ValueError(f"Rotation invalide: {rotation}")

    return [face_colors[i] for i in idx]


def rotate_cells_grid(cells, rotation):
    """Tourne la liste de 9 cells avec (i,j) recalculés"""
    if not cells or len(cells) != 9:
        return cells

    rot = rotation % 360
    if rot == 0:
        idx = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    elif rot == 90:
        idx = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    elif rot == 180:
        idx = [8, 7, 6, 5, 4, 3, 2, 1, 0]
    elif rot == 270:
        idx = [2, 5, 8, 1, 4, 7, 0, 3, 6]
    else:
        raise ValueError(f"Rotation invalide: {rotation}")

    rotated = []
    for new_pos, old_pos in enumerate(idx):
        _, roi = cells[old_pos]
        i, j = divmod(new_pos, 3)
        rotated.append(((i, j), roi))
    return rotated


def reorient_cube_for_kociemba_legacy(corrected_results: FacesDict) -> FacesDict:
    """
    Réorientation pour Kociemba - Rotation 270° (LA SEULE QUI FONCTIONNE)
    """
    reorientation_map = {
        'F': 'R', 'R': 'B', 'B': 'L', 'L': 'F', 'U': 'U', 'D': 'D'
    }
    
    reoriented = {}
    for your_face, standard_face in reorientation_map.items():
        if your_face in corrected_results:
            reoriented[standard_face] = corrected_results[your_face]
    
    return reoriented

def reorient_cube_for_kociemba(corrected: FacesDict, yaw: int = 0) -> FacesDict:
    """
    yaw = rotation globale autour de l’axe vertical (U/D), en degrés.
    0 / 90 / 180 / 270.
    """
    yaw = yaw % 360
    maps = {
        0:   {"F":"F","R":"R","B":"B","L":"L","U":"U","D":"D"},
        90:  {"F":"R","R":"B","B":"L","L":"F","U":"U","D":"D"},
        180: {"F":"B","R":"L","B":"F","L":"R","U":"U","D":"D"},
        270: {"F":"L","R":"F","B":"R","L":"B","U":"U","D":"D"},
    }
    m = maps[yaw]

    out: FacesDict = {}
    for src_face, dst_face in m.items():
        if src_face in corrected:
            out[dst_face] = corrected[src_face]
    return out


def create_color_mapping(face_results: FacesDict) -> Dict[str, str]:
    """Crée le mapping couleur→lettre dynamique basé sur les centres"""
    color_map = {}
    for face_name, face_result in face_results.items():
        if face_result.colors and len(face_result.colors) >= 5:
            center_color = face_result.colors[4].lower().strip()
            color_map[center_color] = face_name
    return color_map


def encode_with_mapping(face_results: FacesDict, debug: bool = False) -> Tuple[Dict[str, str], str]:
    """Encode les faces en utilisant le mapping couleur→lettre"""
    color_to_letter = create_color_mapping(face_results)
    
    if debug:
        print("\n=== ENCODAGE FACE PAR FACE ===")
    
    cube = {}
    for target_letter in "URFDLB":
        if target_letter not in face_results:
            raise ValueError(f"Face {target_letter} manquante")
            
        face_colors = face_results[target_letter].colors
        letters = []
        
        if debug:
            print(f"\nFace {target_letter}: {face_colors}")
        
        for i, color in enumerate(face_colors):
            mapped = color_to_letter.get(color.lower().strip(), '?')
            letters.append(mapped)
            if debug:
                print(f"  {i}: {color} → {mapped}")
        
        face_string = ''.join(letters)
        cube[target_letter] = face_string
        
        if debug:
            print(f"  Résultat: {face_string}")
    
    full = ''.join(cube[L] for L in "URFDLB")
    
    if debug:
        print(f"\nChaîne complète: {full}")
        print(f"Centres: {[full[i*9+4] for i in range(6)]}")
    
    return cube, full


def validate_cube_string(full: str) -> bool:
    """Validation basique de la chaîne de cube"""
    if len(full) != 54:
        return False
    
    centers = [full[i*9 + 4] for i in range(6)]
    if centers != list("URFDLB"):
        return False
    
    for letter in "URFDLB":
        if full.count(letter) != 9:
            return False
    
    return True


# Fonctions de validation avancée pour diagnostic
EDGE_SLOTS: List[Tuple[str, Tuple[str, int], Tuple[str, int]]] = [
    ("UF", ("U", 7), ("F", 1)), ("UR", ("U", 5), ("R", 1)),
    ("UB", ("U", 1), ("B", 1)), ("UL", ("U", 3), ("L", 1)),
    ("DF", ("D", 1), ("F", 7)), ("DR", ("D", 5), ("R", 7)),
    ("DB", ("D", 7), ("B", 7)), ("DL", ("D", 3), ("L", 7)),
    ("FR", ("F", 5), ("R", 3)), ("RB", ("R", 5), ("B", 3)),
    ("BL", ("B", 5), ("L", 3)), ("LF", ("L", 5), ("F", 3)),
]

ALLOWED_EDGE_PAIRS = {
    tuple(sorted(p)) for p in [
        ("U", "F"), ("U", "R"), ("U", "B"), ("U", "L"),
        ("D", "F"), ("D", "R"), ("D", "B"), ("D", "L"),
        ("F", "R"), ("R", "B"), ("B", "L"), ("L", "F"),
    ]
}


def opposite_edges(s: str):
    """Détecte les arêtes opposées impossibles"""
    if len(s) != 54:
        raise ValueError(f"Cube string length must be 54, got {len(s)}")

    opp = {'U': 'D', 'D': 'U', 'F': 'B', 'B': 'F', 'R': 'L', 'L': 'R'}
    base = {'U': 0, 'R': 9, 'F': 18, 'D': 27, 'L': 36, 'B': 45}
    
    def v(face: str, k: int) -> str:
        return s[base[face] + k]

    bad = []
    for name, (fa, ia), (fb, ib) in EDGE_SLOTS:
        a, b = v(fa, ia), v(fb, ib)
        if opp.get(a) == b:
            bad.append((name, a, b))
    return bad


def edge_pairs_multiset(s: str):
    """Analyse les arêtes pour détecter les duplicatas et manquants"""
    if len(s) != 54:
        raise ValueError(f"Cube string length must be 54, got {len(s)}")

    base = {'U': 0, 'R': 9, 'F': 18, 'D': 27, 'L': 36, 'B': 45}
    
    def v(face: str, k: int) -> str:
        return s[base[face] + k]

    pairs = [tuple(sorted((v(a, ia), v(b, ib)))) for _, (a, ia), (b, ib) in EDGE_SLOTS]
    cnt = Counter(pairs)

    missing = [p for p in sorted(ALLOWED_EDGE_PAIRS) if cnt[p] == 0]
    duplicates = [(p, cnt[p]) for p in sorted(cnt) if cnt[p] > 1]

    return pairs, missing, duplicates


def convert_to_kociemba_legacy(color_results: FacesDict,
                       mode: str = "robot_raw",
                       strategy: str = "center_hsv",
                       debug: str = "text") -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Conversion FacesDict → string Kociemba URFDLB (54)
    """
    try:
        # 1. Rotations robot
        corrected = apply_robot_orientation_corrections(color_results, mode=mode)

        # 2. Réorientation pour Kociemba
        reoriented = reorient_cube_for_kociemba(corrected)

        # 3. Encodage
        _cube_dict, full = encode_with_mapping(reoriented, debug=(debug in ["text", "both"]))

        # 4. Validation basique
        if not validate_cube_string(full):
            return False, None, "Validation basique échouée"

        # 5. Diagnostic avancé
        if debug in ["text", "both"]:
            centers = [full[i*9+4] for i in range(6)]
            bad_opp = opposite_edges(full)
            _, missing, dups = edge_pairs_multiset(full)
            
            print("Centers:", centers)
            if bad_opp:
                print("Opposite edges:", bad_opp)
            if missing:
                print("Missing edges:", missing)
            if dups:
                print("Duplicate edges:", dups)

        return True, full, None

    except Exception as e:
        return False, None, f"Erreur encodage: {e}"

def convert_to_kociemba(color_results, mode="robot_cam", strategy=None, debug=False, yaw=0):
    return _convert_to_kociemba_new(color_results, rot_mode=mode, yaw=yaw, debug=debug)

def _convert_to_kociemba_new(color_results: FacesDict,
                        rot_mode: str = "robot_cam",
                        yaw: int = 0,
                        debug: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
    try:
        corrected  = apply_robot_orientation_corrections(color_results, mode=rot_mode)
        reoriented = reorient_cube_for_kociemba(corrected, yaw=yaw)
        _cube_dict, full = encode_with_mapping(reoriented, debug=debug)

        if not validate_cube_string(full):
            return False, None, "Validation basique échouée"

        return True, full, None
    except Exception as e:
        return False, None, f"Erreur encodage: {e}"


def production_mode(
    roi_data: Optional[Dict[str, Tuple[int, int, int, int]]],
    color_calibration: Optional[Dict[str, Any]] = None,
    image_folder: str = "tmp",
    mode: str = "robot_cam",
    strategy: str = "center_hsv",
    debug: str = "text",
    save: bool = True,
    return_faces: bool = False,
):
    """
    Orchestration principale: Phase vision → Phase encodage Kociemba
    """
    if roi_data is None:
        roi_data = load_calibration()
        if roi_data is None:
            return {"success": False, "singmaster": None, "error": "Calibration ROI introuvable"}

    #if color_calibration is None:
    #    color_calibration = load_color_calibration()
    color_calibration = None

    # Phase vision
    color_results: FacesDict = detect_colors_for_faces(
        image_folder=image_folder,
        roi_data=roi_data,
        color_calibration=color_calibration,
        debug=debug,
    )
    
    if len(color_results) < 6:
        missing = [f for f in ["F", "R", "B", "L", "U", "D"] if f not in color_results]
        return {
            "success": False,
            "singmaster": None,
            "error": f"Moins de 6 faces détectées. Manquantes: {', '.join(missing)}",
            **({"faces": color_results} if return_faces else {}),
        }

    # Phase encodage
    ok, cubestring, err = convert_to_kociemba(
        color_results,
        mode=mode,
        strategy=strategy,
        debug=debug,
    )
    
    if not ok or not cubestring:
        return {
            "success": False,
            "singmaster": None,
            "error": err or "Erreur encodage inconnue",
            **({"faces": color_results} if return_faces else {}),
        }

    # Sauvegarde optionnelle
    if save:
        save_singmaster_file({'full': cubestring})

    res = {"success": True, "singmaster": cubestring, "error": None}
    if return_faces:
        res["faces"] = color_results
    return res


def process_rubiks_to_singmaster(
    image_folder: str = "tmp",
    calibration_file: Optional[str] = None,
    debug: str = "text",
    mode: str = "robot_cam",
    strategy: str = "center_hsv",
    save: bool = True,
    return_faces: bool = False,
) -> Dict[str, Any]:
    """
    API principale: dossier d'images → code Singmaster (URFDLB, 54)
    """
    roi_data = load_calibration(calibration_file)
    if roi_data is None:
        return {"success": False, "singmaster": None, "error": "Calibration ROI non trouvée"}

    #color_calibration = load_color_calibration()
    color_calibration = None

    required = ["F.jpg", "R.jpg", "B.jpg", "L.jpg", "U.jpg", "D.jpg"]
    missing = [fn for fn in required if not os.path.exists(os.path.join(image_folder, fn))]
    if missing:
        return {
            "success": False,
            "singmaster": None,
            "error": f"Fichiers manquants: {', '.join(missing)}"
        }

    try:
        result = production_mode(
            roi_data=roi_data,
            color_calibration=color_calibration,
            image_folder=image_folder,
            mode=mode,
            strategy=strategy,
            debug=debug,
            save=save,
            return_faces=return_faces,
        )
        return result
    except Exception as e:
        return {"success": False, "singmaster": None, "error": f"Erreur traitement: {e}"}


# Fonctions utilitaires pour la sauvegarde
def _normalize_cube(obj):
    """Normalise différents formats de cube en (dict, string)"""
    if isinstance(obj, str):
        full = obj
        cube = _split_full_urfdlb(full)
        cube['full'] = full
        return cube, full
    if isinstance(obj, dict):
        if 'full' in obj and isinstance(obj['full'], str) and len(obj['full']) == 54:
            full = obj['full']
            cube = _split_full_urfdlb(full)
            cube['full'] = full
            return cube, full
        need = all(k in obj and isinstance(obj[k], str) and len(obj[k]) == 9 for k in "URFDLB")
        if not need:
            raise ValueError("Objet invalide: fournir str 54, ou dict avec 'full' 54, ou U,R,F,D,L,B")
        full = "".join(obj[k] for k in "URFDLB")
        cube = {k: obj[k] for k in "URFDLB"}
        cube['full'] = full
        return cube, full
    raise TypeError("Type non supporté pour l'encodage.")


def _split_full_urfdlb(full: str):
    """Découpe une chaîne 54 en faces URFDLB"""
    if not isinstance(full, str) or len(full) != 54:
        raise ValueError(f"Len != 54 (got {len(full) if isinstance(full, str) else 'NA'})")
    return {
        'U': full[0:9], 'R': full[9:18], 'F': full[18:27],
        'D': full[27:36], 'L': full[36:45], 'B': full[45:54],
    }


def save_singmaster_file(singmaster_cube,
                        filename: str = "rubiks_singmaster.txt",
                        pretty: bool = False,
                        also_json: bool = False,
                        json_filename: Optional[str] = None) -> bool:
    """Sauvegarde l'encodage dans un fichier"""
    try:
        cube, full = _normalize_cube(singmaster_cube)

        if not pretty:
            content = full + "\n"
        else:
            def rows3(s): return [s[0:3], s[3:6], s[6:9]]
            parts = [full, ""]
            for k in "URFDLB":
                r1, r2, r3 = rows3(cube[k])
                parts.append(f"Face {k}: {cube[k]}")
                parts.append(f"  {r1}")
                parts.append(f"  {r2}")
                parts.append(f"  {r3}")
                parts.append("")
            content = "\n".join(parts) + "\n"

        folder = os.path.dirname(filename)
        if folder:
            os.makedirs(folder, exist_ok=True)

        tmp = filename + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, filename)
        print(f"Encodage sauvegardé: {filename}")

        if also_json:
            jf = json_filename or (os.path.splitext(filename)[0] + ".json")
            meta = {
                "created_at": dt.datetime.now().isoformat(timespec="seconds"),
                "length": 54,
                "centers": [full[i*9+4] for i in range(6)],
                "counts": {k: full.count(k) for k in "URFDLB"},
                "faces": {k: cube[k] for k in "URFDLB"},
                "full": full,
            }
            with open(jf, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            print(f"Métadonnées sauvegardées: {jf}")

        return True
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")
        return False


# Fonctions pour tests et diagnostics
def quick_pipeline_test_corrected(folder="tmp", debug="text", mode="robot_cam"):
    """Test rapide du pipeline complet"""
    roi = load_calibration()
    #color_calib = load_color_calibration()
    color_calib = None

    faces = detect_colors_for_faces(folder, roi, color_calib, debug=debug)
    if len(faces) < 6:
        print("Vision incomplète")
        return False

    ok, full, err = convert_to_kociemba(faces, mode=mode, debug=debug)
    if not ok:
        print(f"Encodage échoué: {err}")
        return False

    print(f"SUCCESS: {full}")
    
    try:
        solution = solve_cube(full)
        print(f"SOLVEUR OK: {solution}")
        save_singmaster_file({'full': full})
        return True
    except Exception as e:
        print(f"SOLVEUR ÉCHOUÉ: {e}")
        return False


def debug_color_mapping(folder="tmp"):
    """Diagnostique le mapping couleur détectée → lettre"""
    roi = load_calibration()
    #color_calib = load_color_calibration()
    color_calib = None
    faces = detect_colors_for_faces(folder, roi, color_calib, debug="none")
    corrected = apply_robot_orientation_corrections(faces, mode="robot_cam")
    
    print("=== DIAGNOSTIC MAPPING COULEUR ===")
    color_mapping = create_color_mapping(corrected)
    
    for face_name, face_result in corrected.items():
        print(f"\nFace {face_name}:")
        print(f"  Couleurs détectées: {face_result.colors}")
        print(f"  Centre: {face_result.colors[4]} → {color_mapping.get(face_result.colors[4], '?')}")
        
        mapped = []
        for color in face_result.colors:
            mapped.append(color_mapping.get(color.lower().strip(), '?'))
        print(f"  Mapping: {mapped}")
    
    return color_mapping

################### DEBUG ###########################
def debug_vision_step1(folder="tmp"):
    """
    ÉTAPE 1: Vérifier que la vision des couleurs est correcte
    """
    print("=== DEBUG ÉTAPE 1: VISION DES COULEURS ===")
    
    roi = load_calibration()
    #color_calib = load_color_calibration()
    color_calib = None
    
    # Vision brute sans debug graphique
    faces = detect_colors_for_faces(folder, roi, color_calib, debug="none")
    
    print(f"\nFaces détectées: {len(faces)}/6")
    
    # Analyser chaque face en détail
    for face_name in ["F", "R", "B", "L", "U", "D"]:
        if face_name not in faces:
            print(f"\n❌ Face {face_name}: MANQUANTE")
            continue
            
        face_result = faces[face_name]
        colors = face_result.colors
        
        print(f"\n--- Face {face_name} ---")
        print(f"Grille 3x3:")
        for i in range(3):
            row = colors[i*3:(i+1)*3]
            print(f"  {row}")
        print(f"Centre: {colors[4]}")
        
        # Vérifications de base
        if len(colors) != 9:
            print(f"❌ Erreur: {len(colors)} couleurs au lieu de 9")
        else:
            print(f"✅ 9 couleurs détectées")
            
        # Comptage par couleur sur cette face
        color_count = Counter(colors)
        print(f"Répartition: {dict(color_count)}")
    
    # Comptage global
    all_colors = [c for fr in faces.values() for c in fr.colors]
    global_count = Counter(all_colors)
    print(f"\n=== COMPTAGE GLOBAL ===")
    print(f"Total stickers: {len(all_colors)}")
    for color, count in sorted(global_count.items()):
        status = "✅" if count == 9 else "❌"
        print(f"  {color}: {count} {status}")
    
    # Validation
    is_valid = (len(all_colors) == 54 and 
                all(count == 9 for count in global_count.values()) and
                len(global_count) == 6)
    
    if is_valid:
        print("\n✅ VISION VALIDE: 6 couleurs × 9 stickers chacune")
    else:
        print("\n❌ VISION INVALIDE")
        
    return faces, is_valid

def debug_rotation_step2(faces):
    """
    ÉTAPE 2: Vérifier que les rotations préservent la cohérence
    """
    print("\n=== DEBUG ÉTAPE 2: ROTATIONS ===")
    
    print("AVANT rotations:")
    print_face_grids(faces, "AVANT")
    
    # Appliquer rotations
    #corrected = apply_robot_orientation_corrections(faces, mode="robot_raw")
    corrected = apply_robot_orientation_corrections(faces, mode="robot_cam")
    
    print("\nAPRÈS rotations:")
    print_face_grids(corrected, "APRÈS")
    
    # Vérifications post-rotation
    print("\n=== VÉRIFICATIONS POST-ROTATION ===")
    
    # 1. Centres préservés
    print("Centres préservés:")
    for face_name in ["F", "R", "B", "L", "U", "D"]:
        before = faces[face_name].colors[4] if face_name in faces else "?"
        after = corrected[face_name].colors[4] if face_name in corrected else "?"
        status = "✅" if before == after else "❌"
        print(f"  {face_name}: {before} → {after} {status}")
    
    # 2. Comptage global préservé
    all_before = [c for fr in faces.values() for c in fr.colors]
    all_after = [c for fr in corrected.values() for c in fr.colors]
    
    count_before = Counter(all_before)
    count_after = Counter(all_after)
    
    print("\nComptage préservé:")
    for color in sorted(count_before.keys()):
        before_c = count_before[color]
        after_c = count_after[color]
        status = "✅" if before_c == after_c else "❌"
        print(f"  {color}: {before_c} → {after_c} {status}")
    
    # 3. Validation finale
    rotation_valid = (count_before == count_after and
                     all(faces[f].colors[4] == corrected[f].colors[4] 
                         for f in faces.keys()))
    
    if rotation_valid:
        print("\n✅ ROTATIONS VALIDES: Centres et comptages préservés")
    else:
        print("\n❌ ROTATIONS INVALIDES")
        
    return corrected, rotation_valid

def print_face_grids(faces_dict, label):
    """Affiche les grilles 3x3 de toutes les faces"""
    print(f"\n{label} - Grilles 3x3:")
    for face_name in ["F", "R", "B", "L", "U", "D"]:
        if face_name not in faces_dict:
            continue
        colors = faces_dict[face_name].colors
        print(f"\nFace {face_name}:")
        for i in range(3):
            row = colors[i*3:(i+1)*3]
            print(f"  {' '.join(f'{c:>6}' for c in row)}")

def full_debug_pipeline():
    """
    Pipeline complet de debug vision + rotations
    """
    print("🔍 DIAGNOSTIC COMPLET VISION + ROTATIONS")
    print("=" * 50)
    
    # Étape 1: Vision
    faces, vision_ok = debug_vision_step1()
    if not vision_ok:
        print("\n❌ ARRÊT: Vision défaillante")
        return False
    
    # Étape 2: Rotations
    _corrected, rotation_ok = debug_rotation_step2(faces)
    if not rotation_ok:
        print("\n❌ ARRÊT: Rotations défaillantes")
        return False
    
    # Étape 3: Guide de vérification
    debug_compare_with_physical_cube()
    
    print(f"\n✅ DIAGNOSTIC TERMINÉ")
    print(f"Vision: {'✅ OK' if vision_ok else '❌ KO'}")
    print(f"Rotations: {'✅ OK' if rotation_ok else '❌ KO'}")
    
    return vision_ok and rotation_ok

def debug_compare_with_physical_cube():
    """
    ÉTAPE 3: Guide pour comparer avec le cube physique
    """
    print("\n=== DEBUG ÉTAPE 3: COMPARAISON CUBE PHYSIQUE ===")
    print("\n📋 VÉRIFICATION MANUELLE À FAIRE:")
    print("\n1. Prenez votre cube physique en main")
    print("2. Identifiez la face F (front) - celle avec le centre YELLOW")
    print("3. Placez cette face face à vous")
    print("4. Vérifiez que:")
    print("   - La face à droite (R) a un centre ORANGE")
    print("   - La face derrière (B) a un centre WHITE") 
    print("   - La face à gauche (L) a un centre RED")
    print("   - La face du haut (U) a un centre BLUE")
    print("   - La face du bas (D) a un centre GREEN")
    
    print("\n5. Pour chaque face, comparez la grille 3x3 avec l'affichage ci-dessus")
    print("6. Si ça ne correspond pas, le problème est dans:")
    print("   - Soit la vision (étape 1)")
    print("   - Soit les rotations (étape 2)")
    print("   - Soit l'ordre de capture des photos du robot")
