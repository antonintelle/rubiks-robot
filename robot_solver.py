# ============================================================================
#  robot_solver.py
#  ----------------
#  Objectif :
#     Classe principale pour orchestrer toutes les étapes du robot
#     depuis la capture des images jusqu'à la résolution et l'exécution.
#
#  Pipeline (méthode run) :
#     1) capture_all_faces  : acquisition des 6 faces (F,R,B,L,U,D) via caméra
#     2) calibrate_roi      : calibration automatique YOLO (optionnelle)
#     3) detect_colors      : détection des couleurs par vision (FacesDict)
#     4) convert_to_kociemba: conversion en string Kociemba 54 (URFDLB)
#     5) solve              : appel au solveur pour obtenir la séquence
#     6) execute_moves      : exécution physique des mouvements
#
#  Classes :
#     - CameraInterface : interface générique pour plugger une caméra réelle
#     - RobotCubeSolver : classe principale pilotant le pipeline complet
#
#  Méthodes clés de RobotCubeSolver :
#     - capture_all_faces(progress_callback)  : capture avec progression
#     - detect_colors(progress_callback)      : détection avec progression
#     - convert_to_kociemba()                 : conversion vers format solveur
#     - solve()                               : appelle solver_wrapper.solve_cube
#     - execute_moves(progress_callback)      : exécution avec progression
#     - run(callbacks...)                     : pipeline complet avec callbacks
#     - emergency_stop()                      : arrêt d'urgence
#
#  Entrées :
#     - Images des 6 faces (F.jpg, R.jpg, B.jpg, L.jpg, U.jpg, D.jpg)
#     - Fichiers de calibration (optionnels avec auto_calibrate)
#
#  Sorties :
#     - CubeString (URFDLB, 54 caractères)
#     - Solution (suite de mouvements Singmaster)
#
# ============================================================================
# ============================================================================
#  Pipeline visuel avec callbacks
#
#        [Caméra / Images F,R,B,L,U,D]
#                       │
#                       ▼
#             capture_all_faces(callback)
#         → callback(face, current, total, status)
#                       │
#                       ▼
#         calibrate_roi_yolo() [optionnel]
#                       │
#                       ▼
#              detect_colors(callback)
#         → callback(face, current, total, status)
#                       │
#                       ▼
#         convert_to_kociemba()
#     → CubeString (54 caractères URFDLB)
#                       │
#              ┌────────┴─────────┐
#              │                  │
#              ▼                  ▼
#        solve(cube_string)   (do_solve=False)
#     → Solution mouvements
#              │
#              ▼
#        execute_moves(callback)
#     → callback(current, total, move, next_move, status)
# ============================================================================

import os
import threading

from calibration_rubiks import load_calibration
from process_images_cube import detect_colors_for_faces, load_color_calibration
from processing_rubiks import convert_to_kociemba
from solver_wrapper import solve_cube
from robot_moves import execute_solution
from calibration_roi import calibrate_roi_yolo


class CameraInterface:
    """Interface générique pour une caméra réelle"""
    
    def capture_face(self, face_name: str):
        """
        À implémenter si tu pilotes une vraie caméra/robot.
        
        Args:
            face_name: 'F', 'R', 'B', 'L', 'U', ou 'D'
        
        Returns:
            Image capturée (numpy array ou PIL Image)
        """
        raise NotImplementedError("Implémenter la capture caméra")


