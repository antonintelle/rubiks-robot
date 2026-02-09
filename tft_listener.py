# tft_listener.py
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
