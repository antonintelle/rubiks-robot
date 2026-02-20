#!/usr/bin/env python3
<<<<<<< HEAD
# ============================================================================
#  check_dependencies.py
#  ---------------------
#  Objectif :
#     Script de **pré-vérification** avant lancement de l’interface GUI du robot
#     (Tkinter). Il contrôle :
#       - la présence des modules Python requis (et optionnels),
#       - la présence des fichiers clés du projet,
#       - le bon fonctionnement de Tkinter,
#       - l’existence des dossiers attendus,
#       - la présence (optionnelle) des fichiers de calibration.
#
#  Entrée principale :
#     - Exécution directe (__main__) :
#         python3 check_dependencies.py
#         -> Affiche un rapport en console + code de sortie :
#              0 : tout OK
#              1 : dépendances manquantes (bloquantes)
#
#  Étapes principales (main) :
#     1) Modules Python essentiels (bloquants si absents) :
#        - numpy, matplotlib, cv2 (OpenCV), PIL, kociemba, colorama, tkinter
#
#     2) Modules optionnels (non bloquants) :
#        - picamera2, pytest, RubikTwoPhase, ultralytics (YOLO)
#
#     3) Fichiers projet attendus (bloquants si manquants) :
#        - robot_moves_cubotino.py, Cubotino_T_moves.py, robot_solver.py,
#          calibration_rubiks.py, process_images_cube.py, processing_rubiks.py,
#          solver_wrapper.py, calibration_roi.py
#
#     4) Test Tkinter :
#        - Crée une fenêtre Tk, withdraw(), destroy() pour valider l’environnement GUI.
#
#     5) Dossiers nécessaires :
#        - tmp, logs (avertissement si absents, création possible par ailleurs)
#
#     6) Fichiers de calibration (optionnels) :
#        - rubiks_calibration.json (ROI), rubiks_color_calibration.json (couleurs)
#
#  Fonctions utilitaires :
#     - check_module(name, import_name=None, optional=False)
#         Vérifie import, affiche un statut coloré (✅/⚠️/❌) et retourne True/False.
#
#     - check_file_exists(filepath, description)
#         Vérifie existence d’un fichier et affiche OK/KO.
#
#  Sorties / UX :
#     - Affichage console structuré par sections avec codes couleurs ANSI.
#     - En cas d’échec : propose des commandes d’installation (script + apt + pip).
#     - En cas de succès : indique la commande pour lancer le GUI :
#         python3 tkinter_gui_robot.py
# ============================================================================

=======
# =====================================================================
# check_dependencies.py
# Script de vérification des dépendances avant lancement du GUI robot
# =====================================================================
>>>>>>> screen-gui

import sys
import subprocess

def check_module(name, import_name=None, optional=False):
    """
    Vérifie qu'un module peut être importé.
    
    Args:
        name: Nom d'affichage du module
        import_name: Nom d'import (si différent)
        optional: Si True, ne provoque pas d'échec
    
    Returns:
        bool: True si le module est disponible
    """
    if import_name is None:
        import_name = name
    
    try:
        __import__(import_name)
        status = "✅"
        color = "\033[92m"  # Vert
    except ImportError as e:
        if optional:
            status = "⚠️ "
            color = "\033[93m"  # Jaune
        else:
            status = "❌"
            color = "\033[91m"  # Rouge
    except Exception as e:
        status = "❌"
        color = "\033[91m"  # Rouge
    
    reset = "\033[0m"
    suffix = " (optionnel)" if optional else ""
    print(f"{color}{status} {name}{suffix}{reset}")
    
    if status == "❌" and not optional:
        return False
    return True

def check_file_exists(filepath, description):
    """Vérifie qu'un fichier existe"""
    import os
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MANQUANT: {filepath}")
        return False

