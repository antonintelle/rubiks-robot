# rbx_ui_adapter.py
from rbx_ui_contracts import RBXScreenProgressState

class RBXPipelineToScreenAdapter:
    """
    Convertit les events du pipeline (emit progress_callback)
    en RBXScreenProgressState (2 lignes + pct).
    """
    def __init__(self):
        self.last = RBXScreenProgressState()

    @staticmethod
    def _norm_pct(pct) -> float:
        try:
            pct = float(pct)
        except Exception:
            return 0.0
        if pct > 1.0:
            pct = pct / 100.0
        return max(0.0, min(1.0, pct))

    @staticmethod
    def _short(s: str, n: int = 30) -> str:
        if not s:
            return ""
        return (s[:n-1] + "…") if len(s) > n else s

    def on_event(self, event: str, payload: dict) -> RBXScreenProgressState:
        pct = self._norm_pct(payload.get("pct", 0.0))
        step = str(payload.get("step", "") or "")
        msg = str(payload.get("msg", "") or payload.get("status", "") or "")

        line1 = f"{int(pct*100):>3d}% {step}".strip()
        line2 = self._short(msg)

        st = RBXScreenProgressState(
            line1=line1 if line1 else "Working…",
            line2=line2,
            pct=pct,
            step=step,
            event=event,
            status=str(payload.get("status", "") or ""),
        )
        self.last = st
        return st
