<<<<<<< HEAD
#!/usr/bin/env python3
# ============================================================================
#  rubiks_operations.py
#  --------------------
#  Objectif :
#     Fournir une **couche “métier” unifiée** (API) pour piloter toutes les
#     fonctionnalités du projet Rubik’s Cube, indépendamment de l’interface :
#       - CLI (texte), GUI (Tkinter/PyQt), API REST, tests unitaires, etc.
#     Le module encapsule :
#       - la calibration ROI et couleurs,
#       - le processing vision -> cubestring (Singmaster/Kociemba),
#       - la résolution (solveur) + génération d’URL de visualisation,
#       - le mode robot complet (progress listeners + TFT),
#       - la capture d’images (simple ou via robot + lock camera multi-face),
#       - des outils debug et utilitaires (nettoyage tmp, statut, infos système).
#
#  Architecture / conventions :
#     - Toutes les opérations retournent des dictionnaires standardisés
#       (OperationResult.to_dict()) :
#         {success: bool, data: Any|None, error: str|None, message: str|None, metadata: dict|None}
#     - Séparation stricte logique métier vs UI (pas d’input/print sauf cas tests).
#     - Enums pour les modes (DebugMode, ProcessingMode).
#
#  Entrées principales (API) :
#     - class RubiksOperations(tmp_folder="tmp", config_folder=".")
#         Gestionnaire central d’opérations ; référence les fichiers :
#           * rubiks_calibration.json (ROI)
#           * rubiks_color_calibration.json (couleurs)
#
#  Calibration :
#     - calibrate_zones_interactive()
#         Lance calibration ROI (calibration_roi.calibration_menu).
#     - calibrate_colors_interactive()
#         Lance calibration couleurs (calibration_colors.calibrate_colors_interactive).
#     - get_calibration_status()
#         Retourne l’état ROI + couleurs + metadata (stats via calibration_rubiks.get_calibration_stats).
#     - load_roi_calibration() / load_color_calibration()
#         Charge les JSON de calibration et les retourne dans data.
#
#  Processing / production :
#     - process_rubiks_cube(debug="text")
#         Vision + encodage :
#           * vérifie ROI + couleurs,
#           * appelle processing_rubiks.production_mode(...),
#           * retourne singmaster + faces (si fourni).
#     - process_api_mode(debug="text")
#         Variante “sans UI” : processing_rubiks.process_rubiks_to_singmaster(...)
#     - quick_pipeline_test(mode="robot_raw", debug="text")
#         Lance processing_rubiks.quick_pipeline_test_corrected(...)
#
#  Debug :
#     - debug_single_face(face)
#         Diagnostic détaillé d’une face (process_images_cube.test_single_face_debug).
#     - debug_color_mapping()
#         Diagnostic mapping couleurs (processing_rubiks.debug_color_mapping).
#     - debug_vision_and_rotations()
#         Debug complet vision + rotations (processing_rubiks.full_debug_pipeline).
#
#  Solveur :
#     - solve_cube(cubestring)
#         Résout une chaîne 54 caractères via solver_wrapper.solve_cube.
#     - solve_and_get_url(cubestring, method="kociemba", site="alg")
#         Résout + génère une URL via url_convertor.convert_to_url.
#
#  Mode robot (pipeline complet + progress + TFT) :
#     - run_robot_mode(do_solve=True, do_execute=False, debug="text")
#         Orchestration :
#           * RobotCubeSolver.run(...)
#           * listeners : console_clean_listener + jsonl_file_listener + TFT listener
#           * retourne cubestring, solution, chemin log JSONL, flags solved/executed.
#
#  Capture d’images :
#     - capture_images(rotation=0, folder="captures")
#         Capture interactive via CameraInterface2.capture_loop.
#     - capture_single_image(rotation=0, folder="captures")
#         Capture unique (fonction capture_image) + retourne le chemin.
#     - capture_images_robot(rotation=0, folder="", debug="text")
#         Capture “robot” :
#           * reset_initial + lock_for_scan_multiface (avec flips)
#           * capture_all_faces via RobotCubeSolver
#           * gestion LEDs + close caméra (cleanup best-effort).
#
#  Calibration des blancs (AWB) :
#     - calibrate_blancs()
#         Lance CameraInterface2.awb_menu(...) (workflow “feuille blanche”).
#
#  Tests GPIO / matériel :
#     - test_anneau_lumineux()
#         Lance anneau_lumineux.main() (auto relance sudo si nécessaire).
#     - test_tft(duration) / test_tft_text(message, duration=5)
#         Tests écran TFT (via ecran.tft.*).
#     - test_moteur() / test_mouvements_robot()
#         Tests servos (robot_servo.hardware_test / manual_singmaster_loop_cubotino).
#
#  Utilitaires :
#     - cleanup_tmp_files(confirm=True) / confirm_cleanup()
#         Nettoyage dossier tmp en conservant {F,R,B,L,U,D}.jpg.
#     - get_available_faces()
#         Liste faces présentes / manquantes dans tmp.
#     - get_system_info()
#         Résume chemins + présence calibrations + nombre de fichiers tmp.
#
#  Exécution directe (__main__) :
#     - Démonstrations : statut calibration, processing, solve+url, infos système.
# ============================================================================


