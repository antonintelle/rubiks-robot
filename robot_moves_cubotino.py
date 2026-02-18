#!/usr/bin/env python3
# ============================================================================
#  robot_moves_cubotino.py
#  -----------------------
#  Objectif :
#     Adapter l’algorithme **Cubotino** (conversion d’une solution Kociemba/Singmaster
#     en séquence robot F/S/R) à **ton hardware** (servos via robot_servo.py).
#     Le module :
#       - parse une solution Singmaster ("R U R' U' ..."),
#       - la convertit au format attendu par Cubotino_T_moves (U1R2...),
#       - compile une séquence robot “Cubotino-like” (F/S/R),
#       - exécute réellement les primitives mécaniques (flip/spin/rotate),
#       - propose aussi des helpers dédiés à la **capture des faces** (yaw/return).
#
#  Dépendances :
#     - Cubotino_T_moves.py (obligatoire) : robot_required_moves(...) (conversion Kociemba -> F/S/R)
#     - robot_servo.py (optionnel) : pilotage réel des servos (sinon mode simulation / Windows)
#
#  Entrées principales (API “exécution solution”) :
#     - execute_solution(singmaster, start_mode="UFR", dry_run=False, verbose=True,
#                        stop_flag=None, progress_callback=None) -> str
#         Point d’entrée utilisateur :
#           * compile_robot_moves(...) -> moves_str "F1S3R1..."
#           * execute_robot_moves(...) -> exécution step-by-step
#         Retourne la chaîne de moves F/S/R exécutée.
#
#     - compile_robot_moves(singmaster, start_mode="UFR", informative=False) -> (moves_str, tot_moves)
#         Compile uniquement (sans exécution) une solution Singmaster en mouvements robot.
#
#  Parsing / normalisation Singmaster :
#     - parse_singmaster(solution) -> List[str]
#         Accepte formats :
#           * "R U R' U'" (avec espaces)
#           * "RUR'U'" (sans espaces)
#         Supporte la normalisation des quotes typographiques (’ -> ').
#
#     - singmaster_to_cubotino_kociemba(tokens) -> str
#         Convertit tokens URFDLB vers le format compact Cubotino :
#           - 1 : 90° CW
#           - 2 : 180°
#           - 3 : 90° CCW (prime)
#         Refuse explicitement x/y/z (rotations de cube).
#
#  Exécution des mouvements robot (format Cubotino) :
#     - execute_robot_moves(moves, opt, stop_flag=None, progress_callback=None)
#         Exécute une chaîne de paires :
#           * Fk : flip(s)
#           * Sx : spin du cube (capot ouvert)
#           * Rx : rotation layer bas (capot fermé)
#         Émet des événements progress_callback :
#           - "execute_move" (status executing/completed)
#           - "execution_finished" / "execution_stopped"
#
#  Options d’exécution :
#     - ExecOptions(start_mode="UFR", dry_run=False, verbose=True)
#         * dry_run : simule la cinématique en mettant à jour hw.cube_pos / hw.cover_pos
#         * verbose : logs console des actions HW
#
#  Primitives hardware (wrappers) :
#     - flip_up(), flip_open(), spin_out(direction), spin_mid()
#         -> appellent robot_servo si dispo, sinon mode simulation (Windows / SERVO_AVAILABLE=False)
#
#  Helpers capture (scan des faces / orientation) :
#     - step_flip(), step_yaw(dir_="D"), step_yaw90_to_mid(dir_="D")
#     - scan_yaw_out(direction), scan_yaw_home()
#     - return_to_u_fr_l(), return_to_u_fr_l2(), return_to_u_fr()
#         Utilitaires de repositionnement du cube après séquences de capture.
#
#  Arrêt rapide / sécurité :
#     - stop_flag (threading.Event typiquement) :
#         Vérifié avant chaque action ; lève ExecutionStopped si stop demandé.
#
#  Exécution directe (__main__) :
#     - CLI :
#         python robot_moves_cubotino.py "R U R' U'" --start UFR --dry-run --quiet
# ============================================================================


