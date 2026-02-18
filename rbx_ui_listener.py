from rbx_ui_state_store import RBXScreenStateStore
from rbx_ui_callback import RBXScreenProgressCallback

def make_rbx_ui_listener(store: RBXScreenStateStore):
    cb = RBXScreenProgressCallback(store)

    def _listener(event: str, *args, **kwargs):
        cb(event, *args, **kwargs)

    return _listener