=======
# rubiks_operations.py - Module des opérations Rubik's Cube
# ============================================================================
# RÉSUMÉ : Module abstrait qui définit toutes les opérations disponibles
#          pour le système de reconnaissance et résolution du Rubik's Cube.
#          
# OBJECTIF : Séparer la logique métier de l'interface utilisateur pour permettre :
#            - Un mode texte/CLI
#            - Un GUI personnalisé (Tkinter, PyQt, web, etc.)
#            - Une API REST
#            - Des tests unitaires
#
# ARCHITECTURE :
#   - Toutes les fonctions retournent des dictionnaires standardisés
#   - Gestion des erreurs avec try/except
#   - Documentation complète de chaque fonction
#   - Aucune interaction directe avec l'utilisateur (input/print minimal)
#   - Paramètres explicites pour tous les modes de fonctionnement
#
# UTILISATION :
#   from rubiks_operations import RubiksOperations
#   
#   ops = RubiksOperations()
#   result = ops.calibrate_zones()
#   if result['success']:
#       print(result['data'])
#   else:
#       print(result['error'])
# ============================================================================

>>>>>>> screen-gui
import os
import glob
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
<<<<<<< HEAD
import traceback
=======

>>>>>>> screen-gui

class DebugMode(Enum):
    """Modes de debug disponibles"""
    NONE = "none"      # Silencieux
    TEXT = "text"      # Texte uniquement
    BOTH = "both"      # Texte + graphique
    GRAPHICAL = "graphical"  # Graphique uniquement


class ProcessingMode(Enum):
    """Modes de traitement disponibles"""
    ROBOT = "robot"           # Mode robot complet
    ROBOT_RAW = "robot_raw"   # Mode robot sans résolution
    PRODUCTION = "production" # Mode production avec debug
    TEST = "test"             # Mode test


