#!/usr/bin/env python3
# ============================================================================
#  robot_solver.py
#  --------------
#  Objectif :
#     Orchestrer le **pipeline complet** du robot solveur, depuis la capture des
#     6 faces jusqu’à la résolution et (optionnellement) l’exécution physique
#     des mouvements, avec une gestion standardisée de la progression via callbacks.
#
#  Pipeline (méthode run) — SCHÉMA ESSENTIEL :
#
#        [Caméra / Images F,R,B,L,U,D]
#                       │
#                       ▼
#             1) capture_images()
#                       │
#                       ▼
#        2) calibrate_roi_auto()   [optionnel : YOLO]
#                       │
#                       ▼
#             3) detect_colors()
#                       │
#                       ▼
#          4) convert_to_kociemba()
#     → CubeString (54 caractères URFDLB)
#                       │
#              ┌────────┴─────────┐
#              │                  │
#              ▼                  ▼
#       5) solve(cube_string)   (do_solve=False)
#     → Solution (Singmaster)
#              │
#              ▼
#       6) execute_moves(solution) (do_execute=True)
#
#  Progress / callbacks :
#     - Toutes les étapes émettent des événements structurés via self.emit(...)
#       (progress.emit), typiquement : *_started, *_completed, *_failed,
#       et des événements “granulaires” : capture_face, detect_face, execute_move...
#
#  Classes :
#     - CameraInterface :
#         Interface générique (placeholder) pour brancher une caméra réelle.
#     - RobotCubeSolver :
#         Classe principale contenant l’état (cube_string, solution, stop_flag)
#         et les 6 étapes du pipeline + run().
#
#  Entrées attendues :
#     - Captures : tmp/{F,R,B,L,U,D}.jpg (produites par capture_all_faces)
#     - Calibration ROI : rubiks_calibration.json (obligatoire pour la vision)
#     - (Option) YOLO : in/best.pt + ultralytics pour auto-calibrer ROI
#
#  Sorties :
#     - cube_string : chaîne URFDLB (54 caractères, valide pour solveur)
#     - solution    : suite de mouvements Singmaster ("R U R' ...") (si do_solve)
#     - exécution   : mouvements robot (si do_execute) via robot_moves_cubotino
#
#  Fonctions clés (par étape) :
#     1) capture_images():
#        - Initialise CameraInterface2, allume LEDs, reset robot,
#          verrouille AE/AWB (lock_for_scan_multiface), puis capture_all_faces().
#
#     2) calibrate_roi_auto():
#        - Optionnel : calibrate_roi_yolo(...) si YOLO disponible.
#
#     3) detect_colors():
#        - Charge ROI (load_calibration), puis detect_colors_for_faces(...)
#          et simule une progression par face via events detect_face.
#
#     4) convert_to_kociemba():
#        - convert_to_kociemba(color_results, mode="robot_cam", strategy="center_hsv")
#          + validations fortes (len=54, alphabet URFDLB, 9× chaque lettre).
#
#     5) solve():
#        - solve_cube(...) via solver_wrapper ; gère CubeAlreadySolved.
#
#     6) execute_moves():
#        - execute_solution(...) via robot_moves_cubotino, avec stop_flag,
#          et remonte la progression vers le callback (execute_move, finished/stopped).
#
#  Contrôle arrêt d’urgence :
#     - stop_flag (threading.Event) : lu pendant l’exécution mouvements.
#     - emergency_stop() / reset_stop_flag().
# ============================================================================

import os
import threading

from calibration_rubiks import load_calibration
#from calibration_colors import load_color_calibration
from process_images_cube import detect_colors_for_faces
from processing_rubiks import convert_to_kociemba
from solver_wrapper import solve_cube
from robot_moves_cubotino import execute_solution,ExecutionStopped
from capture_photo_from_311 import CameraInterface2
import traceback
from types_shared import FaceResult, FacesDict
from progress import emit as _emit


try:
    from calibration_roi import calibrate_roi_yolo
    from ultralytics.solutions import solutions
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    calibrate_roi_yolo = None

class PipelineStopped(Exception):
    """Arrêt demandé (E-STOP). Ce n’est pas une erreur."""
    pass

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

