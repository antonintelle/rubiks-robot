#!/usr/bin/env python3
# =============================================================================
# text_gui.py - Interface texte principale du système Rubik's Cube
# =============================================================================
# RÉSUMÉ :
#   Interface texte moderne et modulaire pour piloter toutes les opérations du
#   système de reconnaissance, de calibration, de vision, de conversion Kociemba,
#   de résolution et de pilotage robotisé du Rubik's Cube.
#
#   Cette version repose sur le module `rubiks_operations` pour exécuter les
#   traitements réels, séparant ainsi la logique métier de l’interface utilisateur.
#
#   Structure du menu :
#   ---------------------------------------------------------------------------
#       [CALIBRATION]
#           c1 - Statut des calibrations
#           c2 - Calibration des couleurs
#           c3 - Calibration des zones (ROI)
#       [CAPTURE]
#           i1 - Capture d'images
#       [VISION]
#           v1 - Diagnostic couleurs
#           v2 - Debug vision et rotations
#           v3 - Debug face spécifique
#       [CONVERSION KOCIEMBA]
#           k1 - Traiter le cube (mode graphique)
#           k2 - Traiter le cube (mode texte)
#           k3 - Traiter le cube (mode silencieux)
#           k4 - Mode API debug
#       [RESOLUTION]
#           r1 - Résoudre un cube seul (chaîne)
#       [PIPELINE]
#           p1 - Test pipeline rapide
#           p2 - Mode robot complet
#       [TESTS GPIO]
#           g1 - Lancer le menu de l’anneau lumineux
#       [MOUVEMENTS ROBOT]
#           (vide)
#       [ROBOT]
#           (vide)
#       [UTILITAIRES]
#           u1 - Nettoyer fichiers temporaires
#           u2 - Informations système
#           u3 - Voir l'historique
#           q  - Quitter
#
# =============================================================================
# AUTEUR  : Projet Rubik's Cube
# VERSION : 2.1
# DATE    : 2025-10-25
# =============================================================================

import sys
import os
from colorama import init, Fore, Style
from datetime import datetime
from typing import Dict

from rubiks_operations import RubiksOperations

# Initialisation couleur terminal
init(autoreset=True)


# =============================================================================
# AFFICHAGE FORMATÉ
# =============================================================================
class Display:
    @staticmethod
    def header(title: str):
        print("\n" + Fore.CYAN + "=" * 70)
        print(Fore.YELLOW + Style.BRIGHT + title.center(70))
        print(Fore.CYAN + "=" * 70 + Style.RESET_ALL)

    @staticmethod
    def section(text: str):
        print(Fore.CYAN + "\n" + "─" * 70)
        print(Fore.YELLOW + f"▶ {text}")
        print(Fore.CYAN + "─" * 70 + Style.RESET_ALL)

    @staticmethod
    def success(msg: str): print(Fore.GREEN + f"✅ {msg}" + Style.RESET_ALL)
    @staticmethod
    def error(msg: str): print(Fore.RED + f"❌ {msg}" + Style.RESET_ALL)
    @staticmethod
    def warning(msg: str): print(Fore.YELLOW + f"⚠️  {msg}" + Style.RESET_ALL)
    @staticmethod
    def info(msg: str): print(Fore.CYAN + f"ℹ️  {msg}" + Style.RESET_ALL)
    @staticmethod
    def prompt(text: str) -> str: return input(Fore.YELLOW + f"\n➤ {text}: " + Style.RESET_ALL).strip()

    @staticmethod
    def result_data(data: Dict, indent: int = 2):
        prefix = " " * indent
        for k, v in data.items():
            if isinstance(v, dict):
                print(f"{prefix}{Fore.CYAN}{k}:{Style.RESET_ALL}")
                Display.result_data(v, indent + 2)
            elif isinstance(v, list):
                print(f"{prefix}{Fore.CYAN}{k}:{Style.RESET_ALL} {', '.join(map(str, v))}")
            else:
                print(f"{prefix}{Fore.CYAN}{k}:{Style.RESET_ALL} {v}")