from __future__ import annotations

from dataclasses import dataclass
import re
import platform
from typing import Iterable, List, Tuple
import time

# ---------------------------------------------------------------------------
# Import Cubotino converter (fortement réutilisé)
# ---------------------------------------------------------------------------

try:
    import Cubotino_T_moves as cub_moves  # type: ignore
except Exception as e:  # pragma: no cover
    raise ImportError(
        "Impossible d'importer Cubotino_T_moves.py.\n"
        "→ Copie `Cubotino_T_moves.py` dans le même dossier que ce fichier,\n"
        "  OU ajoute son dossier au PYTHONPATH.\n"
        f"Détail import: {e}"
    )

# Import matériel
try:
    import robot_servo as hw
    SERVO_AVAILABLE = True
except Exception:
    hw = None
    SERVO_AVAILABLE = False

# Pour arret rapide
class ExecutionStopped(Exception):
    pass

def _stopped(stop_flag) -> bool:
    try:
        return stop_flag is not None and stop_flag.is_set()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Hardware primitives (ton robot)
# ---------------------------------------------------------------------------

def flip_up():
    if platform.system() == "Windows" or not SERVO_AVAILABLE:
        print("[SIMULATION] flip_up")
        time.sleep(0.1)
        return
    hw.flip_up()

def flip_open():
    if platform.system() == "Windows" or not SERVO_AVAILABLE:
        print("[SIMULATION] flip_open")
        time.sleep(0.1)
        return
    hw.flip_open()

def spin_out(direction: str):
    if platform.system() == "Windows" or not SERVO_AVAILABLE:
        print(f"[SIMULATION] spin_out {direction}")
        time.sleep(0.1)
        return
    hw.spin_out(direction)

def spin_mid():
    if platform.system() == "Windows" or not SERVO_AVAILABLE:
        print("[SIMULATION] spin_mid")
        time.sleep(0.1)
        return
    hw.spin_mid()


