#!/usr/bin/env python3
from rbx_ui_state_store import RBXScreenStateStore
from rbx_ui_listener import make_rbx_ui_listener

def main():
    store = RBXScreenStateStore()
    ui = make_rbx_ui_listener(store)

    ui("capture_started", {"step": "capture", "pct": 0.0, "msg": "Capture started"})
    print(store.get())

    ui("capture_face", {"step": "capture", "pct": 0.12, "msg": "Capturing U (1/6)"})
    print(store.get())

    ui("solve_done", {"step": "solve", "pct": 0.75, "msg": "Solution ready"})
    print(store.get())

if __name__ == "__main__":
    main()