def main():
    print("=" * 60)
    print("🔍 VÉRIFICATION DES DÉPENDANCES - GUI ROBOT")
    print("=" * 60)
    
    all_ok = True
    
    # ====================================================================
    # 1. Modules Python essentiels
    # ====================================================================
    print("\n📦 Modules Python essentiels:")
    
    required_modules = [
        ("NumPy", "numpy"),
        ("Matplotlib", "matplotlib"),
        ("OpenCV", "cv2"),
        ("Pillow (PIL)", "PIL"),
        ("Kociemba", "kociemba"),
<<<<<<< HEAD
=======
        ("Ultralytics (YOLO)", "ultralytics"),
>>>>>>> screen-gui
        ("Colorama", "colorama"),
        ("Tkinter", "tkinter"),
    ]
    
    for name, import_name in required_modules:
        if not check_module(name, import_name):
            all_ok = False
    
    # ====================================================================
    # 2. Modules optionnels
    # ====================================================================
    print("\n📦 Modules optionnels:")
    
    optional_modules = [
        ("Picamera2", "picamera2"),
        ("Pytest", "pytest"),
        ("RubikTwoPhase", "RubikTwoPhase"),
<<<<<<< HEAD
        ("Ultralytics (YOLO)", "ultralytics"),
=======
>>>>>>> screen-gui
    ]
    
    for name, import_name in optional_modules:
        check_module(name, import_name, optional=True)
    
    # ====================================================================
    # 3. Fichiers du projet
    # ====================================================================
    print("\n📁 Fichiers du projet:")
    
    project_files = [
<<<<<<< HEAD
        ("robot_moves_cubotino.py", "Module des mouvements robot"),
        ("Cubotino_T_moves.py", "Module des mouvements robot"),
        ("robot_solver.py", "Module solveur robot"),
=======
        ("robot_moves.py", "Module des mouvements robot"),
        ("robot_solver.py", "Module solveur robot"),
        ("tkinter_gui_robot.py", "Interface graphique robot"),
>>>>>>> screen-gui
        ("calibration_rubiks.py", "Module de calibration"),
        ("process_images_cube.py", "Module de traitement d'images"),
        ("processing_rubiks.py", "Module de processing"),
        ("solver_wrapper.py", "Wrapper du solveur"),
        ("calibration_roi.py", "Calibration ROI"),
    ]
    
    for filepath, description in project_files:
        if not check_file_exists(filepath, description):
            all_ok = False
    
    # ====================================================================
    # 4. Test Tkinter
    # ====================================================================
    print("\n🖼️  Test de Tkinter:")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        print("✅ Tkinter fonctionne correctement")
    except Exception as e:
        print(f"❌ Erreur Tkinter: {e}")
        all_ok = False
    
    # ====================================================================
    # 5. Dossiers nécessaires
    # ====================================================================
    print("\n📂 Dossiers nécessaires:")
    import os
    
    folders = ["tmp", "logs"]
    for folder in folders:
        if os.path.exists(folder):
            print(f"✅ Dossier '{folder}' existe")
        else:
            print(f"⚠️  Dossier '{folder}' manquant (sera créé automatiquement)")
    
    # ====================================================================
    # 6. Fichiers de calibration (optionnels)
    # ====================================================================
    print("\n⚙️  Fichiers de calibration (optionnels):")
    
    calib_files = [
        ("rubiks_calibration.json", "Calibration ROI"),
        ("rubiks_color_calibration.json", "Calibration couleurs"),
    ]
    
    for filepath, description in calib_files:
        check_file_exists(filepath, description)
    
    # ====================================================================
    # RÉSULTAT FINAL
    # ====================================================================
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ TOUTES LES DÉPENDANCES SONT SATISFAITES")
        print("=" * 60)
        print("\n🚀 Vous pouvez lancer l'interface:")
        print("   python3 tkinter_gui_robot.py")
        print()
        return 0
    else:
        print("❌ CERTAINES DÉPENDANCES SONT MANQUANTES")
        print("=" * 60)
        print("\n📝 Pour installer les dépendances:")
        print("   bash install_robot_gui.sh")
        print()
        print("📝 Ou manuellement:")
        print("   sudo apt install python3-tk python3-opencv python3-picamera2")
        print("   pip3 install -r requirements.txt")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())