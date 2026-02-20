<<<<<<< HEAD
#!/usr/bin/env python3
# ============================================================================
#  main_robot_solveur.py
#  --------------------
#  Objectif :
#     Script “main” de pilotage du **pipeline complet** du robot solveur, avec une
#     mini-UI matérielle :
#       - affichage de progression sur un écran TFT (via driver + listener),
#       - journalisation des événements au format JSONL,
#       - contrôle pause/stop via un bouton GPIO (appui court / appui long),
#       - exécution du pipeline : capture → processing → solve → exécution robot.
#
#  Configuration (constantes) :
#     - TMP_FOLDER   = "tmp"   : dossier de travail (captures, logs, écran TFT simulé)
#     - DEBUG        = "text"  : niveau debug ("none" / "text" / "full")
#     - DO_SOLVE     = True    : calcule la solution (Kociemba/solver)
#     - DO_EXECUTE   = True    : exécute physiquement la solution sur le robot
#
#     - BUTTON_GPIO_PIN = 17   : bouton (BCM GPIO17)
#     - HOLD_STOP_S     = 1.0  : appui long => stop
#     - DEBOUNCE_S      = 0.05 : anti-rebond
#
#  Entrées principales :
#     - main(tmp_folder="tmp", debug="text", do_solve=True, do_execute=True)
#         Orchestration complète :
#           * init dossier tmp + timer
#           * init bouton GPIO (pause/stop)
#           * init listeners (console + JSONL + TFT + état bouton)
#           * instancie RobotCubeSolver(image_folder=tmp_folder, debug=debug)
#           * lance solver.run(do_solve, do_execute, progress_callback=listener)
#           * affiche bilan (temps, cubeString, solution, chemins de sortie)
#
#  Contrôle bouton GPIO (gpiozero) :
#     - start_gpio_button(control, pin, hold_s=1.0, debounce_s=0.05)
#         Comportement :
#           * appui court  => toggle pause (control.pause)
#           * appui long   => stop (control.stop)
#         + lance un thread “keep_alive” tant que stop=False.
#     - RunControl dataclass : {stop: bool, pause: bool}
#
#  Progress / UI :
#     - progress_listeners :
#         * console_clean_listener : rendu console “propre”
#         * jsonl_file_listener    : log JSONL dans tmp/
#         * multi_listener         : agrégation de plusieurs listeners
#     - TFT :
#         * ConsoleTFTFile (tft_driver) : écran TFT simulé via fichier tmp/tft_screen.txt
#         * make_tft_listener (tft_listener) : adaptateur events -> affichage TFT
#     - button_listener :
#         injecte dans chaque event {btn_pause, btn_stop} pour affichage/log.
#
#  Sorties / artifacts :
#     - tmp/tft_screen.txt : sortie “écran TFT” (driver fichier)
#     - tmp/progress*.jsonl : journal JSONL des events de progression
#     - Affichage console du cubeString et de la solution (si do_solve=True)
#
#  Notes :
#     - Si le bouton STOP est actif avant le run, do_execute est forcé à False.
#     - En cas d’erreur d’initialisation bouton GPIO : le pipeline reste utilisable
#       (warning en console).
#     - Le script suppose l’API solver.run(...) et le type de retour :
#         * si do_solve=True  -> (cubeString, solution)
#         * sinon             -> cubeString
# ============================================================================

import os
import time
import threading
from dataclasses import dataclass
from colorama import init, Fore, Style
from rbx_ui_state_store import RBXScreenStateStore
from rbx_ui_listener import make_rbx_ui_listener

init(autoreset=True)

# ========= CONFIG =========
TMP_FOLDER = "tmp"
DEBUG = "text"          # "none" / "text" / "full"
DO_SOLVE = True
DO_EXECUTE = True

# GPIO
BUTTON_GPIO_PIN = 17    # BCM numbering (GPIO17)
HOLD_STOP_S = 1.0       # appui long => stop
DEBOUNCE_S = 0.05       # anti-rebond

@dataclass
class RunControl:
    stop: bool = False
    pause: bool = False

def banner():
    print(Fore.CYAN + "\n" + "=" * 60)
    print(Fore.YELLOW + Style.BRIGHT + "MAIN ROBOT SOLVEUR (UI: TFT + GPIO Button)")
    print(Fore.CYAN + "=" * 60 + Style.RESET_ALL)


def start_gpio_button(control: RunControl, pin: int, hold_s: float = 1.0, debounce_s: float = 0.05):
    """
    gpiozero:
      - appui court => toggle pause
      - appui long  => stop
    """
    from gpiozero import Button

    btn = Button(pin, pull_up=True, bounce_time=debounce_s)
    press_t0 = {"t": None}

    def on_press():
        press_t0["t"] = time.monotonic()

    def on_release():
        t0 = press_t0["t"]
        press_t0["t"] = None
        if t0 is None:
            return
        dt = time.monotonic() - t0
        if dt >= hold_s:
            control.stop = True
        else:
            control.pause = not control.pause

    btn.when_pressed = on_press
    btn.when_released = on_release

    # petit thread pour garder une boucle "vivante" + possibilité d'actions périodiques
    def keep_alive():
        while not control.stop:
            time.sleep(0.2)

    th = threading.Thread(target=keep_alive, daemon=True)
    th.start()
    return btn, th