class CubeAlreadySolved(Exception):
    pass

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
        self.progress_callback = None

    ## Utiliser pour les call backs
    def emit(self, event: str, **data):  
        _emit(self.progress_callback, event, **data)
    # ========================================================================
    # ÉTAPE 1 : CAPTURE DES FACES capture_images
    # ========================================================================

    def capture_images(self):
        import os, traceback
        from robot_moves_cubotino import flip_up,return_to_u_fr
        from robot_servo import reset_initial

        camera = None
        try:
            print("🔍 Début de capture des images...")

            rotation = 0
            folder = ""

            out_dir = self.image_folder if not folder else os.path.join(self.image_folder, folder)
            os.makedirs(out_dir, exist_ok=True)

            camera = CameraInterface2(rotation=rotation) if "rotation" in CameraInterface2.__init__.__code__.co_varnames else CameraInterface2()
            self.camera = camera

            self.emit("camera_lock_started",
                    step="capture",
                    face="LOCK",
                    status="locking_started",
                    pct=0.00,
                    msg="Camera lock started (AE/AWB)")
            camera.leds_on_for_scan()
            reset_initial()

            def flip_cb():
                flip_up()

            #camera.lock_for_scan_multiface(
            #    flip_cb=flip_cb,
            #    n_samples=4,
            #    aggregate="median",
            #    warmup_s=0.8,
            #    settle_after_flip_s=0.25,
            #    per_pose_timeout_s=1.2,
            #    stability_pts=6,
            #    tol=0.05,
            #    min_exp=8000,
            #    max_gain=8.0,
            #    debug=True
            #)

            self.check_stop("capture", 0.00)
            camera.lock_for_scan_multiface_cfg(flip_cb=flip_cb, debug=True)
            self.check_stop("capture", 0.02)
            self.emit("camera_lock_done",
                    step="capture",
                    face="LOCK",
                    status="locking_done",
                    pct=0.02,
                    msg="Camera lock done")
            self.capture_all_faces()
            print("🔍 Retour à l'état initial...")
            #return_to_u_fr()
            print("🔍 Fin de capture des images...")

        except Exception as e:
            print("❌ ERREUR lors de la capture des images:")
            print(traceback.format_exc())
            raise RuntimeError(f"CAPTURE_FAILED: {e}") from e

        finally:
            # cleanup best-effort
            try:
                if camera:
                    camera.leds_off()
            except Exception:
                pass
            try:
                if camera:
                    camera.close()
            except Exception:
                pass

    def capture_all_faces(self):
        from robot_moves_cubotino import flip_up,scan_yaw_out,scan_yaw_home

        faces_total = 6
        current = 0

        # Capture occupe 0.02 -> 0.20 (comme dans l'exemple capture_images)
        CAP_START = 0.02
        CAP_END = 0.20

        def pct_for(i: int) -> float:
            return CAP_START + (CAP_END - CAP_START) * (i / faces_total)        

        def snap(face):
            nonlocal current
            current += 1
            self.check_stop("capture", pct_for(current))

            self.emit(
                "capture_face",
                step="capture",
                face=face,
                current=current,
                total=faces_total,
                status="capturing",
                pct=pct_for(current),
                msg=f"Capturing {face} ({current}/{faces_total})"
            )

            print(f"📸 {face}")
            self.camera.capture_image(
                filename=f"{self.image_folder}/{face}.jpg",
                rotation=0
            )
            self.emit(
                "capture_face",
                step="capture",
                face=face,
                current=current,
                total=faces_total,
                status="completed",
                pct=pct_for(current),
                msg=f"Captured {face} ({current}/{faces_total})"
            )      
        # U
        self.check_stop("capture")
        snap("U")

        # B
        self.check_stop("capture")
        flip_up()
        snap("B")

        # D
        self.check_stop("capture")
        flip_up()
        snap("D")

        # F
        self.check_stop("capture")
        flip_up()
        snap("F")

        # R
        self.check_stop("capture")
        scan_yaw_out("D")  # ou "G"
        flip_up()
        scan_yaw_home()
        snap("R")

        # L
        self.check_stop("capture")
        flip_up()
        flip_up()
        snap("L")
        scan_yaw_home()

    # ========================================================================
    # ÉTAPE 2 : CALIBRATION AUTOMATIQUE (optionnelle)
    # ========================================================================
    
    def calibrate_roi_auto(self, show_preview=False):
        """
        Calibration automatique des ROI avec YOLO.
        
        Args:
            show_preview: afficher les résultats de détection
        """
        if not YOLO_AVAILABLE:
            print("❌ YOLO non installé")
            return
        print("🔧 Calibration automatique YOLO...")
        calibrate_roi_yolo(show_preview=show_preview)
        print("✅ Calibration terminée")
    
    # ========================================================================
    # ÉTAPE 3 : DÉTECTION DES COULEURS
    # ========================================================================  
    def detect_colors(self):
        faces = ["F", "R", "B", "L", "U", "D"]
        total = len(faces)
        
        print("🔍 Détection des couleurs...")
        
        # Charger les calibrations
        roi = load_calibration()
        if roi is None:
            raise ValueError("Calibration ROI introuvable")        
        #color_calib = load_color_calibration()
        color_calib = None

        # plage de progression globale pour la détection
        DET_START = 0.30
        DET_END = 0.55

        def pct_for(i: int) -> float:
            return DET_START + (DET_END - DET_START) * (i / total)

        # Simuler une progression "processing" pour l'UI
        for i, face in enumerate(faces, 1):
            self.check_stop("detection", pct_for(i))
            self.emit(
                "detect_face",
                step="detection",
                face=face,
                current=i,
                total=total,
                status="processing",
                pct=pct_for(i),
                msg=f"Processing {face} ({i}/{total})"
            )

        self.check_stop("detection", DET_START)
        color_results: FacesDict = detect_colors_for_faces(self.image_folder, roi, color_calib, debug=self.debug, strict=True)
        self.check_stop("detection", DET_END)

        # Avec progression : notifier chaque face
        # Note: detect_colors_for_faces traite toutes les faces d'un coup
        # On simule la progression pour l'interface
        
        # Notifier fin "completed"
        for i, face in enumerate(faces, 1):
            self.emit(
                "detect_face",
                step="detection",
                face=face,
                current=i,
                total=total,
                status="completed",
                pct=pct_for(i),
                msg=f"Completed {face} ({i}/{total})"
            )
        
        print("✅ Détection terminée")
        return color_results
    
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
        self.check_stop("conversion", 0.55)
        ok, cube, err = convert_to_kociemba(
            color_results,
            mode="robot_cam",
            strategy="center_hsv",
            debug=self.debug
        )
        
        if not ok:
            raise ValueError(f"Échec conversion: {err}")

        if not isinstance(cube, str) or len(cube) != 54:
            raise ValueError(f"CubeString invalide: len={len(cube) if isinstance(cube,str) else type(cube)} cube={cube!r}")

        allowed = set("URFDLB")
        if set(cube) - allowed:
            raise ValueError(f"CubeString contient des caractères invalides: {set(cube) - allowed}")

        # optionnel : vérifier 9 de chaque lettre
        from collections import Counter
        cnt = Counter(cube)
        if any(cnt[k] != 9 for k in "URFDLB"):
            raise ValueError(f"Répartition invalide (doit être 9x chaque): {dict(cnt)}")
        
        print(f"✅ CubeString: {cube}")
        self.cube_string = cube
        return cube
    
    # ========================================================================
    # ÉTAPE 5 : RÉSOLUTION
    # ========================================================================
    
    def solve(self, cube_string: str, method: str = "kociemba") -> str:
        print(f"🧩 Résolution du cube... (method={method})")
        self.check_stop("solve", 0.60)

        cube_string = (cube_string or "").strip()
        SOLVED_URFDLB = "U"*9 + "R"*9 + "F"*9 + "D"*9 + "L"*9 + "B"*9

        if cube_string == SOLVED_URFDLB:
            raise CubeAlreadySolved("Cube déjà résolu (état = URFDLB solved).")

        try:
            solution = solve_cube(cube_string, method=method)
        except Exception as e:
            raise RuntimeError(f"SOLVE_FAILED method={method}: {e}") from e

        solution = (solution or "").strip()
        print(f"✅ Solution: {solution!r}")

        # optionnel : tu peux aussi traiter solution=="" comme "déjà résolu"
        if solution == "":
            raise CubeAlreadySolved("Cube déjà résolu (solution vide).")

        self.solution = solution
        return solution


    # ========================================================================
    # ÉTAPE 6 : EXÉCUTION DES MOUVEMENTS
    # ========================================================================
    
    def execute_moves(self, solution: str, start_mode="LUB"):
        print("▶️ Exécution des mouvements...")
        self.check_stop("execute", 0.70)
        #input("Entrée pour continuer (stop si effort anormal) ")

        EXEC_START, EXEC_END = 0.70, 1.00

        def progress(event, data):
            # On copie + on enlève la clé "event" si robot_moves l'a mise,
            # pour éviter collision / double event dans le payload final.
            data = dict(data)
            data.pop("event", None)

            idx = data.get("index") or data.get("current") or 0
            tot = data.get("total") or 0
            pct = EXEC_START + (EXEC_END - EXEC_START) * (idx / tot) if tot else None

            # Clamp optionnel (évite >1.0 si idx dépasse total)
            if isinstance(pct, (int, float)):
                if pct < EXEC_START: pct = EXEC_START
                if pct > EXEC_END: pct = EXEC_END

            self.emit(event, pct=pct, **data)

        try:
            _moves_str = execute_solution(
                solution,
                start_mode=start_mode,
                verbose=True,
                dry_run=False,
                stop_flag=self.stop_flag,
                progress_callback=progress,
            )
            print("✅ Exécution terminée")
            return True

        except ExecutionStopped:
            print("🔴 Exécution interrompue")
            return False
    
    # ========================================================================
    # PIPELINE COMPLET
    # ========================================================================
    
    def run(self,
            do_solve=False,
            do_execute=False,
            auto_calibrate=False,
            progress_callback=None):
        # # Initialise la fonction de callback
        self.progress_callback = progress_callback

        # # Test de l'arret
        if self.stop_flag.is_set():
            self.emit("pipeline_stopped", step="start", pct=0.0, msg="E-STOP already active")
            raise PipelineStopped("E-STOP already active")

        # Réinitialiser le flag d'arrêt
        self.stop_flag.clear()
        
        # ====================================================================
        # 1️⃣ CAPTURE DES FACES
        # ====================================================================
        self.emit("capture_started", step="capture", pct=0.00, msg="Capture started")
        try:
            self.check_stop("capture", 0.0)
            self.capture_images()
            self.emit("capture_completed", step="capture", pct=0.20, msg="Capture completed")
        except PipelineStopped:
            # STOP = pas une erreur => on remonte juste l'exception
            raise            
        except Exception as e:
            self.emit("capture_failed", step="capture", pct=0.20, msg=str(e), err=str(e))
            raise


        # ====================================================================
        # 2️⃣ CALIBRATION AUTOMATIQUE YOLO (optionnelle)
        # ====================================================================
        if auto_calibrate:
            self.emit("calibration_started", step="calibration", pct=0.20, msg="Calibration started (YOLO)")       
            try:
                self.calibrate_roi_auto(show_preview=False)
                self.emit("calibration_completed", step="calibration", pct=0.30, msg="Calibration completed")
            except PipelineStopped:
                # STOP = pas une erreur => on remonte juste l'exception
                raise                  
            except Exception as e:
                self.emit("calibration_failed", step="calibration", pct=0.30, msg=str(e), err=repr(e))
                raise                
        
        # ====================================================================
        # 3️⃣ DÉTECTION DES COULEURS
        # ====================================================================
        self.emit("detection_started", step="detection", pct=0.30, msg="Detection started")
        try:
            self.check_stop("detection", 0.30)
            color_results = self.detect_colors()
            self.emit("detection_completed", step="detection", pct=0.55, msg="Detection completed")
        except PipelineStopped:
            # STOP = pas une erreur => on remonte juste l'exception
            raise              
        except Exception as e:
            self.emit("detection_failed", step="detection", pct=0.55, msg=str(e), err=repr(e))
            raise            
        
        # ====================================================================
        # 4️⃣ CONVERSION EN FORMAT KOCIEMBA
        # ====================================================================
        self.emit("conversion_started", step="conversion", pct=0.55, msg="Conversion to Kociemba started")
        try:
            self.check_stop("conversion", 0.55)
            cube_string = self.convert_to_kociemba(color_results)
            self.emit("conversion_completed", step="conversion", pct=0.60,
              msg="Conversion completed", cube_string=cube_string)
        except PipelineStopped:
            # STOP = pas une erreur => on remonte juste l'exception
            raise                
        except Exception as e:
            self.emit("conversion_failed", step="conversion", pct=0.60, msg=str(e), err=repr(e))
            raise         

        # S'arrêter ici si pas de résolution demandée
        if not do_solve:
            return cube_string
        
        # ====================================================================
        # 5️⃣ RÉSOLUTION
        # ====================================================================
        self.emit("solving_started", step="solve", pct=0.60, msg="Solving started (kociemba)")
        try:
            self.check_stop("solve", 0.60)
            solution = self.solve(cube_string, method="kociemba")
            moves_count = len(solution.split()) if solution else 0
            self.emit("solving_completed", step="solve", pct=0.70,
              msg="Solving completed", moves=moves_count,solution=solution)
        except CubeAlreadySolved as e:
            print(f"🟦 {e}")
            self.emit("already_solved", step="solve", pct=0.70, msg=str(e), moves=0)
            self.solution = ""
            return cube_string, ""
        except PipelineStopped:
            # STOP = pas une erreur => on remonte juste l'exception
            raise              
        except Exception as e:
            self.emit("solving_failed", step="solve", pct=0.70, msg=str(e), err=repr(e))
            raise
                
        # S'arrêter ici si pas d'exécution demandée
        if not do_execute:
            return cube_string, solution
        
        # ====================================================================
        # 6️⃣ EXÉCUTION DES MOUVEMENTS
        # ====================================================================
        ## self.emit("execution_started", step="execute", pct=0.70, msg="Execution started") ## Inutile déjà dans execute move
        
        try:
            self.check_stop("execute", 0.80)
            success = self.execute_moves(solution)
            if success:
                    # self.emit("execution_completed", step="execute", pct=1.00, msg="Execution completed", success=True) ## Inutile déjà dans execute move
                    print("🔍 Execution completed...")
            else:
                # stopped (stop_flag / erreur gérée / etc.)
                # self.emit("execution_stopped", step="execute", pct=1.00, msg="Execution stopped", success=False) ## Inutile déjà dans execute move
                print("🔍 Execution stopped...")
        except PipelineStopped:
            # STOP = pas une erreur => on remonte juste l'exception
            raise                  
        except Exception as e:
            print(f"🔍 Execution failed: {e}")
            self.emit("execution_failed", step="execute", pct=1.00, msg=str(e), err=repr(e)) ## Laissé
            raise   

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

    def check_stop(self, step: str = "", pct: float | None = None, msg: str = "E-STOP activated"):
        if self.stop_flag.is_set():
            self.emit("pipeline_stopped", step=step or "unknown", pct=pct, msg=msg)
            raise PipelineStopped(msg)


# ============================================================================
# TESTS
# ============================================================================


if __name__ == "__main__":
    from progress_listeners import console_clean_listener, jsonl_file_listener, multi_listener

    print("="*60)
    print("TEST robot_solver.py")
    print("="*60)

    file_listener = jsonl_file_listener(folder="tmp", prefix="progress")
    debug_listener = jsonl_file_listener(folder="tmp", prefix="debug_progress")
    listener = multi_listener(console_clean_listener, file_listener, debug_listener)
    print("JSONL:", file_listener.path)
    
    # Test avec callbacks
    solver = RobotCubeSolver(image_folder="tmp", debug="text")
    
    try:
        cube_string, solution = solver.run(
            do_solve=True,
            do_execute=False,
            auto_calibrate=True,
            progress_callback=listener
        )
        
        print("\n" + "="*60)
        print("✅ TEST TERMINÉ")
        print(f"CubeString: {cube_string}")
        print(f"Solution: {solution}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")