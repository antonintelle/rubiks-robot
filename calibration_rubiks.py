
# ============================================================================
#  calibration_rubiks.py
#  ---------------------
#  Objectif :
#     Fichier **pont enrichi** pour la calibration du projet Rubik’s Cube.
#     - Interface unifiée pour la calibration ROI et Couleurs
#     - Fournit des statistiques et un affichage complet de la calibration actuelle
#     - Corrige la clé 'faces_count' (anciennement 'faces count')
#
#  Fonctions principales :
#     - get_calibration_stats()     → résumé des calibrations
#     - calibration_mode()          → menu interactif global
#
#  Sous-modules utilisés :
#     * calibration_roi.py      → calibration ROI (zones des faces)
#     * calibration_colors.py   → calibration des couleurs
# ============================================================================

from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np
import json
import os

# --- ROI (pont) ---
from calibration_roi import (
    load_calibration,
    calibration_menu,  # nouveau menu interactif ROI
)

# --- Couleurs (pont) ---
from calibration_colors import (
    load_color_calibration,
    calibrate_colors_interactive,
)

__all__ = [
    "load_calibration",
    "save_calibration",
    "validate_roi_dict",
    "load_color_calibration",
    "save_color_calibration",
    "calibrate_colors_interactive",
    "get_calibration_stats",
    "calibration_mode",
]

# ---------------------------------------------------------------------------
#  Statistiques globales (ROI + Couleurs)
# ---------------------------------------------------------------------------

def get_calibration_stats() -> Optional[Dict[str, Any]]:
    """Retourne un petit résumé sur l'état de calibration ROI/Couleurs."""
    roi = load_calibration()
    colors = load_color_calibration()

    if roi is None and colors is None:
        return None

    stats: Dict[str, Any] = {}

    # ROI
    if roi is not None:
        faces = list(roi.keys())
        widths, heights = [], []
        for f, (x1, y1, x2, y2) in roi.items():
            widths.append(x2 - x1)
            heights.append(y2 - y1)
        stats["roi"] = {
            "faces": faces,
            "faces_count": len(faces),  # ✅ clé corrigée
            "missing_faces": [f for f in ["F", "R", "B", "L", "U", "D"] if f not in faces],
            "avg_width": float(np.mean(widths)) if widths else 0.0,
            "avg_height": float(np.mean(heights)) if heights else 0.0,
        }
    else:
        stats["roi"] = None

    # COULEURS
    if colors is not None:
        stats["colors"] = {
            "count": len(colors),
            "labels": list(colors.keys()),
        }
    else:
        stats["colors"] = None

    return stats

# ---------------------------------------------------------------------------
#  Affichage du contenu des calibrations
# ---------------------------------------------------------------------------

def show_full_calibration():
    """Affiche le contenu brut des calibrations (ROI + Couleurs)."""
    print("\n=== CONTENU DES CALIBRATIONS ===")

    # Fichier ROI
    roi_file = "rubiks_calibration.json"
    if os.path.exists(roi_file):
        print(f"\n📄 {roi_file} :")
        try:
            with open(roi_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Erreur lecture {roi_file}: {e}")
    else:
        print("\n❌ Aucune calibration ROI trouvée.")

    # Fichier Couleurs
    color_file = "rubiks_color_calibration.json"
    if os.path.exists(color_file):
        print(f"\n📄 {color_file} :")
        try:
            with open(color_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Erreur lecture {color_file}: {e}")
    else:
        print("\n❌ Aucune calibration Couleur trouvée.")

# ---------------------------------------------------------------------------
#  Menu global de calibration
# ---------------------------------------------------------------------------

def calibration_mode():
    """Menu global pour lancer une calibration ROI ou Couleurs, ou afficher les stats."""
    while True:
        print("\n=== MODE CALIBRATION ===")
        print("1. Calibration ROI (zones des faces)")
        print("2. Calibration couleurs (RGB/HSV)")
        print("3. Afficher statistiques")
        print("4. Afficher le contenu complet des calibrations")
        print("5. Quitter")
        choice = input("Choisissez une option (1/2/3/4/5) : ").strip()

        if choice == "1":
            try:
                calibration_menu()
            except Exception as e:
                print(f"Erreur lors du lancement du menu ROI : {e}")
        elif choice == "2":
            try:
                calibrate_colors_interactive()
            except Exception as e:
                print(f"Erreur calibration couleurs : {e}")
        elif choice == "3":
            s = get_calibration_stats()
            if s is None:
                print("Aucune calibration disponible.")
            else:
                print("\n=== ÉTAT DES CALIBRATIONS ===")
                if s["roi"]:
                    roi_stats = s["roi"]
                    print(f"Calibration ROI : {roi_stats['faces_count']}/6 faces")
                    print(f"Faces calibrées : {', '.join(roi_stats['faces'])}")
                    print(f"Taille moyenne : {roi_stats['avg_width']:.0f}×{roi_stats['avg_height']:.0f} px")
                if s["colors"]:
                    col = s["colors"]
                    print(f"Calibration couleurs : {col['count']} couleurs → {', '.join(col['labels'])}")
        elif choice == "4":
            show_full_calibration()
        else:
            print("Fin du mode calibration.")
            break
