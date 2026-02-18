#!/usr/bin/env python3
# ============================================================================
#  progress.py
#  -----------
#  Objectif :
#     Fournir un **point unique d’émission d’événements** de progression pour tout
#     le pipeline (capture / processing / solve / exécution), via un callback.
#     Le module standardise la forme des messages et garantit que le pipeline ne
#     casse pas si le callback plante.
#
#  Types / conventions :
#     - ProgressCallback = Optional[Callable[[str, Dict[str, Any]], None]]
#         Callback recevant :
#           * event : str  (ex: "capture_started", "solving_completed", ...)
#           * payload : dict (ts, event, + données métier)
#
#  Entrée principale (API) :
#     - emit(cb, event, **data) -> None
#         Émet un événement si cb est défini :
#           * ajoute automatiquement :
#               - ts    : time.time() (timestamp epoch, float)
#               - event : nom de l’événement
#           * fusionne les champs supplémentaires passés en **data
#           * mode “safe” : try/except autour du callback
#               - si le callback lève une exception, on loggue un warning
#                 et le pipeline continue (pas de crash).
#
#  Dépendances :
#     - time : génération du timestamp
#     - typing : types du callback et du payload
#
#  Notes :
#     - Ce module sert de brique de base aux “listeners” (console, JSONL, TFT, etc.)
#       et évite de dupliquer la logique ts/event + gestion d’erreurs partout.
# ============================================================================


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
