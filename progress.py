# progress.py
from typing import Callable, Dict, Any, Optional
import time

ProgressCallback = Optional[Callable[[str, Dict[str, Any]], None]]

def emit(cb: ProgressCallback, event: str, **data: Any) -> None:
    """
    Point unique d'émission d'events.
    - ajoute ts + event
    - safe: si le callback plante, le pipeline continue
    """
    if not cb:
        return
    payload = {"ts": time.time(), "event": event, **data}
    try:
        cb(event, payload)
    except Exception as e:
        print(f"[WARN] progress callback failed: {e}")
