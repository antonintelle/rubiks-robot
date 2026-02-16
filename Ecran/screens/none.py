from .base import Screen, HEADER_HEIGHT, BLACK

class NoneScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="None")
    
    def render_body(self, draw, header_h: int):
        pass
