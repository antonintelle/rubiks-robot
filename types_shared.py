# ============================================================================
#  types_shared.py
#  ----------------
#  Objectif :
#     Définir les types et structures de données partagés entre
#     les différents modules du projet Rubik’s Cube (vision, encodage,
#     solveur, robot).
#
#  Définitions principales :
#     - Cell :
#         Tuple ((i,j), ROI) représentant une cellule d’une face.
#         * (i,j) → coordonnées dans la grille 3×3
#         * ROI   → sous-image (np.ndarray BGR) de la cellule
#
#     - ROI :
#         Tuple (x1, y1, x2, y2) représentant une région d’intérêt
#         rectangulaire dans l’image source.
#
#     - FaceResult (dataclass) :
#         Contient toutes les informations pour une face du cube :
#           * colors : liste [9] de labels de couleurs ('red','blue',...)
#           * cells  : liste [9] de Cell alignées (row-major, 3×3)
#           * warped : image normalisée 300×300 (np.ndarray) ou None
#           * roi    : ROI utilisée pour extraire la face
#
#     - FacesDict :
#         Dictionnaire {face_name → FaceResult}
#         face_name ∈ {'F','R','B','L','U','D'}
#
#  Utilisation :
#     - Centralise la représentation standardisée d’un cube
#     - Sert de lien entre :
#         * process_images_cube.py (vision)
#         * processing_rubiks.py   (encodage Singmaster)
#         * robot_solver.py        (pipeline robot)
#
#  Auteur : [Ton Nom]
#  Version : structures partagées
#  Date : [AAAA-MM-JJ]
# ============================================================================
# ============================================================================
#  Structure des types partagés
#
#   FacesDict (dict)
#   ├── "F" → FaceResult
#   ├── "R" → FaceResult
#   ├── "B" → FaceResult
#   ├── "L" → FaceResult
#   ├── "U" → FaceResult
#   └── "D" → FaceResult
#
#   FaceResult (dataclass)
#   ├── colors : [ "red", "blue", ... ]   # 9 éléments
#   ├── cells  : [ Cell × 9 ]             # 3×3 en row-major
#   ├── warped : np.ndarray (300×300) ou None
#   └── roi    : (x1, y1, x2, y2)
#
#   Cell (tuple)
#   ├── (i, j) : indices dans la grille 3×3
#   └── ROI    : sous-image np.ndarray (BGR)
#
#   ROI (tuple)
#   └── (x1, y1, x2, y2) : rectangle dans l’image source
# ============================================================================

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

Cell = Tuple[Tuple[int, int], Any]  # ((i,j), ROI BGR np.ndarray)
ROI  = Tuple[int, int, int, int]    # (x1,y1,x2,y2)

@dataclass
class FaceResult:
    colors: List[str]               # 9 labels de couleur ('red','blue',...)
    cells:  List[Cell]              # 9 cellules alignées (row-major)
    warped: Optional[Any]           # image 300x300 (np.ndarray) ou None
    roi:    ROI                     # ROI utilisée pour extraire la face

FacesDict = Dict[str, FaceResult]   # clés 'F','R','B','L','U','D'
