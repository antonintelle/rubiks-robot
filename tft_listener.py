#!/usr/bin/env python3
# ============================================================================
#  tft_listener.py
#  ---------------
#  Objectif :
#     Convertir les événements de progression du pipeline (progress.emit / listeners)
#     en un affichage “écran TFT” simple (2 lignes + barre), via un driver TFT
#     compatible (ex: ConsoleTFTFile de tft_driver.py).
#
#  Principe :
#     - Filtre uniquement les événements “majeurs” (MAJOR_EVENTS) afin de ne pas
#       saturer l’affichage.
#     - Limite le taux de rafraîchissement (min_refresh_s) pour éviter le flicker.
#     - Formate des messages courts (max_line_len) adaptés à un petit écran.
#     - Déduplique les rendus : ne redessine pas si (event, pct, msg) n’a pas changé.
#
#  Entrée principale (factory) :
#     - make_tft_listener(tft, min_refresh_s=0.10, max_line_len=20) -> listener
#         Retourne une fonction listener(event: str, data: dict) qui :
#           * ignore les events non majeurs,
#           * affiche :
#               - ligne 1 : "<pct> <step>"
#               - ligne 2 : message court contextuel
#               - barre   : progression (si pct numérique)
#           * gère les erreurs silencieusement (try/except autour du driver TFT).
#
#  Événements supportés :
#     - Pipeline : pipeline_started / pipeline_done
#     - Capture  : capture_started, camera_lock_started/done, capture_face,
#                 capture_completed, capture_failed
#     - Calibration : calibration_started/completed/failed/skipped
#     - Detection : detection_started, detect_face, detection_completed/failed
#     - Conversion : conversion_started/completed/failed
#     - Solve : solving_started/completed/failed, already_solved
#     - Execute : execute_move, execution_finished/stopped/failed
#     - Generic : error
#
#  Formats d’affichage (exemples) :
#     - CAP U capturing 1/6
#     - DET F ... 2/6
#     - Conv OK: UFRDLB…   (aperçu cube_string)
#     - EXE 12/42 R2 executing
#     - SOL 23: R U R' ...
#     - ...FAILED: <msg | err>
#
#  Fonctions internes :
#     - _short(s)     : tronque/pad à max_line_len, remplace "→" par ">"
#     - _fmt_pct(pct) : " 42%" si pct ∈ [0..1], sinon " --%"
#     - _err_hint(data) : assemble msg + err court (troncature à 40 chars)
#
#  Notes :
#     - FINAL_EVENTS ne subit pas la limitation min_refresh_s (on force l’update).
#     - Le listener ne lève jamais : en cas d’erreur driver TFT, il ignore.
# ============================================================================

from __future__ import annotations
from typing import Dict, Any
import time