# =============================================================================
# HISTORIQUE
# =============================================================================
class HistoryManager:
    def __init__(self, path: str = "history.json"):
        self.path = path
        self.history = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                import json
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        import json
        try:
            with open(self.path, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            Display.error(f"Erreur sauvegarde historique: {e}")

    def add(self, operation: str, result: Dict):
        entry = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "operation": operation,
            "success": result.get("success", False),
            "error": result.get("error"),
            "message": result.get("message")
        }
        self.history.append(entry)
        self._save()

    def show(self, limit: int = 10):
        if not self.history:
            Display.info("Aucun historique disponible")
            return
        Display.section("HISTORIQUE DES OPÉRATIONS")
        for entry in self.history[-limit:][::-1]:
            ts = entry["timestamp"]
            status = "✅" if entry["success"] else "❌"
            print(f"{status} {ts} - {entry['operation']}")
            if entry["error"]:
                print(Fore.RED + f"   ⚠️  {entry['error']}" + Style.RESET_ALL)


# =============================================================================
# INTERFACE PRINCIPALE
# =============================================================================
class RubiksTextGUI:
    def __init__(self):
        self.ops = RubiksOperations()
        self.history = HistoryManager()
        self.running = True

    def show_main_menu(self):
        Display.header("SYSTÈME DE RECONNAISSANCE RUBIK'S CUBE")
        print(Fore.CYAN + "\nConfiguration initiale = CALIBRATION")
        print("PIPELINE = CAPTURE → VISION → CONVERSION KOCIEMBA → RESOLUTION → MOUVEMENTS ROBOT")
        print("ROBOT = Test complet du robot\n")

        print(Fore.MAGENTA + "[CALIBRATION]" + Style.RESET_ALL)
        print(" c1 - Statut des calibrations")
        print(" c2 - Calibration des couleurs")
        print(" c3 - Calibration des zones (ROI)")
        print(Fore.MAGENTA + "[CAPTURE]" + Style.RESET_ALL)
        print(" i1 - Capture d'images")
        print(Fore.MAGENTA + "[VISION]" + Style.RESET_ALL)
        print(" v1 - Diagnostic couleurs")
        print(" v2 - Debug vision et rotations")
        print(" v3 - Debug face spécifique")
        print(Fore.MAGENTA + "[CONVERSION KOCIEMBA]" + Style.RESET_ALL)
        print(" k1 - Traiter le cube (mode graphique)")
        print(" k2 - Traiter le cube (mode texte)")
        print(" k3 - Traiter le cube (mode silencieux)")
        print(" k4 - Mode API debug")
        print(Fore.MAGENTA + "[RESOLUTION]" + Style.RESET_ALL)
        print(" r1 - Résoudre un cube seul (chaîne)")
        print(Fore.MAGENTA + "[PIPELINE]" + Style.RESET_ALL)
        print(" p1 - Test pipeline rapide")
        print(" p2 - Mode robot complet")
        print(Fore.MAGENTA + "[TESTS GPIO]" + Style.RESET_ALL)
        print(" g1 - Lancer le menu de l’anneau lumineux")
        print(Fore.MAGENTA + "[MOUVEMENTS ROBOT]" + Style.RESET_ALL)
        print("   (vide)")
        print(Fore.MAGENTA + "[ROBOT]" + Style.RESET_ALL)
        print("   (vide)")
        print(Fore.MAGENTA + "[UTILITAIRES]" + Style.RESET_ALL)
        print(" u1 - Nettoyer fichiers temporaires")
        print(" u2 - Informations système")
        print(" u3 - Voir l'historique")
        print(" q  - Quitter")

    # -------------------------------------------------------------------------
    # HANDLERS
    # -------------------------------------------------------------------------
    def handle_calibration_status(self):
        Display.section("STATUT DES CALIBRATIONS")
        result = self.ops.get_calibration_status()
        self.history.add("Statut calibration", result)
        Display.result_data(result["data"]) if result["success"] else Display.error(result["error"])

    def handle_process_cube(self, debug: str):
        Display.section(f"TRAITEMENT DU CUBE - MODE {debug.upper()}")
        result = self.ops.process_rubiks_cube(debug)
        self.history.add(f"Process cube ({debug})", result)
        if result["success"]:
            Display.success("Code Singmaster généré avec succès")
            print(f"{Fore.CYAN}{result['data']['singmaster']}{Style.RESET_ALL}")
        else:
            Display.error(result["error"])

    def handle_debug_face(self):
        Display.section("DEBUG FACE SPÉCIFIQUE")
        face = Display.prompt("Quelle face analyser ? (F/R/B/L/U/D)").upper()
        result = self.ops.debug_single_face(face)
        self.history.add(f"Debug face {face}", result)
        Display.success(result["message"]) if result["success"] else Display.error(result["error"])

    def handle_solve_cube(self):
        Display.section("RÉSOLUTION D’UN CUBE")
        cube = Display.prompt("Chaîne Singmaster (54 caractères)")
        if len(cube) != 54:
            Display.error("Chaîne invalide")
            return
        url = Display.prompt("Générer URL de visualisation ? (o/n)").lower() in ["o", "oui", "y"]
        result = self.ops.solve_and_get_url(cube) if url else self.ops.solve_cube(cube)
        self.history.add("Résolution cube", result)
        Display.result_data(result["data"]) if result["success"] else Display.error(result["error"])

    def handle_gpio_ring(self):
        Display.section("TEST GPIO - ANNEAU LUMINEUX")
        result = self.ops.test_anneau_lumineux()
        self.history.add("Test GPIO - Anneau lumineux", result)
        if result["success"]:
            Display.success(result.get("message", "Test terminé"))
        else:
            Display.error(result.get("error", "Erreur inconnue"))

    def handle_cleanup_files(self):
            """Gère le nettoyage des fichiers temporaires avec affichage"""
            Display.section("NETTOYAGE FICHIERS TEMPORAIRES")
            result = self.ops.cleanup_tmp_files(confirm=True)
            self.history.add("Nettoyage fichiers", result)
            
            if not result["success"]:
                Display.error(result["error"])
                return
            
            data = result["data"]
            
            # Cas : Aucun fichier à supprimer
            if data.get("to_delete", 0) == 0:
                Display.success(result.get("message", "Aucun fichier à supprimer"))
                if data.get('files_kept'):
                    Display.info(f"Fichiers conservés ({len(data['files_kept'])}):")
                    for f in data['files_kept']:
                        print(f"  ✅ {f}")
                return
            
            # Afficher les fichiers à supprimer
            Display.warning(f"📁 {data['to_delete']} fichier(s) à supprimer")
            
            if data.get('files_to_delete'):
                print("\nFichiers qui seront supprimés:")
                for f in data['files_to_delete']:
                    print(f"  🗑️  {f}")
            
            if data.get('files_kept'):
                Display.info(f"\nFichiers conservés: {len(data['files_kept'])}")
                for f in data['files_kept']:
                    print(f"  ✅ {f}")
            
            # Demander confirmation
            confirm = Display.prompt("\nConfirmer la suppression ? (o/n)").lower()
            
            if confirm not in ["o", "oui", "y"]:
                Display.info("Nettoyage annulé")
                return
            
            # Supprimer
            result = self.ops.cleanup_tmp_files(confirm=False)
            if result["success"]:
                data = result["data"]
                Display.success(f"{data['deleted']} fichier(s) supprimé(s)")
                if data.get('failed', 0) > 0:
                    Display.warning(f"{data['failed']} fichier(s) non supprimé(s)")
            else:
                Display.error(result["error"])

    def handle_system_info(self):
        """Affiche les informations système"""
        Display.section("INFORMATIONS SYSTÈME")
        result = self.ops.get_system_info()
        self.history.add("Info système", result)
        
        if not result["success"]:
            Display.error(result["error"])
            return
        
        data = result["data"]
        
        # Dossiers
        print(f"\n{Fore.CYAN}📁 Dossiers:{Style.RESET_ALL}")
        print(f"  Temporaire    : {data['tmp_folder']}")
        print(f"  Configuration : {data['config_folder']}")
        
        # Calibrations
        print(f"\n{Fore.CYAN}⚙️  Calibrations:{Style.RESET_ALL}")
        roi_status = f"{Fore.GREEN}✅ Présent{Style.RESET_ALL}" if data['roi_calibration_exists'] else f"{Fore.RED}❌ Absent{Style.RESET_ALL}"
        color_status = f"{Fore.GREEN}✅ Présent{Style.RESET_ALL}" if data['color_calibration_exists'] else f"{Fore.RED}❌ Absent{Style.RESET_ALL}"
        print(f"  ROI      : {roi_status}")
        print(f"  Couleurs : {color_status}")
        
        # Dossier tmp
        print(f"\n{Fore.CYAN}📂 Dossier tmp:{Style.RESET_ALL}")
        tmp_status = f"{Fore.GREEN}✅ Existe{Style.RESET_ALL}" if data['tmp_folder_exists'] else f"{Fore.RED}❌ N'existe pas{Style.RESET_ALL}"
        print(f"  Statut   : {tmp_status}")
        if data.get('tmp_files_count') is not None:
            print(f"  Fichiers : {data['tmp_files_count']}")
        
        # Statut général
        print(f"\n{Fore.CYAN}📊 Statut:{Style.RESET_ALL}")
        if data['roi_calibration_exists'] and data['color_calibration_exists']:
            Display.success("Système prêt")
        else:
            Display.warning("Calibration(s) manquante(s)")
            if not data['roi_calibration_exists']:
                print("   → c3 pour calibrer ROI")
            if not data['color_calibration_exists']:
                print("   → c2 pour calibrer couleurs")


    def handle_calibrate_colors(self):
        """Calibration des couleurs avec affichage du résultat"""
        Display.section("CALIBRATION DES COULEURS")
        result = self.ops.calibrate_colors_interactive()
        self.history.add("Calib couleurs", result)
        if result["success"]:
            Display.success(result.get("message", "Calibration terminée"))
        else:
            Display.error(result.get("error", "Erreur lors de la calibration"))

    def handle_calibrate_zones(self):
        """Calibration des zones ROI avec affichage du résultat"""
        Display.section("CALIBRATION DES ZONES (ROI)")
        result = self.ops.calibrate_zones_interactive()
        self.history.add("Calib zones", result)
        if result["success"]:
            Display.success(result.get("message", "Calibration terminée"))
        else:
            Display.error(result.get("error", "Erreur lors de la calibration"))

    def handle_capture_images(self):
        """Capture d'images avec affichage du résultat"""
        Display.section("CAPTURE D'IMAGES")
        result = self.ops.capture_images()
        self.history.add("Capture images", result)
        if result["success"]:
            Display.success(result.get("message", "Capture terminée"))
            if result.get("data"):
                Display.result_data(result["data"])
        else:
            Display.error(result.get("error", "Erreur lors de la capture"))

    def handle_debug_color_mapping(self):
        """Diagnostic couleurs avec affichage du résultat"""
        Display.section("DIAGNOSTIC COULEURS")
        result = self.ops.debug_color_mapping()
        self.history.add("Diagnostic couleurs", result)
        if result["success"]:
            Display.success(result.get("message", "Diagnostic terminé"))
            if result.get("data"):
                Display.result_data(result["data"])
        else:
            Display.error(result.get("error", "Erreur lors du diagnostic"))

    def handle_debug_vision(self):
        """Debug vision et rotations avec affichage du résultat"""
        Display.section("DEBUG VISION ET ROTATIONS")
        result = self.ops.debug_vision_and_rotations()
        self.history.add("Debug vision", result)
        if result["success"]:
            Display.success(result.get("message", "Debug terminé"))
            if result.get("data"):
                Display.result_data(result["data"])
        else:
            Display.error(result.get("error", "Erreur lors du debug"))

    def handle_api_mode(self):
        """Mode API debug avec affichage du résultat"""
        Display.section("MODE API DEBUG")
        result = self.ops.process_api_mode()
        self.history.add("API debug", result)
        if result["success"]:
            Display.success("Traitement API terminé")
            if result.get("data"):
                Display.result_data(result["data"])
        else:
            Display.error(result.get("error", "Erreur en mode API"))

    def handle_quick_pipeline_test(self):
        """Test pipeline rapide avec affichage du résultat"""
        Display.section("TEST PIPELINE RAPIDE")
        result = self.ops.quick_pipeline_test()
        self.history.add("Test pipeline", result)
        if result["success"]:
            Display.success(result.get("message", "Test terminé"))
            if result.get("data"):
                Display.result_data(result["data"])
        else:
            Display.error(result.get("error", "Erreur lors du test"))

    def handle_robot_mode(self):
        """Mode robot complet avec affichage du résultat"""
        Display.section("MODE ROBOT COMPLET")
        result = self.ops.run_robot_mode()
        self.history.add("Mode robot", result)
        if result["success"]:
            Display.success(result.get("message", "Mode robot terminé"))
            if result.get("data"):
                Display.result_data(result["data"])
        else:
            Display.error(result.get("error", "Erreur en mode robot"))

    # -------------------------------------------------------------------------
    # BOUCLE PRINCIPALE
    # -------------------------------------------------------------------------
    def run(self):
        while self.running:
            try:
                self.show_main_menu()
                choice = Display.prompt("Choisir une option").lower()

                if choice == "c1": self.handle_calibration_status()
                elif choice == "c2": self.handle_calibrate_colors()
                elif choice == "c3": self.handle_calibrate_zones()
                elif choice == "i1": self.handle_capture_images()
                elif choice == "v1": self.handle_debug_color_mapping()
                elif choice == "v2": self.handle_debug_vision()
                elif choice == "v3": self.handle_debug_face()
                elif choice == "k1": self.handle_process_cube("both")
                elif choice == "k2": self.handle_process_cube("text")
                elif choice == "k3": self.handle_process_cube("none")
                elif choice == "k4": self.handle_api_mode()
                elif choice == "r1": self.handle_solve_cube()
                elif choice == "p1": self.handle_quick_pipeline_test()
                elif choice == "p2": self.handle_robot_mode()
                elif choice == "g1": self.handle_gpio_ring()
                elif choice == "u1": self.handle_cleanup_files()
                elif choice == "u2": self.handle_system_info()
                elif choice == "u3": self.history.show()
                elif choice in ["q", "quit", "exit"]:
                    Display.info("Au revoir 👋")
                    self.running = False
                else:
                    Display.error("Option non reconnue")

                if self.running:
                    input(Fore.CYAN + "\nAppuyez sur Entrée pour continuer..." + Style.RESET_ALL)

            except KeyboardInterrupt:
                Display.warning("Interruption détectée (Ctrl+C)")
                if Display.prompt("Quitter ? (o/n)").lower() in ["o", "oui", "y"]:
                    self.running = False
            except Exception as e:
                Display.error(f"Erreur inattendue: {e}")
                import traceback
                print(traceback.format_exc())
                input(Fore.CYAN + "\nAppuyez sur Entrée pour continuer..." + Style.RESET_ALL)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================
def main():
    app = RubiksTextGUI()
    app.run()


if __name__ == "__main__":
    main()