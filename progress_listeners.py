#!/usr/bin/env python3
# ============================================================================
#  progress_listeners.py
#  ---------------------
#  Objectif :
#     Fournir des **listeners** (consommateurs d’événements) pour exploiter les
#     messages de progression émis par `progress.emit(...)` :
#       - affichage console “propre” (seulement les étapes majeures),
#       - journalisation persistante au format JSONL (un fichier par run),
#       - agrégation de plusieurs listeners avec tolérance aux erreurs.
#
#  Types / conventions :
#     - Listener = Callable[[str, Dict[str, Any]], None]
#       Chaque listener reçoit :
#         * event : str  (nom de l’événement)
#         * data  : dict (payload enrichi : ts, pct, msg, etc.)
#
#  Entrées principales (API) :
#     - console_clean_listener(event, data)
#         Affiche uniquement un sous-ensemble d’événements “majeurs” (set `major`) :
#           * pipeline : start/done
#           * capture  : lock + capture faces + completed/failed
#           * detection/conversion/solve/execute : started/completed/failed
#           * already_solved / error
#         Format : "[ xx.x%] <event> <msg>"
#
#     - jsonl_file_listener(folder="tmp", prefix="debug_progress", timestamp=None) -> Listener
#         Crée un listener qui écrit chaque événement en JSONL :
#           * crée le dossier si nécessaire,
#           * nomme le fichier : {prefix}_{YYYYMMDD_HHMMSS}.jsonl (sauf timestamp fourni),
#           * écrit chaque payload (data) en une ligne JSON (UTF-8, ensure_ascii=False),
#           * flush à chaque écriture (utile en live/debug).
#         Bonus : expose le chemin via attribut _listener.path.
#
#     - multi_listener(*listeners) -> Listener
#         Combine plusieurs listeners en un seul :
#           * appelle chacun dans l’ordre,
#           * encapsule chaque appel dans try/except pour éviter qu’un listener
#             défaillant casse tout le pipeline.
#
#  Dépendances :
#     - typing (types)
#     - json, os (écriture fichier + mkdir)
#     - datetime (timestamp des fichiers)
#
#  Notes :
#     - jsonl_file_listener ouvre le fichier en mode "w" : un nouveau fichier est
#       créé à chaque exécution (pas d’append).
#     - console_clean_listener est volontairement minimal : adapte la liste `major`
#       selon les événements que tu veux voir.
# ============================================================================


from typing import Dict, Any, Callable, Optional
import json
import os
from datetime import datetime

Listener = Callable[[str, Dict[str, Any]], None]

def console_clean_listener(event: str, data: Dict[str, Any]) -> None:
    # Affiche uniquement les étapes majeures (modifie la liste à ta sauce)
    major = {
        # pipeline
        "pipeline_started", "pipeline_done",

        # capture
        "capture_started", "camera_lock_started", "camera_lock_done",
        "capture_face", "capture_completed", "capture_failed",

        # calibration (si utilisé)
        "calibration_started", "calibration_completed", "calibration_failed", "calibration_skipped",

        # detection
        "detection_started", "detect_face", "detection_completed", "detection_failed",

        # conversion
        "conversion_started", "conversion_completed", "conversion_failed",

        # solve
        "solving_started", "solving_completed", "solving_failed", "already_solved",

        # execute
        "execute_move", "execution_finished", "execution_stopped", "execution_failed",

        # generic
        "error",
    }
    if event in major:
        pct = data.get("pct")
        pct_txt = f"{pct*100:5.1f}%" if isinstance(pct, (int, float)) and 0 <= pct <= 1 else "  -- "
        msg = data.get("msg", "")
        print(f"[{pct_txt}] {event:20s} {msg}")

def jsonl_file_listener(
    folder: str = "tmp",
    prefix: str = "debug_progress",
    timestamp: Optional[str] = None,
) -> Listener:
    os.makedirs(folder, exist_ok=True)
    ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"{prefix}_{ts}.jsonl")

    f = open(path, "w", encoding="utf-8")  # "w" => nouveau fichier à chaque run

    def _listener(event: str, data: Dict[str, Any]) -> None:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
        f.flush()

    # optionnel : expose le path pour l'afficher
    _listener.path = path  # type: ignore[attr-defined]
    return _listener

def multi_listener(*listeners: Listener) -> Listener:
    def _listener(event: str, data: Dict[str, Any]) -> None:
        for l in listeners:
            try:
                l(event, data)
            except Exception as e:
                print("[WARN] listener failed:", e)
    return _listener
