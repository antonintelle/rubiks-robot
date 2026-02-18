# rbx_ui_state_store.py
import threading
from rbx_ui_contracts import RBXScreenProgressState

class RBXScreenStateStore:
    """
    Store thread-safe : le pipeline écrit, l'UI lit.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._state = RBXScreenProgressState()

    def set(self, st: RBXScreenProgressState) -> None:
        with self._lock:
            self._state = st

    def get(self) -> RBXScreenProgressState:
        with self._lock:
            return self._state
