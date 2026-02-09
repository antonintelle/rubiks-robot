# progress_listeners.py
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
