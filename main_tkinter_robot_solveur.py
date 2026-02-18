#!/usr/bin/env python3
# =============================================================================
# main_tkinter_robot_solveur.py
# -----------------------------------------------------------------------------
# GUI Tkinter principale :
# - Start / Pause-Resume / E-STOP
# - Optionnel : bouton GPIO E-STOP ONLY (aucune pause)
# - Affiche les callbacks (event, data) : 2 lignes + barre + log
#
# IMPORTANT :
# - Tkinter DOIT tourner sur le thread principal
# - Le pipeline robot tourne dans un thread séparé
# - Thread robot -> UI via queue.Queue
# - Pause : on "gate" le pipeline à l'intérieur du progress_callback (pause réelle
#   si ton pipeline émet des callbacks régulièrement)
# =============================================================================

from __future__ import annotations

import os
import time
import threading
import queue
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from robot_solver import PipelineStopped

# ============ CONFIG ============
TMP_FOLDER = "tmp"
DEBUG_DEFAULT = "text"        # "none" / "text" / "full"
DO_SOLVE_DEFAULT = True
DO_EXECUTE_DEFAULT = True

# GPIO E-STOP (optionnel)
BUTTON_GPIO_PIN = 17  # BCM


# ============ CONTROL ============
@dataclass
class RunControl:
    pause: bool = False
    stop: bool = False


# ============ GPIO E-STOP ONLY ============
def start_gpio_emergency_stop(on_estop, pin: int):
    from gpiozero import Button
    btn = Button(pin, pull_up=True)
    btn.when_pressed = on_estop
    return btn


# ============ QUEUE LISTENER (thread-safe) ============
UIEvent = Tuple[str, Dict[str, Any]]

def make_queue_listener(q: "queue.Queue[UIEvent]"):
    """Listener pipeline -> queue (NE TOUCHE JAMAIS Tkinter)."""
    def listener(event: str, data: Dict[str, Any]) -> None:
        q.put((event, dict(data)))
    return listener


def make_gated_progress_callback(control: RunControl, base_cb):
    """
    Wrappe le progress_callback pour gérer :
    - stop : lève EmergencyStop pour abort ASAP
    - pause : bloque tant que pause=True (au prochain callback)
    - injecte btn_pause/btn_stop dans data (comme ton main)
    """
    paused_notified = {"sent": False}

    def cb(event: str, data: Dict[str, Any]):
        # inject état boutons dans data
        data["btn_pause"] = control.pause
        data["btn_stop"] = control.stop

        # pause : bloque le pipeline ici (au prochain callback)
        while control.pause and not control.stop:
            if not paused_notified["sent"]:
                paused_notified["sent"] = True
                try:
                    base_cb("paused", {
                        "step": data.get("step", ""),
                        "pct": data.get("pct", None),
                        "msg": "Paused",
                        "btn_pause": True,
                        "btn_stop": False,
                    })
                except Exception:
                    pass
            time.sleep(0.05)

        paused_notified["sent"] = False

        # forward event
        base_cb(event, data)

    return cb