MAJOR_EVENTS = {
    # pipeline
    "pipeline_started", "pipeline_done",

    # capture
    "capture_started", "camera_lock_started", "camera_lock_done",
    "capture_face", "capture_completed", "capture_failed",

    # calibration
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

FINAL_EVENTS = {"already_solved", "solving_completed", "solving_failed",
                "conversion_failed", "execution_finished", "execution_failed", "execution_stopped"}

def make_tft_listener(
    tft,
    min_refresh_s: float = 0.10,
    max_line_len: int = 20,
):
    last_draw_t = 0.0
    last_key = None

    def _short(s: str) -> str:
        s = (s or "").replace("→", ">")
        return s[:max_line_len].ljust(max_line_len)

    def _fmt_pct(pct: Any) -> str:
        if isinstance(pct, (int, float)) and 0.0 <= pct <= 1.0:
            return f"{int(pct * 100):3d}%"
        return " --%"

    def _err_hint(data: Dict[str, Any]) -> str:
        # msg + éventuellement err court
        msg = data.get("msg") or ""
        err = data.get("err") or ""
        if err and err not in msg:
            # coupe court
            err = str(err)
            if len(err) > 40:
                err = err[:40] + "…"
            return (msg + " | " + err).strip(" |")
        return msg

    def listener(event: str, data: Dict[str, Any]) -> None:
        nonlocal last_draw_t, last_key

        if event not in MAJOR_EVENTS:
            return

        now = time.time()
        if event not in FINAL_EVENTS:
            if now - last_draw_t < min_refresh_s:
                return
        pct = data.get("pct")
        step = data.get("step", "")
        msg = ""

        # -------------------------
        # Formats par type d'event
        # -------------------------

        # Pipeline
        if event == "pipeline_started":
            msg = data.get("msg") or "Pipeline started"
        elif event == "pipeline_done":
            msg = data.get("msg") or "Pipeline done"

        # Capture + lock caméra
        elif event == "capture_started":
            msg = data.get("msg") or "Capture started"
        elif event == "camera_lock_started":
            msg = data.get("msg") or "Camera lock..."
        elif event == "camera_lock_done":
            msg = data.get("msg") or "Camera locked"
        elif event == "capture_face":
            face = data.get("face", "?")
            status = data.get("status", "")
            cur = data.get("current", "")
            tot = data.get("total", "")
            msg = f"CAP {face} {status} {cur}/{tot}"
        elif event == "capture_completed":
            msg = data.get("msg") or "Capture completed"
        elif event == "capture_failed":
            msg = "CAP FAILED: " + _err_hint(data)

        # Calibration
        elif event == "calibration_started":
            msg = data.get("msg") or "Calibration..."
        elif event == "calibration_completed":
            msg = data.get("msg") or "Calibration OK"
        elif event == "calibration_skipped":
            msg = data.get("msg") or "Calibration skipped"
        elif event == "calibration_failed":
            msg = "CAL FAILED: " + _err_hint(data)

        # Detection
        elif event == "detection_started":
            msg = data.get("msg") or "Detection..."
        elif event == "detect_face":
            face = data.get("face", "?")
            status = data.get("status", "")
            cur = data.get("current", "")
            tot = data.get("total", "")
            msg = f"DET {face} {status} {cur}/{tot}"
        elif event == "detection_completed":
            msg = data.get("msg") or "Detection OK"
        elif event == "detection_failed":
            msg = "DET FAILED: " + _err_hint(data)

        # Conversion
        elif event == "conversion_started":
            msg = data.get("msg") or "Conversion..."
        elif event == "conversion_completed":
            # option: montrer les 6 premiers chars du cube_string
            cs = data.get("cube_string")
            if cs:
                msg = f"Conv OK: {str(cs)[:8]}…"
            else:
                msg = data.get("msg") or "Conversion OK"
        elif event == "conversion_failed":
            msg = "CONV FAIL: " + _err_hint(data)

        # Solve
        elif event == "solving_started":
            msg = data.get("msg") or "Solving..."
        elif event == "solving_completed":
            moves = data.get("moves")
            sol = data.get("solution")
            if sol:
                msg = f"SOL {moves or ''}: {sol}"
            else:
                msg = f"Solved ({moves} moves)" if moves is not None else (data.get("msg") or "Solved")
        elif event == "already_solved":
            msg = data.get("msg") or "Already solved"
        elif event == "solving_failed":
            msg = "SOL FAIL: " + _err_hint(data)

        # Execute
        elif event == "execute_move":
            idx = data.get("index", "")
            tot = data.get("total", "")
            move = data.get("move", "")
            status = data.get("status", "")
            msg = f"EXE {idx}/{tot} {move} {status}"
        elif event == "execution_finished":
            msg = data.get("msg") or "Execution done"
        elif event == "execution_stopped":
            msg = data.get("msg") or "Execution stopped"
        elif event == "execution_failed":
            msg = "EXE FAIL: " + _err_hint(data)

        # Generic
        elif event == "error":
            msg = "ERROR: " + _err_hint(data)

        else:
            # fallback (au cas où)
            msg = data.get("msg") or event

        # -------------------------
        # Dedup + render
        # -------------------------
        key = (event, pct, msg)
        if key == last_key:
            return
        last_key = key
        last_draw_t = now

        line1 = _short(f"{_fmt_pct(pct)} {step}")
        line2 = _short(msg)

        try:
            tft.clear()
            tft.text(line1, row=0)
            tft.text(line2, row=1)
            if isinstance(pct, (int, float)):
                tft.bar(max(0.0, min(1.0, float(pct))))
            tft.show()
        except Exception as e:
            # pendant debug tu peux décommenter:
            # print("[TFT_LISTENER_ERROR]", repr(e))
            return

    return listener
