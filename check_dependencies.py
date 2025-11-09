#!/usr/bin/env python3
# =====================================================================
# check_dependencies.py
# Script de vérification des dépendances avant lancement du GUI robot
# =====================================================================

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
        ("Ultralytics (YOLO)", "ultralytics"),
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
    ]
    
    for name, import_name in optional_modules:
        check_module(name, import_name, optional=True)
    
    # ====================================================================
    # 3. Fichiers du projet
    # ====================================================================
    print("\n📁 Fichiers du projet:")
    
    project_files = [
        ("robot_moves.py", "Module des mouvements robot"),
        ("robot_solver.py", "Module solveur robot"),
        ("tkinter_gui_robot.py", "Interface graphique robot"),
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