def main(
    tmp_folder: str = TMP_FOLDER,
    debug: str = DEBUG,
    do_solve: bool = DO_SOLVE,
    do_execute: bool = DO_EXECUTE,
    extra_listeners=None,
):
    banner()
    os.makedirs(tmp_folder, exist_ok=True)
    start_time = time.perf_counter()

    # ========= CONTROL (bouton) =========
    control = RunControl()
    try:
        btn, btn_thread = start_gpio_button(
            control,
            pin=BUTTON_GPIO_PIN,
            hold_s=HOLD_STOP_S,
            debounce_s=DEBOUNCE_S,
        )
        print(Fore.GREEN + f"✅ Bouton GPIO actif sur BCM GPIO{BUTTON_GPIO_PIN} (court=pause, long=stop)")
    except Exception as e:
        btn = None
        print(Fore.YELLOW + f"⚠️ Bouton GPIO non initialisé: {e}")

    # ========= LISTENERS =========
    from progress_listeners import console_clean_listener, jsonl_file_listener, multi_listener
    from tft_driver import ConsoleTFTFile
    from tft_listener import make_tft_listener

    from rbx_ui_state_store import RBXScreenStateStore
    from rbx_ui_listener import make_rbx_ui_listener

    # TFT "fichier" (ou remplace par le vrai driver TFT)
    tft = ConsoleTFTFile(path=f"{tmp_folder}/tft_screen.txt", width=24)
    tft_listener = make_tft_listener(tft, min_refresh_s=0.15, max_line_len=24)

    # JSONL
    file_listener = jsonl_file_listener(folder=tmp_folder, prefix="progress")

    # Listener bouton -> injecte l'état pause/stop dans les events
    def inject_button_state(event: str, data: dict) -> None:
        data["btn_pause"] = control.pause
        data["btn_stop"] = control.stop

    # RBX (état écran)
    rbx_store = RBXScreenStateStore()
    rbx_listener = make_rbx_ui_listener(rbx_store)

    # ✅ Construire la LISTE, puis extend, puis multi_listener
    listeners = [
        inject_button_state,
        console_clean_listener,
        file_listener,
        tft_listener,
        rbx_listener,
    ]

    if extra_listeners:
        listeners.extend(extra_listeners)

    listener = multi_listener(*listeners)

    # ========= PIPELINE =========
    from robot_solver import RobotCubeSolver

    solver = RobotCubeSolver(image_folder=tmp_folder, debug=debug)

    if control.stop:
        do_execute = False

    try:
        result = solver.run(
            do_solve=do_solve,
            do_execute=do_execute,
            progress_callback=listener
        )

        print("[RBX_UI FINAL]", rbx_store.get())

        if do_solve:
            cubestring, solution = result
        else:
            cubestring, solution = result, ""

        if control.stop:
            print(Fore.YELLOW + "🛑 STOP demandé (bouton). Fin immédiate.")

        elapsed = time.perf_counter() - start_time
        print(Fore.CYAN + "\n" + "=" * 60)
        print(Fore.YELLOW + Style.BRIGHT + f"FINI en {elapsed:.2f} secondes" + Style.RESET_ALL)
        print(Fore.CYAN + "=" * 60)
        print(Fore.CYAN + f"CubeString: {cubestring}")
        if solution:
            print(Fore.CYAN + f"Solution:   {solution}")
        print(Fore.CYAN + f"TFT output:  {tmp_folder}/tft_screen.txt")
        print(Fore.CYAN + f"JSONL log:   {getattr(file_listener, 'path', '(voir tmp)')}")

    except Exception as e:
        elapsed = time.perf_counter() - start_time
        print(Fore.RED + f"\n❌ Échec en {elapsed:.2f}s : {e}")
        print("[RBX_UI FINAL - on error]", rbx_store.get())

    finally:
        pass

if __name__ == "__main__":
    main()
=======
# main_robot_solveur.py 
# Création d'une instance du robot puis lancement (run)
#

import time

#from types_shared import FacesDict
from colorama import init, Fore, Style
# Initialisation des couleurs (Windows / Linux / Mac)
init(autoreset=True)

print(Fore.CYAN + "\n" + "=" * 50)
print(Fore.YELLOW + Style.BRIGHT + "SYSTÈME ROBOTIQUE DE RECONNAISSANCE RUBIK'S CUBE")
print(Fore.CYAN + "=" * 50 + Style.RESET_ALL)

from robot_solver import RobotCubeSolver

start_time = time.perf_counter()

solver = RobotCubeSolver(image_folder="tmp", debug="text")
cubestring = solver.run(do_solve=True,do_execute=True)  # renvoie la chaîne 54 URFDLB
#print(cubestring)

end_time = time.perf_counter()
elapsed = end_time - start_time

print(Fore.CYAN + "\n" + "="*60)
print(Fore.YELLOW + Style.BRIGHT + f"FINI en {elapsed:.2f} secondes" + Style.RESET_ALL)
print(Fore.CYAN + "="*60)

>>>>>>> screen-gui