@dataclass
class OperationResult:
    """Structure standardisée pour les résultats d'opération"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CalibrationStatus:
    """État de la calibration"""
    roi_calibrated: bool
    roi_faces_count: int
    roi_faces: List[str]
    roi_missing_faces: List[str]
    colors_calibrated: bool
    colors_count: int
    colors_list: List[str]


class RubiksOperations:
    """
    Classe principale qui encapsule toutes les opérations du système Rubik's Cube.
    
    Cette classe sépare la logique métier de l'interface utilisateur, permettant
    une réutilisation facile dans différents contextes (CLI, GUI, API).
    """

    def __init__(self, tmp_folder: str = "tmp", config_folder: str = "."):
        """
        Initialise le gestionnaire d'opérations.
        
        Args:
            tmp_folder: Dossier contenant les images temporaires
            config_folder: Dossier contenant les fichiers de configuration
        """
        self.tmp_folder = tmp_folder
        self.config_folder = config_folder
        self.roi_calibration_file = os.path.join(config_folder, "rubiks_calibration.json")
        self.color_calibration_file = os.path.join(config_folder, "rubiks_color_calibration.json")

    # ========================================================================
    # CALIBRATION
    # ========================================================================

    def calibrate_zones_interactive(self) -> Dict:
        """
        Lance la calibration interactive des zones ROI.
        
        Returns:
            Dict avec success, data (nombre de faces calibrées), error
        """
        try:
            from calibration_roi import calibration_menu
            calibration_menu()
            return OperationResult(
                success=True,
                message="Calibration des zones terminée"
            ).to_dict()
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la calibration des zones: {str(e)}"
            ).to_dict()

    def calibrate_colors_interactive(self) -> Dict:
        """
        Lance la calibration interactive des couleurs.
        
        Returns:
            Dict avec success, data (couleurs calibrées), error
        """
        try:
<<<<<<< HEAD
            from calibration_colors import calibrate_colors_interactive
=======
            from process_images_cube import calibrate_colors_interactive
>>>>>>> screen-gui
            calibrate_colors_interactive()
            return OperationResult(
                success=True,
                message="Calibration des couleurs terminée"
            ).to_dict()
        except Exception as e:
<<<<<<< HEAD
            import traceback
            traceback.print_exc()
            tb = traceback.format_exc()
            return OperationResult(
                success=False,
                error=f"Erreur lors de la calibration des couleurs: {e}\n\nTRACEBACK:\n{tb}"
=======
            return OperationResult(
                success=False,
                error=f"Erreur lors de la calibration des couleurs: {str(e)}"
>>>>>>> screen-gui
            ).to_dict()

    def get_calibration_status(self) -> Dict:
        """
        Récupère l'état complet de la calibration.
        
        Returns:
            Dict avec success, data (CalibrationStatus), error
        """
        try:
            from calibration_rubiks import get_calibration_stats, load_calibration
<<<<<<< HEAD
            from calibration_colors import load_color_calibration
=======
            from process_images_cube import load_color_calibration
>>>>>>> screen-gui

            stats = get_calibration_stats()
            roi_data = load_calibration()
            color_data = load_color_calibration()

            # Analyse ROI
            roi_calibrated = roi_data is not None and len(roi_data) > 0
            roi_faces = list(roi_data.keys()) if roi_data else []
            all_faces = ['F', 'R', 'B', 'L', 'U', 'D']
            roi_missing = [f for f in all_faces if f not in roi_faces]

            # Analyse couleurs
            colors_calibrated = color_data is not None and len(color_data) > 0
            colors_list = list(color_data.keys()) if color_data else []

            status = CalibrationStatus(
                roi_calibrated=roi_calibrated,
                roi_faces_count=len(roi_faces),
                roi_faces=roi_faces,
                roi_missing_faces=roi_missing,
                colors_calibrated=colors_calibrated,
                colors_count=len(colors_list),
                colors_list=colors_list
            )

            return OperationResult(
                success=True,
                data=asdict(status),
                metadata=stats
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la récupération du statut: {str(e)}"
            ).to_dict()

    def load_roi_calibration(self) -> Dict:
        """
        Charge les données de calibration ROI.
        
        Returns:
            Dict avec success, data (dict des ROI par face), error
        """
        try:
            from calibration_rubiks import load_calibration
            roi_data = load_calibration()
            
            if roi_data is None:
                return OperationResult(
                    success=False,
                    error="Aucune calibration ROI trouvée"
                ).to_dict()
            
            return OperationResult(
                success=True,
                data=roi_data
            ).to_dict()
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du chargement de la calibration ROI: {str(e)}"
            ).to_dict()

    def load_color_calibration(self) -> Dict:
        """
        Charge les données de calibration des couleurs.
        
        Returns:
            Dict avec success, data (dict des couleurs), error
        """
        try:
<<<<<<< HEAD
            from calibration_colors  import load_color_calibration
=======
            from process_images_cube import load_color_calibration
>>>>>>> screen-gui
            color_data = load_color_calibration()
            
            if color_data is None:
                return OperationResult(
                    success=False,
                    error="Aucune calibration des couleurs trouvée"
                ).to_dict()
            
            return OperationResult(
                success=True,
                data=color_data
            ).to_dict()
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du chargement de la calibration des couleurs: {str(e)}"
            ).to_dict()

    # ========================================================================
    # PRODUCTION ET TRAITEMENT
    # ========================================================================

    def process_rubiks_cube(self, debug: str = "text") -> Dict:
        """
        Traite les 6 faces du cube et génère le code Singmaster.
        
        Args:
            debug: Mode de debug ("none", "text", "both")
            
        Returns:
            Dict avec success, data (singmaster code), error
        """
        try:
            from calibration_rubiks import load_calibration
<<<<<<< HEAD
            from calibration_colors import load_color_calibration
=======
            from process_images_cube import load_color_calibration
>>>>>>> screen-gui
            from processing_rubiks import production_mode

            # Vérification des calibrations
            roi_data = load_calibration()
            if roi_data is None:
                return OperationResult(
                    success=False,
                    error="Aucune calibration ROI trouvée. Calibrez d'abord les zones."
                ).to_dict()

            color_calibration = load_color_calibration()
            if color_calibration is None:
                return OperationResult(
                    success=False,
                    error="Aucune calibration des couleurs trouvée. Calibrez d'abord les couleurs."
                ).to_dict()

            # Traitement
            result = production_mode(roi_data, color_calibration, debug=debug)
            
            return OperationResult(
                success=result["success"],
                data={
                    "singmaster": result.get("singmaster"),
                    "faces": result.get("faces", {})
                },
                error=result.get("error"),
                message="Code Singmaster généré avec succès" if result["success"] else "Échec de la génération"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du traitement: {str(e)}"
            ).to_dict()

    def process_api_mode(self, debug: str = "text") -> Dict:
        """
        Traite le cube en mode API (sans interface).
        
        Args:
            debug: Mode de debug ("none", "text", "both")
            
        Returns:
            Dict avec success, data (singmaster), error
        """
        try:
            from processing_rubiks import process_rubiks_to_singmaster
            result = process_rubiks_to_singmaster(debug=debug)
            
            return OperationResult(
                success=result["success"],
                data={"singmaster": result.get("singmaster")},
                error=result.get("error")
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur en mode API: {str(e)}"
            ).to_dict()

    def quick_pipeline_test(self, mode: str = "robot_raw", debug: str = "text") -> Dict:
        """
        Test rapide du pipeline avec encodage corrigé.
        
        Args:
            mode: Mode de traitement ("robot_raw", "robot", etc.)
            debug: Mode de debug
            
        Returns:
            Dict avec success, data, error
        """
        try:
            from processing_rubiks import quick_pipeline_test_corrected
            success = quick_pipeline_test_corrected(self.tmp_folder, debug=debug, mode=mode)
            
            return OperationResult(
                success=success,
                message="Pipeline rapide exécuté avec succès" if success else "Échec du pipeline rapide"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du test rapide: {str(e)}"
            ).to_dict()

    # ========================================================================
    # DEBUG
    # ========================================================================

    def debug_single_face(self, face: str) -> Dict:
        """
        Analyse détaillée d'une face spécifique.
        
        Args:
            face: Face à analyser (F, R, B, L, U, D)
            
        Returns:
            Dict avec success, data (analyse de la face), error
        """
        try:
<<<<<<< HEAD
            from calibration_rubiks import load_calibration, load_color_calibration
            from process_images_cube import test_single_face_debug
=======
            from calibration_rubiks import load_calibration
            from process_images_cube import load_color_calibration, test_single_face_debug
>>>>>>> screen-gui

            face = face.upper()
            if face not in ['F', 'R', 'B', 'L', 'U', 'D']:
                return OperationResult(
                    success=False,
                    error=f"Face invalide: {face}. Utilisez F, R, B, L, U ou D"
                ).to_dict()

            roi_data = load_calibration()
            if roi_data is None or face not in roi_data:
                return OperationResult(
                    success=False,
                    error=f"Face {face} non calibrée"
                ).to_dict()

            color_calibration = load_color_calibration()
            test_single_face_debug(face, roi_data[face], color_calibration)

            return OperationResult(
                success=True,
                message=f"Analyse de la face {face} terminée"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du debug de la face: {str(e)}"
            ).to_dict()

    def debug_color_mapping(self) -> Dict:
        """
        Diagnostic du mapping des couleurs.
        
        Returns:
            Dict avec success, data, error
        """
        try:
            from processing_rubiks import debug_color_mapping
            debug_color_mapping(self.tmp_folder)
            
            return OperationResult(
                success=True,
                message="Diagnostic couleur terminé"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du diagnostic couleur: {str(e)}"
            ).to_dict()

    def debug_vision_and_rotations(self) -> Dict:
        """
        Debug complet de la vision et des rotations.
        
        Returns:
            Dict avec success, message, error
        """
        try:
            from processing_rubiks import full_debug_pipeline
            full_debug_pipeline()
            
            return OperationResult(
                success=True,
                message="Debug vision et rotations terminé"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du debug vision: {str(e)}"
            ).to_dict()

    # ========================================================================
    # SOLVEUR
    # ========================================================================

    def solve_cube(self, cubestring: str) -> Dict:
        """
        Résout un cube à partir d'une chaîne Singmaster.
        
        Args:
            cubestring: Chaîne de 54 caractères représentant le cube
            
        Returns:
            Dict avec success, data (solution), error
        """
        try:
            from solver_wrapper import solve_cube
            
            if len(cubestring) != 54:
                return OperationResult(
                    success=False,
                    error=f"Chaîne invalide: {len(cubestring)} caractères au lieu de 54"
                ).to_dict()

            solution = solve_cube(cubestring)
            
            return OperationResult(
                success=True,
                data={"solution": solution, "cubestring": cubestring}
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la résolution: {str(e)}"
            ).to_dict()

    def solve_and_get_url(self, cubestring: str, method: str = "kociemba", 
                          site: str = "alg") -> Dict:
        """
        Résout un cube et génère une URL de visualisation.
        
        Args:
            cubestring: Chaîne de 54 caractères
            method: Méthode de résolution ("kociemba", etc.)
            site: Site de visualisation ("alg", "twizzle", etc.)
            
        Returns:
            Dict avec success, data (solution, url), error
        """
        try:
            from solver_wrapper import solve_cube
            from url_convertor import convert_to_url

            if len(cubestring) != 54:
                return OperationResult(
                    success=False,
                    error=f"Chaîne invalide: {len(cubestring)} caractères au lieu de 54"
                ).to_dict()

            solution = solve_cube(cubestring)
            url = convert_to_url(solution, method=method, site=site)
            
            return OperationResult(
                success=True,
                data={
                    "solution": solution,
                    "url": url,
                    "cubestring": cubestring
                }
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la résolution et génération d'URL: {str(e)}"
            ).to_dict()

    # ========================================================================
    # MODE ROBOT
    # ========================================================================

<<<<<<< HEAD
    def run_robot_mode(self, do_solve: bool = True, do_execute: bool = False,
=======
    def run_robot_mode(self, do_solve: bool = True, do_execute: bool = True,
>>>>>>> screen-gui
                       debug: str = "text") -> Dict:
        """
        Exécute le pipeline complet en mode robot.
        
        Args:
            do_solve: Si True, résout le cube
            do_execute: Si True, exécute les mouvements
            debug: Mode de debug
            
        Returns:
            Dict avec success, data (cubestring, solution), error
        """
        try:
            from robot_solver import RobotCubeSolver
<<<<<<< HEAD
            from progress_listeners import console_clean_listener, jsonl_file_listener, multi_listener
            from tft_driver import ConsoleTFTFile
            from tft_listener import make_tft_listener
            tft = ConsoleTFTFile(path=f"{self.tmp_folder}/tft_screen.txt", width=24) # METTRE ICI LE BON DRIVER ECRAN en attendant on écrit dans une console
            tft_listener = make_tft_listener(tft, min_refresh_s=0.15, max_line_len=24)
            file_listener = jsonl_file_listener(folder=self.tmp_folder, prefix="progress")
            listeners = [console_clean_listener, file_listener,tft_listener]
            listener = multi_listener(*listeners)
            solver = RobotCubeSolver(image_folder=self.tmp_folder, debug=debug)
            result  = solver.run(do_solve=do_solve, do_execute=do_execute,progress_callback=listener)
            if do_solve:
                cubestring, solution = result
            else:
                cubestring, solution = result, ""
=======
            
            solver = RobotCubeSolver(image_folder=self.tmp_folder, debug=debug)
            cubestring = solver.run(do_solve=do_solve, do_execute=do_execute)
            
>>>>>>> screen-gui
            return OperationResult(
                success=True,
                data={
                    "cubestring": cubestring,
<<<<<<< HEAD
                    "solution": solution,
                    "log_jsonl": getattr(file_listener, "path", None),  # chemin du fichier jsonl
                    "solved": do_solve,
                    "executed": do_execute
                },
                message="Pipeline robot terminé"
=======
                    "solved": do_solve,
                    "executed": do_execute
                },
                message="Pipeline robot terminé avec succès"
>>>>>>> screen-gui
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur en mode robot: {str(e)}"
            ).to_dict()

    # ========================================================================
    # CAPTURE D'IMAGES
    # ========================================================================

<<<<<<< HEAD
    def capture_images_robot(self, rotation: int = 0, folder: str = "", debug: str = "text") -> Dict:
        try:
            from robot_solver import RobotCubeSolver
            from capture_photo_from_311 import CameraInterface2
            from robot_servo import reset_initial, flip_up

        # 1) dossier de sortie (si folder == "" => pas de sous-dossier)
            out_dir = self.tmp_folder if not folder else os.path.join(self.tmp_folder, folder)
            os.makedirs(out_dir, exist_ok=True)

            camera = CameraInterface2(rotation=rotation) if "rotation" in CameraInterface2.__init__.__code__.co_varnames else CameraInterface2()

            # 2) init solver
            solver = RobotCubeSolver(image_folder=out_dir, debug=debug, camera=camera)

            # callback: 1 flip "x"
            def flip_cb():
                flip_up()

            # 3) série: LEDs ON + lock caméra + capture faces + cleanup
            camera.leds_on_for_scan()  # -> à implémenter/mapper vers ta fonction LEDs
            # ✅ IMPORTANT : remettre le robot dans une pose connue AVANT le lock
            reset_initial()

            # ✅ Pré-lock multiface : 4 flips -> retour état initial
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
            camera.lock_for_scan_multiface_cfg(flip_cb=flip_cb,debug=True)

            solver.capture_all_faces()  # -> doit écrire U.jpg, R.jpg, F.jpg... dans out_dir
            
            camera.leds_off()                # -> à implémenter/mapper
            camera.close()                   # -> important sur RPi (picam2)

            return OperationResult(success=True, message="Prises de photos terminées avec succès avec robot").to_dict()

        except Exception as e:
            # Cleanup best-effort (ne jamais planter sur le cleanup)
            print("❌ ERREUR lors de la capture des images:")
            print(traceback.format_exc())            
            try:
                camera.leds_off()
            except Exception:
                pass
            try:
                camera.close()
            except Exception:
                pass

            return OperationResult(success=False, error=f"Erreur en mode robot + photos: {str(e)}").to_dict()


=======
>>>>>>> screen-gui
    def capture_images(self, rotation: int = 0, folder: str = "captures") -> Dict:
        """
        Capture des images depuis la caméra.
        
        Args:
            rotation: Rotation à appliquer aux images (0, 90, 180, 270)
            folder: Dossier de destination
            
        Returns:
            Dict avec success, data (liste des fichiers), error
        """
        try:
<<<<<<< HEAD
            from capture_photo_from_311 import CameraInterface2
            camera = CameraInterface2()
            
            output = camera.capture_loop(rotation=rotation, folder=folder)
=======
            from capture_photo_from_311 import capture_loop
            
            output = capture_loop(rotation=rotation, folder=folder)
>>>>>>> screen-gui
            
            if output:
                return OperationResult(
                    success=True,
                    data={"files": output, "folder": folder},
                    message=f"Images capturées dans {folder}"
                ).to_dict()
            else:
                return OperationResult(
                    success=False,
                    error="Échec de la capture d'images"
                ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la capture: {str(e)}"
            ).to_dict()

    def capture_single_image(self, rotation: int = 0, folder: str = "captures") -> Dict:
        """
        Capture une seule image.
        """
        try:
            from capture_photo_from_311 import capture_image
            import os, datetime

            os.makedirs(folder, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            filepath = os.path.join(folder, f"capture_{ts}.jpg")   # ✅ on crée le chemin complet ici

            path = capture_image(filename=filepath, rotation=rotation)      # ✅ on passe le bon paramètre
            if path and os.path.exists(path):
                return OperationResult(
                    success=True,
                    data={"file": path},
                    message=f"Image capturée: {path}"
                ).to_dict()
            else:
                return OperationResult(
                    success=False,
                    error="Échec de la capture"
                ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la capture: {str(e)}"
            ).to_dict()

<<<<<<< HEAD
    # ========================================================================
    # Calibration des blancs
    # ========================================================================
    def calibrate_blancs(self):
        try:
            from capture_photo_from_311 import CameraInterface2
            camera = CameraInterface2()
            camera.awb_menu(rotation=0, folder="tmp")
            
            return OperationResult(
                success=True,
                message="Calibration des blancs terminé avec succès"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur calibration blancs: {str(e)}"
            ).to_dict()
=======

>>>>>>> screen-gui
    # ========================================================================
    # TESTS GPIO (ANNEAU LUMINEUX, MOTEUR, ETC.)
    # ========================================================================

    def test_anneau_lumineux(self) -> Dict:
        """
        Lance le menu interactif de l’anneau lumineux (NeoPixel Ring).
        Si le script n’est pas exécuté en sudo, relance automatiquement
        le module en sudo pour permettre l’accès au GPIO18.
        """
        import os, sys, subprocess, importlib

        try:
            # Vérifie si on est en sudo (uid=0)
            if os.geteuid() != 0:
                print("⚙️  Relance automatique du test de l’anneau lumineux avec sudo...")
                # Re-lance Python avec sudo dans le même dossier
                cmd = [
                    "sudo",
                    sys.executable,
                    "-m", "anneau_lumineux"
                ]
                subprocess.run(cmd, check=True)
                return OperationResult(
                    success=True,
                    message="Test de l’anneau lumineux exécuté avec sudo"
                ).to_dict()

            # Si déjà root, on peut importer directement
            import anneau_lumineux
            importlib.reload(anneau_lumineux)

            if hasattr(anneau_lumineux, "main"):
                print("\n🔌 Test GPIO : lancement du menu de l’anneau lumineux (Ctrl+C pour revenir)")
                anneau_lumineux.main()
                return OperationResult(
                    success=True,
                    message="Test de l’anneau lumineux terminé"
                ).to_dict()
            else:
                return OperationResult(
                    success=False,
                    error="Le module 'anneau_lumineux' ne contient pas de fonction main()."
                ).to_dict()

        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de l’exécution avec sudo : {e}"
            ).to_dict()
        except KeyboardInterrupt:
            return OperationResult(
                success=True,
                message="Interruption utilisateur (retour au menu principal)"
            ).to_dict()
        except ModuleNotFoundError:
            return OperationResult(
                success=False,
                error="Module 'anneau_lumineux' introuvable. Vérifie sa présence dans le projet."
            ).to_dict()
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du test de l’anneau lumineux: {str(e)}"
            ).to_dict()

<<<<<<< HEAD
    def test_tft(self, duration: int) -> Dict:
        """
        Lance l'affichage du GIF sur le TFT pendant X secondes.
        """
        try:
            from ecran.tft import display_gif
            display_gif(duration)

            return OperationResult(
                success=True,
                message=f"Affichage TFT pendant {duration} secondes terminé."
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur TFT : {str(e)}"
            ).to_dict()

    def test_tft_text(self, message: str, duration: int = 5) -> Dict:
        """
        Affiche un texte sur le TFT pendant X secondes.
        """
        try:
            from ecran.tft import display_text
            display_text(message, duration)

            return OperationResult(
                success=True,
                message=f"Texte affiché : '{message}' pendant {duration} sec"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur TFT (texte) : {str(e)}"
            ).to_dict()

    def test_moteur(self) -> Dict:
        """
        Lance les tests du moteur
        """
        import os, sys, subprocess, importlib

        try:
            from robot_servo import hardware_test
            hardware_test()
            return OperationResult(
                success=True,
                message="Succès test moteur"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du test moteur: {str(e)}"
            ).to_dict()

    def test_mouvements_robot(self) -> Dict:
        """
        Lance les tests du moteur
        """
        try:
            from robot_servo import manual_singmaster_loop_cubotino
            manual_singmaster_loop_cubotino()
            return OperationResult(
                success=True,
                message="Fin tests moteur"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du test moteur: {str(e)}"
            ).to_dict()            
=======
>>>>>>> screen-gui

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def cleanup_tmp_files(self, confirm: bool = True) -> Dict:
        """
        Nettoie les fichiers temporaires en gardant les originaux.
        
        Args:
            confirm: Si True, demande confirmation (pour mode interactif)
            
        Returns:
            Dict avec success, data (stats), error
        """
        try:
            original_files = ["F.jpg", "R.jpg", "B.jpg", "L.jpg", "U.jpg", "D.jpg"]
            original_paths = [os.path.join(self.tmp_folder, f) for f in original_files]

            if not os.path.exists(self.tmp_folder):
                return OperationResult(
                    success=False,
                    error=f"Le dossier {self.tmp_folder} n'existe pas"
                ).to_dict()

            all_files = glob.glob(os.path.join(self.tmp_folder, "*"))
            files_to_delete = []
            files_kept = []

            for file_path in all_files:
                if os.path.isfile(file_path):
                    if file_path in original_paths:
                        files_kept.append(os.path.basename(file_path))
                    else:
                        files_to_delete.append(file_path)

            if not files_to_delete:
                return OperationResult(
                    success=True,
                    data={
                        "deleted": 0,
                        "kept": len(files_kept),
                        "files_kept": files_kept
                    },
                    message="Aucun fichier temporaire à supprimer"
                ).to_dict()

            # Si pas de confirmation requise, on supprime directement
            if not confirm:
                deleted_count = 0
                failed_count = 0

                for file_path in files_to_delete:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception:
                        failed_count += 1

                return OperationResult(
                    success=True,
                    data={
                        "deleted": deleted_count,
                        "failed": failed_count,
                        "kept": len(files_kept),
                        "files_kept": files_kept
                    },
                    message=f"{deleted_count} fichier(s) supprimé(s)"
                ).to_dict()

            # Sinon, on retourne la liste pour confirmation
            return OperationResult(
                success=True,
                data={
                    "to_delete": len(files_to_delete),
                    "to_keep": len(files_kept),
                    "files_to_delete": [os.path.basename(f) for f in files_to_delete],
                    "files_kept": files_kept
                },
                message=f"{len(files_to_delete)} fichier(s) à supprimer"
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors du nettoyage: {str(e)}"
            ).to_dict()

    def confirm_cleanup(self) -> Dict:
        """
        Exécute le nettoyage après confirmation.
        Utilisé en mode interactif après cleanup_tmp_files(confirm=True).
        
        Returns:
            Dict avec success, data (stats de suppression), error
        """
        return self.cleanup_tmp_files(confirm=False)

    def get_available_faces(self) -> Dict:
        """
        Liste les faces disponibles dans le dossier tmp.
        
        Returns:
            Dict avec success, data (liste des faces), error
        """
        try:
            faces = ['F', 'R', 'B', 'L', 'U', 'D']
            available = []
            missing = []

            for face in faces:
                face_path = os.path.join(self.tmp_folder, f"{face}.jpg")
                if os.path.exists(face_path):
                    available.append(face)
                else:
                    missing.append(face)

            return OperationResult(
                success=True,
                data={
                    "available": available,
                    "missing": missing,
                    "total": len(available)
                }
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la vérification des faces: {str(e)}"
            ).to_dict()

    def get_system_info(self) -> Dict:
        """
        Récupère les informations système.
        
        Returns:
            Dict avec success, data (infos système), error
        """
        try:
            info = {
                "tmp_folder": self.tmp_folder,
                "config_folder": self.config_folder,
                "roi_calibration_exists": os.path.exists(self.roi_calibration_file),
                "color_calibration_exists": os.path.exists(self.color_calibration_file),
                "tmp_folder_exists": os.path.exists(self.tmp_folder)
            }

            # Compte les fichiers dans tmp
            if os.path.exists(self.tmp_folder):
                tmp_files = len([f for f in os.listdir(self.tmp_folder) 
                               if os.path.isfile(os.path.join(self.tmp_folder, f))])
                info["tmp_files_count"] = tmp_files

            return OperationResult(
                success=True,
                data=info
            ).to_dict()

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Erreur lors de la récupération des infos système: {str(e)}"
            ).to_dict()


# ============================================================================
# FONCTIONS D'AIDE POUR L'UTILISATION EN MODE SCRIPT
# ============================================================================

def create_operations(tmp_folder: str = "tmp", config_folder: str = ".") -> RubiksOperations:
    """
    Factory function pour créer une instance de RubiksOperations.
    
    Args:
        tmp_folder: Dossier des images temporaires
        config_folder: Dossier de configuration
        
    Returns:
        Instance de RubiksOperations
    """
    return RubiksOperations(tmp_folder=tmp_folder, config_folder=config_folder)


def print_result(result: Dict, verbose: bool = True):
    """
    Affiche un résultat d'opération de manière formatée.
    
    Args:
        result: Dictionnaire de résultat
        verbose: Si True, affiche tous les détails
    """
    if result["success"]:
        print(f"✅ SUCCÈS: {result.get('message', 'Opération réussie')}")
        if verbose and result.get("data"):
            print(f"Données: {result['data']}")
    else:
        print(f"❌ ÉCHEC: {result.get('error', 'Erreur inconnue')}")


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    # Création de l'instance
    ops = RubiksOperations()
    
    # Exemple 1: Vérifier le statut
    print("=== STATUT DE CALIBRATION ===")
    status = ops.get_calibration_status()
    print_result(status)
    
    # Exemple 2: Traiter le cube
    print("\n=== TRAITEMENT DU CUBE ===")
    result = ops.process_rubiks_cube(debug="text")
    print_result(result)
    
    # Exemple 3: Résoudre un cube
    print("\n=== RÉSOLUTION ===")
    cubestring = "UUUUUULLLURRURRFFFFFFFFFLLDDDRDDRDDRLLDLLDBBBBBBBBBURR"
    solve_result = ops.solve_and_get_url(cubestring)
    print_result(solve_result)
    
    # Exemple 4: Info système
    print("\n=== INFORMATIONS SYSTÈME ===")
    info = ops.get_system_info()
    print_result(info)