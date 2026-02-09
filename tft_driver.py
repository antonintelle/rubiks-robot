# tft_driver.py
from __future__ import annotations

class DummyTFT:
    """Driver de secours: ne fait rien. Remplacer par le driver réel TFT."""
    width = 160
    height = 128

    def clear(self) -> None:
        pass

    def text(self, line: str, row: int = 0) -> None:
        
        pass

    def bar(self, pct: float) -> None:
        pass

    def show(self) -> None:
        pass

#### PERMET DE SIMULER UNE CONSOLE EN ATTENDANT LE TFT 
### POUR VISUALISER
### tail -F rubik/pipeline-complet-rubik/tmp/tft_screen.txt (POur visualiser)
### > rubik/pipeline-complet-rubik/tmp/tft_screen.txt pour remettre à zero
#######

class ConsoleTFTFile:
    """
    Faux driver TFT: écrit l'état "écran" dans un fichier texte.
    Tu peux faire: tail -f tmp/tft_screen.txt
    """
    def __init__(self, path: str = "tmp/tft_screen.txt", width: int = 24):
        self.path = path
        self.width = width
        self._lines = [" " * width, " " * width]
        self._bar = 0.0

    def clear(self) -> None:
        self._lines = [" " * self.width, " " * self.width]
        self._bar = 0.0

    def text(self, line: str, row: int = 0) -> None:
        if row not in (0, 1):
            return
        line = (line or "")[:self.width].ljust(self.width)
        self._lines[row] = line

    def bar(self, pct: float) -> None:
        try:
            pct = float(pct)
        except Exception:
            pct = 0.0
        if pct < 0.0: pct = 0.0
        if pct > 1.0: pct = 1.0
        self._bar = pct

    def show(self) -> None:
        filled = int(self.width * self._bar)
        bar = "[" + "#" * filled + "-" * (self.width - filled) + "]"

        # écriture "atomique" simple: write -> replace
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("[TFT]\n")
            f.write(self._lines[0] + "\n")
            f.write(self._lines[1] + "\n")
            f.write(bar + "\n")
        # rename atomique sur Linux
        import os
        os.replace(tmp_path, self.path)