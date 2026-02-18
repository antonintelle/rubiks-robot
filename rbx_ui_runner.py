# rbx_ui_runner.py
import threading
from typing import Callable, Optional

class RBXPipelineRunner:
    """
    Lance RobotSolver.run() dans un thread.
    """
    def __init__(self, solver):
        self.solver = solver
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self, *, do_solve=True, do_execute=True, auto_calibrate=False,
              progress_callback: Optional[Callable] = None) -> None:
        if self.is_running():
            return

        self._thread = threading.Thread(
            target=self._run,
            args=(do_solve, do_execute, auto_calibrate, progress_callback),
            daemon=True
        )
        self._thread.start()

    def _run(self, do_solve, do_execute, auto_calibrate, progress_callback):
        self.solver.run(
            do_solve=do_solve,
            do_execute=do_execute,
            auto_calibrate=auto_calibrate,
            progress_callback=progress_callback
        )

    def estop(self) -> None:
        # adapte selon ton projet (emergency_stop / stop_flag / stop)
        if hasattr(self.solver, "emergency_stop"):
            self.solver.emergency_stop()
        elif hasattr(self.solver, "stop"):
            self.solver.stop()
        elif hasattr(self.solver, "stop_flag"):
            self.solver.stop_flag.set()