# ============ TK APP ============
class RobotGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rubik's Robot — Tkinter Main")
        self.geometry("820x560")
        self.solver = None

        self.ui_queue: "queue.Queue[UIEvent]" = queue.Queue()
        self.control = RunControl()

        self.robot_thread: Optional[threading.Thread] = None
        self.gpio_btn = None

        # UI vars
        self.var_tmp = tk.StringVar(value=TMP_FOLDER)
        self.var_debug = tk.StringVar(value=DEBUG_DEFAULT)
        self.var_do_solve = tk.BooleanVar(value=DO_SOLVE_DEFAULT)
        self.var_do_execute = tk.BooleanVar(value=DO_EXECUTE_DEFAULT)
        self.var_use_gpio = tk.BooleanVar(value=False)

        self.var_status = tk.StringVar(value="Status: idle")
        self.var_line1 = tk.StringVar(value="--% idle".ljust(28))
        self.var_line2 = tk.StringVar(value="Ready".ljust(28))
        self.var_pause = tk.StringVar(value="pause: False")
        self.var_stop = tk.StringVar(value="stop:  False")

        self._build_ui()
        self.after(50, self._poll_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root)
        top.pack(fill="x")
        ttk.Label(top, text="Rubik's Robot", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.var_status).pack(side="right")

        cfg = ttk.LabelFrame(root, text="Config", padding=10)
        cfg.pack(fill="x", pady=10)

        ttk.Label(cfg, text="tmp folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(cfg, textvariable=self.var_tmp, width=22).grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(cfg, text="debug:").grid(row=0, column=2, sticky="w", padx=(18, 0))
        ttk.Combobox(cfg, textvariable=self.var_debug, values=["none", "text", "full"],
                     width=8, state="readonly").grid(row=0, column=3, sticky="w", padx=6)

        ttk.Checkbutton(cfg, text="do_solve", variable=self.var_do_solve)\
            .grid(row=0, column=4, sticky="w", padx=(18, 0))
        ttk.Checkbutton(cfg, text="do_execute", variable=self.var_do_execute)\
            .grid(row=0, column=5, sticky="w", padx=6)

        ttk.Checkbutton(cfg, text=f"use GPIO E-STOP only (BCM{BUTTON_GPIO_PIN})",
                        variable=self.var_use_gpio)\
            .grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))

        ctl = ttk.LabelFrame(root, text="Controls", padding=10)
        ctl.pack(fill="x", pady=8)

        ttk.Button(ctl, text="Start / Run", command=self.on_start).pack(side="left", padx=6)
        ttk.Button(ctl, text="Pause / Resume", command=self.on_pause).pack(side="left", padx=6)
        ttk.Button(ctl, text="E-STOP", command=self.on_stop).pack(side="left", padx=6)

        right = ttk.Frame(ctl)
        right.pack(side="right")
        ttk.Label(right, textvariable=self.var_pause).pack(anchor="e")
        ttk.Label(right, textvariable=self.var_stop).pack(anchor="e")

        disp = ttk.LabelFrame(root, text="Display (callbacks)", padding=10)
        disp.pack(fill="x", pady=10)

        ttk.Label(disp, textvariable=self.var_line1, font=("Consolas", 12)).pack(anchor="w")
        ttk.Label(disp, textvariable=self.var_line2, font=("Consolas", 12)).pack(anchor="w", pady=(2, 8))

        self.progress = ttk.Progressbar(disp, orient="horizontal", mode="determinate", length=760)
        self.progress.pack(fill="x")
        self.progress["maximum"] = 100
        self.progress["value"] = 0

        logf = ttk.LabelFrame(root, text="Event log", padding=10)
        logf.pack(fill="both", expand=True)

        self.log = ScrolledText(logf, height=14)
        self.log.pack(fill="both", expand=True)

    # ---------- UI buttons ----------
    def on_start(self):
        if self.robot_thread and self.robot_thread.is_alive():
            self._log_line("Already running.")
            return

        tmp_folder = self.var_tmp.get().strip() or "tmp"
        os.makedirs(tmp_folder, exist_ok=True)

        # reset control
        self.control.stop = False
        self.control.pause = False
        self._update_control_labels()

        # GPIO E-STOP only (optionnel)
        if self.var_use_gpio.get():
            try:
                self.gpio_btn = start_gpio_emergency_stop(self.on_stop, pin=BUTTON_GPIO_PIN)
                self._log_line(f"GPIO E-STOP enabled (BCM{BUTTON_GPIO_PIN})")
            except Exception as e:
                self._log_line(f"GPIO init failed: {e}")

        # UI init
        self.var_status.set("Status: running")
        self.progress["value"] = 0
        self.var_line1.set("--% starting".ljust(28))
        self.var_line2.set("Pipeline start".ljust(28))

        # start thread
        self.robot_thread = threading.Thread(
            target=self._robot_thread_main,
            args=(tmp_folder, self.var_debug.get(),
                self.var_do_solve.get(), self.var_do_execute.get()),
            daemon=True,
        )
        self.robot_thread.start()


    def on_pause(self):
        # toggle pause
        self.control.pause = not self.control.pause
        self._update_control_labels()
        self.ui_queue.put(("ui_state", {"msg": f"pause -> {self.control.pause}"}))

    def on_stop(self):
        # UI state
        self.control.stop = True
        self.control.pause = False
        self._update_control_labels()
        self.ui_queue.put(("ui_state", {"msg": "E-STOP demandé (GUI/GPIO)"}))

        # STOP solver (si dispo)
        if self.solver is not None:
            try:
                self.solver.emergency_stop()
            except Exception:
                pass

    # ---------- Robot thread ----------
    def _robot_thread_main(self, tmp_folder: str, debug: str, do_solve: bool, do_execute: bool):
        """
        Lance ton pipeline réel (RobotCubeSolver) en envoyant progress_callback.
        """
        start_time = time.perf_counter()

        # Queue listener (UI)
        q_listener = make_queue_listener(self.ui_queue)

        # Option : si tu veux aussi log console + jsonl (comme ton main)
        try:
            from progress_listeners import console_clean_listener, jsonl_file_listener, multi_listener
            file_listener = jsonl_file_listener(folder=tmp_folder, prefix="progress")
            base_cb = multi_listener(q_listener, console_clean_listener, file_listener)
        except Exception:
            base_cb = q_listener

        # Gate pause/stop + inject state
        progress_cb = make_gated_progress_callback(self.control, base_cb)

        # Import solver (comme ton main_robot_solveur.py)
        try:
            from robot_solver import RobotCubeSolver  # adapte si besoin
        except Exception as e:
            self.ui_queue.put(("error", {"msg": "Import RobotCubeSolver failed", "err": repr(e), "pct": 0.0, "step": "init"}))
            return

        # si stop avant run => surtout pas d'exécution
        if self.control.stop:
            do_execute = False

        try:
            self.solver = RobotCubeSolver(image_folder=tmp_folder, debug=debug)
            solver = self.solver
            solver.reset_stop_flag()
            base_cb("pipeline_started", {"step": "pipeline", "pct": 0.0, "msg": "Pipeline started"})

            result = solver.run(
                do_solve=do_solve,
                do_execute=do_execute,
                progress_callback=progress_cb
            )

            if do_solve:
                cubestring, solution = result
            else:
                cubestring, solution = result, ""

            elapsed = time.perf_counter() - start_time
            base_cb("pipeline_done", {
                "step": "pipeline",
                "pct": 1.0,
                "msg": f"Done in {elapsed:.2f}s",
                "cube_string": cubestring,
                "solution": solution,
                "btn_pause": self.control.pause,
                "btn_stop": self.control.stop,
            })

        except PipelineStopped:
            elapsed = time.perf_counter() - start_time
            base_cb("pipeline_stopped", {
                "step": "pipeline",
                "pct": 1.0,
                "msg": f"Stopped (E-STOP) after {elapsed:.2f}s",
                "btn_pause": False,
                "btn_stop": True,
            })

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            base_cb("error", {
                "step": "error",
                "pct": 1.0,
                "msg": f"Pipeline failed after {elapsed:.2f}s",
                "err": repr(e),
                "btn_pause": self.control.pause,
                "btn_stop": self.control.stop,
            })
        finally:
            # important : libère la référence, même si STOP/erreur
            self.solver = None

    # ---------- Queue -> UI ----------
    def _poll_queue(self):
        try:
            while True:
                event, data = self.ui_queue.get_nowait()
                self._handle_event(event, data)
        except queue.Empty:
            pass

        # au cas où GPIO a changé les états
        self._update_control_labels()
        self.after(50, self._poll_queue)

    def _handle_event(self, event: str, data: Dict[str, Any]):
        pct = data.get("pct", None)
        step = data.get("step", "") or ""
        msg = data.get("msg", "") or event

        def fmt_pct(p):
            if isinstance(p, (int, float)) and 0.0 <= p <= 1.0:
                return f"{int(p * 100):3d}%"
            return " --%"

        def short(s: str, n: int = 28):
            s = (s or "")
            return s[:n].ljust(n)

        # display 2 lignes + progress
        self.var_line1.set(short(f"{fmt_pct(pct)} {step}".strip()))
        self.var_line2.set(short(msg))

        if isinstance(pct, (int, float)):
            self.progress["value"] = int(max(0.0, min(1.0, float(pct))) * 100)

        # status global
        if event == "pipeline_started":
            self.var_status.set("Status: running")
        elif event in ("pipeline_done",):
            self.var_status.set("Status: done ✅")
            self.progress["value"] = 100
        elif event in ("pipeline_stopped", "emergency_stop"):
            self.var_status.set("Status: STOPPED (E-STOP) 🛑")
        elif event == "paused":
            self.var_status.set("Status: paused ⏸")
        elif event == "error":
            self.var_status.set("Status: ERROR ❌")

        # log
        extra = ""
        if "err" in data:
            extra = f" | err={data['err']}"
        self._log_line(f"{event} | step={step} | pct={pct} | msg={msg}{extra}")

    def _update_control_labels(self):
        self.var_pause.set(f"pause: {self.control.pause}")
        self.var_stop.set(f"stop:  {self.control.stop}")

    def _log_line(self, s: str):
        ts = time.strftime("%H:%M:%S")
        self.log.insert("end", f"[{ts}] {s}\n")
        self.log.see("end")

    def _on_close(self):
        self.control.stop = True
        self.control.pause = False
        self.destroy()


if __name__ == "__main__":
    RobotGUI().mainloop()
