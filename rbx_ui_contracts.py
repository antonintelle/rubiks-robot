# rbx_ui_contracts.py
from dataclasses import dataclass

@dataclass
class RBXScreenProgressState:
    """
    État minimal affichable sur un petit écran (LCD/TFT).
    - line1 : titre court (ex: ' 32% capture')
    - line2 : sous-texte (ex: 'Capturing U (1/6)')
    - pct   : 0.0 -> 1.0
    """
    line1: str = "Ready"
    line2: str = ""
    pct: float = 0.0

    # infos bonus (debug / instrumentation)
    step: str = ""
    event: str = ""
    status: str = ""
