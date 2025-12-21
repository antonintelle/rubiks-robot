import pygame
from .base import Screen, HEADER_HEIGHT

class HomeScreen(Screen):
    def __init__(self, gui):
        super().__init__(gui, title="Home")
        # Précharger les icônes sans convert_alpha() (pas de display Pygame) [file:22]
        try:
            self.power_icon = pygame.image.load('icons/power-btn.png')  # .convert_alpha() supprimé
            self.power_icon = pygame.transform.smoothscale(self.power_icon, (16, 16))
        except FileNotFoundError:
            self.power_icon = None

        try:
            self.settings_icon = pygame.image.load('icons/settings-btn.png')  # idem
            self.settings_icon = pygame.transform.smoothscale(self.settings_icon, (16, 16))
        except FileNotFoundError:
            self.settings_icon = None

    def render_body(self):
        # Icône power en bas à gauche
        if self.power_icon is not None:
            w, h = self.power_icon.get_size()
            x, y = self.get_position('ld', obj_size=(w, h), margin=5)
            self.surface.blit(self.power_icon, (x, y))

        # Icône settings en bas à droite
        if self.settings_icon is not None:
            w, h = self.settings_icon.get_size()
            x, y = self.get_position('rd', obj_size=(w, h), margin=5)
            self.surface.blit(self.settings_icon, (x, y))
