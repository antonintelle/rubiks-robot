from rbx_ui_adapter import RBXPipelineToScreenAdapter
from rbx_ui_state_store import RBXScreenStateStore

class RBXScreenProgressCallback:
    def __init__(self, store: RBXScreenStateStore):
        self.store = store
        self.adapter = RBXPipelineToScreenAdapter()

    def __call__(self, event: str, *args, **kwargs):
        # style: cb(event, payload_dict)
        if args and isinstance(args[0], dict) and not kwargs:
            payload = args[0]
        else:
            # style: cb(event, **payload)
            payload = dict(kwargs)

        st = self.adapter.on_event(event, payload)
        self.store.set(st)