class RobotCubeSolver:
    """
    Classe principale pour piloter le robot Rubik's Cube.
    
    Usage:
        solver = RobotCubeSolver(image_folder="tmp", debug="text")
        cube_string, solution = solver.run(
            do_solve=True,
            do_execute=True,
            capture_callback=my_capture_callback,
            execute_callback=my_execute_callback
        )
    """
    
    def __init__(self, image_folder="tmp", debug="text", camera=None):
        """
        Initialise le solveur.
        
        Args:
            image_folder: dossier contenant les images des faces
            debug: niveau de debug ("none", "text", "both")
            camera: instance de CameraInterface (optionnel)
        """
        self.image_folder = image_folder
        self.debug = debug
        self.camera = camera
        
        # Flag pour arrêt d'urgence
        self.stop_flag = threading.Event()
        
        # Stockage des résultats
        self.cube_string = None
        self.solution = None
    
    # ========================================================================
    # ÉTAPE 1 : CAPTURE DES FACES
    # ========================================================================
    
    def capture_all_faces(self, progress_callback=None):
        """
        Capture les 6 faces du cube (ou vérifie leur présence).
        
        Args:
            progress_callback: fonction appelée pour chaque face
                             callback(face, current, total, status)
                             status: "capturing", "completed", "loaded"
        
        Returns:
            bool: True si succès
        """
        faces = ["F", "R", "B", "L", "U", "D"]
        total = len(faces)
        
        # Si pas de caméra, on suppose que les fichiers existent déjà
        if self.camera is None:
            print("📁 Mode fichiers existants (pas de caméra)")
            if progress_callback:
                for i, face in enumerate(faces, 1):
                    progress_callback(face, i, total, "loaded")
            return True
        
        # Avec caméra : capture réelle
        os.makedirs(self.image_folder, exist_ok=True)
        print("📸 Capture des 6 faces...")
        
        for i, face in enumerate(faces, 1):
            # Notifier début capture
            if progress_callback:
                progress_callback(face, i, total, "capturing")
            
            # Capture réelle
            img = self.camera.capture_face(face)
            
            # TODO: Sauvegarder l'image
            # import cv2
            # cv2.imwrite(f"{self.image_folder}/{face}.jpg", img)
            
            # Notifier fin capture
            if progress_callback:
                progress_callback(face, i, total, "completed")
        
        print("✅ Capture terminée")
        return True
    
    # ========================================================================
    # ÉTAPE 2 : CALIBRATION AUTOMATIQUE (optionnelle)
    # ========================================================================
    
    def calibrate_roi_auto(self, show_preview=False):
        """
        Calibration automatique des ROI avec YOLO.
        
        Args:
            show_preview: afficher les résultats de détection
        """
        print("🔧 Calibration automatique YOLO...")
        calibrate_roi_yolo(show_preview=show_preview)
        print("✅ Calibration terminée")
    
    # ========================================================================
    # ÉTAPE 3 : DÉTECTION DES COULEURS
    # ========================================================================
    
    def detect_colors(self, progress_callback=None):
        """
        Détecte les couleurs des 6 faces.
        
        Args:
            progress_callback: fonction appelée pour chaque face
                             callback(face, current, total, status)
                             status: "processing", "completed"
        
        Returns:
            dict: résultats de détection (FacesDict)
        """
        faces = ["F", "R", "B", "L", "U", "D"]
        total = len(faces)
        
        print("🔍 Détection des couleurs...")
        
        # Charger les calibrations
        roi = load_calibration()
        color_calib = load_color_calibration()
        
        # Si pas de callback, appel classique
        if progress_callback is None:
            return detect_colors_for_faces(
                self.image_folder, roi, color_calib, debug=self.debug
            )
        
        # Avec progression : notifier chaque face
        # Note: detect_colors_for_faces traite toutes les faces d'un coup
        # On simule la progression pour l'interface
        
        for i, face in enumerate(faces, 1):
            if progress_callback:
                progress_callback(face, i, total, "processing")
        
        # Traitement réel
        results = detect_colors_for_faces(
            self.image_folder, roi, color_calib, debug=self.debug
        )
        
        # Notifier fin
        for i, face in enumerate(faces, 1):
            if progress_callback:
                progress_callback(face, i, total, "completed")
        
        print("✅ Détection terminée")
        return results
    
    # ========================================================================
    # ÉTAPE 4 : CONVERSION EN FORMAT KOCIEMBA
    # ========================================================================
    
    def convert_to_kociemba(self, color_results):
        """
        Convertit les résultats de détection en string Kociemba.
        
        Args:
            color_results: dict retourné par detect_colors()
        
        Returns:
            str: cube string (54 caractères)
        
        Raises:
            ValueError: si la conversion échoue
        """
        print("🔄 Conversion en format Kociemba...")
        
        ok, cube, err = convert_to_kociemba(
            color_results,
            mode="robot_raw",
            strategy="center_hsv",
            debug=self.debug
        )
        
        if not ok:
            raise ValueError(f"Échec conversion: {err}")
        
        print(f"✅ CubeString: {cube}")
        self.cube_string = cube
        return cube
    
    # ========================================================================
    # ÉTAPE 5 : RÉSOLUTION
    # ========================================================================
    
    def solve(self, cube_string):
        """
        Résout le cube avec le solveur Kociemba.
        
        Args:
            cube_string: string de 54 caractères (URFDLB)
        
        Returns:
            str: solution (séquence de mouvements)
        """
        print("🧩 Résolution du cube...")
        solution = solve_cube(cube_string)
        print(f"✅ Solution: {solution}")
        self.solution = solution
        return solution
    
    # ========================================================================
    # ÉTAPE 6 : EXÉCUTION DES MOUVEMENTS
    # ========================================================================
    
    def execute_moves(self, solution: str, progress_callback=None):
        """
        Exécute la séquence de mouvements sur le robot.
        
        Args:
            solution: séquence de mouvements (ex: "U R2 F' L")
            progress_callback: callback(current, total, move, next_move, status)
                             status: "executing", "completed", "finished", "stopped"
        
        Returns:
            bool: True si terminé, False si arrêté
        """
        print("▶️ Exécution des mouvements...")
        success = execute_solution(
            solution,
            progress_callback=progress_callback,
            stop_flag=self.stop_flag
        )
        
        if success:
            print("✅ Exécution terminée")
        else:
            print("🔴 Exécution interrompue")
        
        return success
    
    # ========================================================================
    # PIPELINE COMPLET
    # ========================================================================
    
    def run(self,
            do_solve=False,
            do_execute=False,
            auto_calibrate=True,
            capture_callback=None,
            detect_callback=None,
            solve_callback=None,
            execute_callback=None):
        """
        Exécute le pipeline complet avec callbacks optionnels.
        
        Args:
            do_solve: calculer la solution (sinon s'arrête après encodage)
            do_execute: exécuter les mouvements (nécessite do_solve=True)
            auto_calibrate: calibration automatique YOLO après capture
            
            capture_callback(face, current, total, status):
                Appelé pendant la capture des faces
                status: "capturing", "completed", "loaded"
            
            detect_callback(face, current, total, status):
                Appelé pendant la détection des couleurs
                status: "processing", "completed"
            
            solve_callback(status):
                Appelé aux différentes étapes du pipeline
                status: "capture_started", "capture_completed",
                       "calibration_started", "calibration_completed",
                       "detection_started", "detection_completed",
                       "conversion_started", "conversion_completed",
                       "solving_started", "solving_completed",
                       "execution_started", "execution_completed", "execution_stopped"
            
            execute_callback(current, total, move, next_move, status):
                Appelé pendant l'exécution des mouvements
                status: "executing", "completed", "finished", "stopped"
        
        Returns:
            tuple: (cube_string, solution) si do_solve=True
            str: cube_string si do_solve=False
        
        Raises:
            ValueError: si erreur dans le pipeline
        """
        
        # Réinitialiser le flag d'arrêt
        self.stop_flag.clear()
        
        # ====================================================================
        # 1️⃣ CAPTURE DES FACES
        # ====================================================================
        if solve_callback:
            solve_callback("capture_started")
        
        self.capture_all_faces(capture_callback)
        
        if solve_callback:
            solve_callback("capture_completed")
        
        # ====================================================================
        # 2️⃣ CALIBRATION AUTOMATIQUE YOLO (optionnelle)
        # ====================================================================
        if auto_calibrate:
            if solve_callback:
                solve_callback("calibration_started")
            
            self.calibrate_roi_auto(show_preview=False)
            
            if solve_callback:
                solve_callback("calibration_completed")
        
        # ====================================================================
        # 3️⃣ DÉTECTION DES COULEURS
        # ====================================================================
        if solve_callback:
            solve_callback("detection_started")
        
        color_results = self.detect_colors(detect_callback)
        
        if solve_callback:
            solve_callback("detection_completed")
        
        # ====================================================================
        # 4️⃣ CONVERSION EN FORMAT KOCIEMBA
        # ====================================================================
        if solve_callback:
            solve_callback("conversion_started")
        
        cube_string = self.convert_to_kociemba(color_results)
        
        if solve_callback:
            solve_callback("conversion_completed")
        
        # S'arrêter ici si pas de résolution demandée
        if not do_solve:
            return cube_string
        
        # ====================================================================
        # 5️⃣ RÉSOLUTION
        # ====================================================================
        if solve_callback:
            solve_callback("solving_started")
        
        solution = self.solve(cube_string)
        
        if solve_callback:
            solve_callback("solving_completed")
        
        # S'arrêter ici si pas d'exécution demandée
        if not do_execute:
            return cube_string, solution
        
        # ====================================================================
        # 6️⃣ EXÉCUTION DES MOUVEMENTS
        # ====================================================================
        if solve_callback:
            solve_callback("execution_started")
        
        success = self.execute_moves(solution, execute_callback)
        
        if solve_callback:
            status = "execution_completed" if success else "execution_stopped"
            solve_callback(status)
        
        return cube_string, solution
    
    # ========================================================================
    # ARRÊT D'URGENCE
    # ========================================================================
    
    def emergency_stop(self):
        """
        Active l'arrêt d'urgence.
        Interrompt l'exécution en cours des mouvements.
        """
        self.stop_flag.set()
        print("🔴 ARRÊT D'URGENCE ACTIVÉ")
    
    def reset_stop_flag(self):
        """Réinitialise le flag d'arrêt d'urgence"""
        self.stop_flag.clear()
        print("✅ Flag d'arrêt réinitialisé")


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("TEST robot_solver.py")
    print("="*60)
    
    # Callbacks de test
    def test_capture_callback(face, current, total, status):
        print(f"  Capture [{current}/{total}] Face {face}: {status}")
    
    def test_detect_callback(face, current, total, status):
        print(f"  Détection [{current}/{total}] Face {face}: {status}")
    
    def test_solve_callback(status):
        print(f"  Pipeline: {status}")
    
    def test_execute_callback(current, total, move, next_move, status):
        if status == "executing":
            print(f"  Exécution [{current}/{total}] {move} (suivant: {next_move})")
        elif status == "completed":
            print(f"  ✅ [{current}/{total}] {move} terminé")
    
    # Test avec callbacks
    solver = RobotCubeSolver(image_folder="tmp", debug="text")
    
    try:
        cube_string, solution = solver.run(
            do_solve=True,
            do_execute=False,  # Mettre True pour tester l'exécution
            auto_calibrate=True,
            capture_callback=test_capture_callback,
            detect_callback=test_detect_callback,
            solve_callback=test_solve_callback,
            execute_callback=test_execute_callback
        )
        
        print("\n" + "="*60)
        print("✅ TEST TERMINÉ")
        print(f"CubeString: {cube_string}")
        print(f"Solution: {solution}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")