# ---------------------------------------------------------------------------
# Parsing / normalisation Singmaster
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\s*([URFDLBxyz])(2|')?\s*")


def _normalize_quotes(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'").strip()


def parse_singmaster(solution: str) -> List[str]:
    """Retourne la liste des tokens Singmaster, en tolérant espaces.

    Exemple: "R U R' U'" -> ["R", "U", "R'", "U'"]
    """
    solution = _normalize_quotes(solution)
    if not solution:
        return []

    # split simple (respecte déjà les espaces)
    if " " in solution:
        toks = [t for t in solution.split() if t]
    else:
        # accepte aussi "RUR'U'" (sans espaces)
        toks = []
        i = 0
        while i < len(solution):
            m = _TOKEN_RE.match(solution, i)
            if not m:
                raise ValueError(f"Token Singmaster invalide autour de: {solution[i:i+6]!r}")
            face, suf = m.group(1), m.group(2) or ""
            toks.append(face + suf)
            i = m.end()
    return toks


def singmaster_to_cubotino_kociemba(tokens: Iterable[str]) -> str:
    """Convertit Singmaster -> format Cubotino 'U1R2L3...' (sans espaces).

    Cubotino_T_moves attend des blocs (Face + chiffre):
      - 1 : 90° CW
      - 2 : 180°
      - 3 : 90° CCW (prime)

    Remarque: on accepte aussi x/y/z (cube rotations) et on les traduit
    en séquence équivalente de faces (approx standard):
      x  = R L' (rotation cube) n'est PAS une face-turn équivalente.
    Donc ici on *refuse* x/y/z dans l'entrée : le solveur renvoie normalement
    seulement URFDLB.
    """
    out: List[str] = []
    for t in tokens:
        if not t:
            continue
        face = t[0]
        if face in ("x", "y", "z"):
            raise ValueError(
                "La solution contient des rotations de cube (x/y/z). "
                "Pour un robot Cubotino-like, donne une solution uniquement en URFDLB."
            )
        if face not in "URFDLB":
            raise ValueError(f"Face invalide: {t}")
        if t.endswith("2"):
            out.append(face + "2")
        elif t.endswith("'"):
            out.append(face + "3")
        else:
            out.append(face + "1")
    return "".join(out)


# ---------------------------------------------------------------------------
# Exécution séquence F/S/R (format Cubotino)
# ---------------------------------------------------------------------------


@dataclass
class ExecOptions:
    start_mode: str = "UFR"  # "UFR" (cube posé comme le solveur) ou "AFTER_SCAN" (orientation Cubotino après scan)
    dry_run: bool = False
    verbose: bool = True


def compile_robot_moves(singmaster: str, start_mode: str = "UFR", informative: bool = False) -> Tuple[str, int]:
    """Compile une solution Singmaster en string Cubotino robot moves (F/S/R...)."""
    tokens = parse_singmaster(singmaster)
    sol_compact = singmaster_to_cubotino_kociemba(tokens)

    simulation = True if start_mode.upper() == "UFR" else False

    _robot_dict, moves_str, tot_moves, _opt = cub_moves.robot_required_moves(
        sol_compact,
        solution_Text="OK",
        simulation=simulation,
        informative=informative,
    )
    return moves_str, tot_moves

def _set_cube_pos(pos: str) -> None:
    try:
        hw.cube_pos = pos
    except Exception:
        pass

def _set_cover_pos(pos: str) -> None:
    try:
        hw.cover_pos = pos
    except Exception:
        pass

def _do_flip(k: int, *, opt: ExecOptions,stop_flag=None) -> None:
    if hw is None and not opt.dry_run:
        raise RuntimeError("Servo non disponible (hw=None)")
    for _ in range(k):
        if _stopped(stop_flag):
            raise ExecutionStopped("Stop demandé pendant flip")        
        if opt.verbose:
            print("[HW] F1 -> flip_up")
        if opt.dry_run:
            # flip_up finit capot ouvert
            _set_cover_pos("open")
            continue
        hw.flip_up()


def _do_spin(code: int, *, opt: ExecOptions,stop_flag=None) -> None:
    """Spin cube (capot ouvert). Codes Cubotino: 1=CW90, 3=CCW90, 0=CW180, 4=CCW180."""
    if hw is None and not opt.dry_run:
        raise RuntimeError("Servo non disponible (hw=None)")    
    if _stopped(stop_flag):
        raise ExecutionStopped("Stop demandé pendant spin")    
    cp = getattr(hw, "cube_pos", "mid")

    # map CW/CCW vers tes directions: D = droite (CW), G = gauche (CCW)
    if code == 1:  # CW 90
        if cp == "mid":
            action = ("spin_out", "D")
        elif cp == "left":
            action = ("spin_mid", None)  # -90 -> 0 : CW 90
        else:
            raise RuntimeError("S1 demandé alors que le plateau est déjà à droite (angle +90).")

    elif code == 3:  # CCW 90
        if cp == "mid":
            action = ("spin_out", "G")
        elif cp == "right":
            action = ("spin_mid", None)  # +90 -> 0 : CCW 90
        else:
            raise RuntimeError("S3 demandé alors que le plateau est déjà à gauche (angle -90).")

    elif code == 0:  # CW 180 (attendu: gauche -> droite)
        if cp != "left":
            raise RuntimeError("S0 (CW180) attendu depuis la position gauche (-90).")
        action = ("spin_out", "D")

    elif code == 4:  # CCW 180 (attendu: droite -> gauche)
        if cp != "right":
            raise RuntimeError("S4 (CCW180) attendu depuis la position droite (+90).")
        action = ("spin_out", "G")

    else:
        raise ValueError(f"Code spin inconnu: S{code}")

    if opt.verbose:
        if action[0] == "spin_out":
            print(f"[HW] S{code} -> spin_out('{action[1]}') (cube_pos={cp})")
        else:
            print(f"[HW] S{code} -> spin_mid() (cube_pos={cp})")

    # POUR DRY RUN
    next_pos = cp
    if action[0] == "spin_mid":
        next_pos = "mid"
    elif action[0] == "spin_out":
        next_pos = "right" if action[1] == "D" else "left"

    if opt.dry_run:
        _set_cube_pos(next_pos)
        return

    if action[0] == "spin_out":
        hw.spin_out(action[1])
    else:
        hw.spin_mid()


def _do_rotate(code: int, *, opt: ExecOptions,stop_flag=None) -> None:
    """Rotate layer du bas (capot fermé). Codes Cubotino: 1=CW90, 3=CCW90, 0=CW180, 4=CCW180."""
    if hw is None and not opt.dry_run:
        raise RuntimeError("Servo non disponible (hw=None)")    
    if _stopped(stop_flag):
        raise ExecutionStopped("Stop demandé avant rotate")    
    cp = getattr(hw, "cube_pos", "mid")

    if code == 1:  # CW 90
        if cp == "mid":
            action = ("rotate_out", "D")
        elif cp == "left":
            action = ("rotate_mid", None)  # -90 -> 0 : CW 90
        else:
            raise RuntimeError("R1 demandé alors que le plateau est déjà à droite (angle +90).")

    elif code == 3:  # CCW 90
        if cp == "mid":
            action = ("rotate_out", "G")
        elif cp == "right":
            action = ("rotate_mid", None)  # +90 -> 0 : CCW 90
        else:
            raise RuntimeError("R3 demandé alors que le plateau est déjà à gauche (angle -90).")

    elif code == 0:  # CW 180 (attendu: gauche -> droite)
        if cp != "left":
            raise RuntimeError("R0 (CW180) attendu depuis la position gauche (-90).")
        action = ("rotate_out", "D")

    elif code == 4:  # CCW 180 (attendu: droite -> gauche)
        if cp != "right":
            raise RuntimeError("R4 (CCW180) attendu depuis la position droite (+90).")
        action = ("rotate_out", "G")

    else:
        raise ValueError(f"Code rotate inconnu: R{code}")

    if opt.verbose:
        if action[0] == "rotate_out":
            print(f"[HW] R{code} -> rotate_out('{action[1]}') (cube_pos={cp})")
        else:
            print(f"[HW] R{code} -> rotate_mid() (cube_pos={cp})")

    ## POUR DRY RUN
    next_pos = cp
    if action[0] == "rotate_mid":
        next_pos = "mid"
    elif action[0] == "rotate_out":
        next_pos = "right" if action[1] == "D" else "left"

    if opt.dry_run:
        _set_cover_pos("open")   # rotate_out finit capot ouvert
        _set_cube_pos(next_pos)
        return

    if action[0] == "rotate_out":
        hw.rotate_out(action[1])
    else:
        hw.rotate_mid()


def execute_robot_moves(moves: str, *, opt: ExecOptions, stop_flag=None, progress_callback=None) -> None:
    moves = moves.strip()
    if len(moves) % 2 != 0:
        raise ValueError(f"Moves string invalide (longueur impaire): {moves!r}")

    total = len(moves) // 2

    def emit(event: str, **data): ### Pour suivre les call back
        if progress_callback:
            try:
                progress_callback(event, data)   # ✅ (event, dict)
            except Exception as e:
                print(f"[WARN] progress_callback failed: {e}")    

    for idx, i in enumerate(range(0, len(moves), 2), start=1):
        if _stopped(stop_flag):
            emit("execution_stopped",
                 step="execute",
                 index=idx - 1, total=total,
                 status="stopped",
                 msg="Stop demandé")
            raise ExecutionStopped("Stop demandé")

        cmd = moves[i]
        val = int(moves[i + 1])
        move = f"{cmd}{val}"
        next_move = f"{moves[i+2]}{moves[i+3]}" if i + 2 < len(moves) else None

        emit("execute_move",
             step="execute",
             index=idx, total=total,
             move=move, next_move=next_move,
             status="executing",
             msg=f"{idx}/{total} {move}" + (f" → {next_move}" if next_move else ""))

        if cmd == "F":
            _do_flip(val, opt=opt, stop_flag=stop_flag)
        elif cmd == "S":
            _do_spin(val, opt=opt, stop_flag=stop_flag)
        elif cmd == "R":
            _do_rotate(val, opt=opt, stop_flag=stop_flag)
        else:
            raise ValueError(f"Commande robot inconnue: {cmd}{val}")

        emit("execute_move",
             step="execute",
             index=idx, total=total,
             move=move, next_move=next_move,
             status="completed",
             msg=f"done {idx}/{total} {move}")

    emit("execution_finished",
        step="execute",
        index=total, total=total,
        status="finished",
        msg="Finished")

def execute_solution(
    singmaster: str,
    *,
    start_mode: str = "UFR",
    dry_run: bool = False,
    verbose: bool = True,
    stop_flag=None,
    progress_callback=None
) -> str:
    moves_str, tot = compile_robot_moves(singmaster, start_mode=start_mode)

    if verbose:
        print("=" * 60)
        print(f"Singmaster : {singmaster}")
        print(f"Start mode : {start_mode}")
        print(f"Robot moves: {moves_str}")
        print(f"Total moves: {tot}")
        print("=" * 60)

    opt = ExecOptions(start_mode=start_mode, dry_run=dry_run, verbose=verbose)
    execute_robot_moves(moves_str, opt=opt, stop_flag=stop_flag, progress_callback=progress_callback)
    return moves_str

#### POUR CAPTURE DES FACES ######
def step_flip():
    flip_up()

def step_yaw(dir_="D"):
    # pas qui finit en MID
    flip_open()
    spin_out(dir_)   # D ou G
    flip_up()
    spin_mid()


def step_yaw90_to_mid(dir_="D"):
    spin_out(dir_)   # "D" ou "G"
    flip_up()
    spin_mid()

def scan_yaw_out(direction: str):
    """SCAN ONLY — plateau à ±90°, on reste OUT."""
    if platform.system() == "Windows" or not SERVO_AVAILABLE:
        print(f"[SIMULATION] scan_yaw_out {direction}")
        time.sleep(0.1)
        return

    flip_open()
    spin_out(direction)


def scan_yaw_home():
    """SCAN ONLY — retour plateau au centre."""
    if platform.system() == "Windows" or not SERVO_AVAILABLE:
        print("[SIMULATION] scan_yaw_home")
        time.sleep(0.1)
        return
    spin_mid()



def return_to_u_fr_l():
    flip_up()
    scan_yaw_out("G")
    flip_up()
    flip_up()
    scan_yaw_home()

def return_to_u_fr_l2():
    flip_open()

    # 1) yaw gauche (plateau out)
    spin_out("G")       # ou scan_yaw_out("G") si tu veux garder ton wrapper

    # 2) flips
    flip_up()
    flip_up()

    # 3) retour MID (home)
    spin_mid()          # ou scan_yaw_home()
   

def return_to_u_fr():
    # On est après snap("L"), donc capot ouvert + MID, mais orientation ≠ dépôt utilisateur

    flip_up()
    flip_up()

    # même "truc" que pour amener R en haut, mais utilisé ici pour remettre la pose d'équerre
    scan_yaw_out("D")
    flip_up()
    scan_yaw_home()

    flip_up()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Exécute une solution Singmaster via l'algo Cubotino.")
    ap.add_argument("solution", help="Solution Singmaster, ex: \"R U R' U'\"")
    ap.add_argument("--start", default="UFR", choices=["UFR", "AFTER_SCAN"], help="Orientation de départ")
    ap.add_argument("--dry-run", action="store_true", help="N'exécute pas les servos, imprime seulement")
    ap.add_argument("--quiet", action="store_true", help="Moins de logs")
    args = ap.parse_args()

    execute_solution(args.solution, start_mode=args.start, dry_run=args.dry_run, verbose=not args.quiet)
