#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug pour visualiser les écrans RubikGUI sans matériel
Sauvegarde et affiche les écrans en PNG avec prévisualisation
"""

from PIL import Image, ImageFont
import os
import sys
import importlib
from datetime import datetime
import glob

# Mock des dépendances matérielles
class MockSerial:
    def cleanup(self):
        pass

class MockDevice:
    def __init__(self, width=320, height=240):
        self.width = width
        self.height = height
        self.size = (width, height)

    def display(self, img):
        pass

    def clear(self):
        pass

class MockTouchHandler:
    def __init__(self, on_press=None, on_release=None, on_move=None):
        self.on_press = on_press
        self.on_release = on_release
        self.on_move = on_move

    def start(self):
        pass

    def cleanup(self):
        pass

    def get_touch(self):
        """Retourne (None, None) pour simuler aucun toucher"""
        return (None, None)

# Injection des mocks
sys.modules['luma.core.interface.serial'] = type('Module', (), {'spi': lambda *args, **kwargs: MockSerial()})()
sys.modules['luma.lcd.device'] = type('Module', (), {'ili9341': lambda serial: MockDevice()})()
sys.modules['hardware.touch'] = type('Module', (), {'TouchHandler': MockTouchHandler})()

# Imports tools
from tools.network import NetworkTools
from tools.system import SystemTools

class DebugGUI:
    """Version mockée de RubikGUI pour le debug"""

    def __init__(self):
        self.device = MockDevice()
        self.font_small = self._load_font()
        self.net = NetworkTools()
        self.sys = SystemTools()
        self.current_screen_name = "home"
        self.touch = MockTouchHandler()

    def _load_font(self):
        """Charge la fonte avec fallback"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size=11)
                except:
                    pass

        return ImageFont.load_default()

    def load_screen(self, screen_name):
        """Charge dynamiquement un écran (HOT RELOAD)"""
        try:
            # Force reload du module
            module_path = f"screens.{screen_name}"
            if module_path in sys.modules:
                importlib.reload(sys.modules[module_path])

            # Import dynamique
            module = importlib.import_module(module_path)

            # Trouve la classe Screen
            class_name = ''.join(word.capitalize() for word in screen_name.split('_')) + 'Screen'
            if hasattr(module, class_name):
                screen_class = getattr(module, class_name)
                return screen_class(self)
            else:
                print(f"⚠️  Classe {class_name} introuvable dans {module_path}")
                return None

        except Exception as e:
            print(f"❌ Erreur import {screen_name}: {e}")
            return None

    def render_screen(self, screen_name):
        """Rend un écran (reload à chaque fois)"""
        print(f"🔄 Chargement {screen_name}...")
        screen = self.load_screen(screen_name)

        if screen is None:
            return None

        self.current_screen_name = screen_name
        return screen.render()

    def get_available_screens(self):
        """Retourne la liste des écrans disponibles (sans base.py)"""
        screens_dir = "screens/"
        pattern = os.path.join(screens_dir, "*.py")

        files = glob.glob(pattern)
        screen_names = []

        for file_path in files:
            filename = os.path.basename(file_path)  # screens/home.py → home.py
            name = os.path.splitext(filename)[0]     # home.py → home

            if name != "base":  # Exclut base.py
                screen_names.append(name)

        return sorted(screen_names)  # Tri alphabétique

def display_image(img, title=""):
    """
    Affiche l'image selon l'environnement disponible
    """
    # Tentative d'affichage inline (Jupyter/IPython)
    try:
        from IPython.display import display as ipy_display
        ipy_display(img)
        if title:
            print(f"📱 {title}")
        return True
    except:
        pass

    # Tentative matplotlib
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 6))
        plt.imshow(img)
        plt.axis('off')
        if title:
            plt.title(title, fontsize=14, pad=10)
        plt.tight_layout()
        plt.show()
        return True
    except:
        pass

    return False

def get_help():
    """Affiche l'aide complète"""
    print("Affichage d'écran")
    print("  [ecran]       → Affichage de l'écran")
    print()
    print("Commandes")
    print("  /help, /h   → Cette aide")
    print("  /list, /l   → Liste écrans")
    print("  /quit, /q   → Quitter")
    print()

def main():
    """Boucle principale du debug viewer"""

    print("╔" + "═" * 60 + "╗")
    print("║" + " " * 15 + "RubikGUI Debug Viewer" + " " * 24 + "║")
    print("╚" + "═" * 60 + "╝")
    print()

    try:
        gui = DebugGUI()
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        print("\nAssurez-vous que tous les modules du projet sont accessibles.")
        return

    print("✅ GUI initialisée")
    print(f"📋 Écrans disponibles: {', '.join(gui.get_available_screens())}")
    print()
    print("Commandes:")
    print("  - Nom d'écran (home, debug, parameters, none) : affiche l'écran")
    print("  - list : liste les écrans disponibles")
    print("  - quit/exit/q : quitter")
    print()

    # Affichage initial
    try:
        current_img = gui.render_screen(gui.current_screen_name)

        display_image(current_img, f"Écran: {gui.current_screen_name}")
    except Exception as e:
        print(f"❌ Erreur lors du rendu initial: {e}")
        import traceback
        traceback.print_exc()

    print()

    # Boucle interactive
    while True:
        try:
            screen_name = input("Écran à afficher > ").strip().lower()

            if screen_name in ['/quit', '/q']:
                print("\n👋 Au revoir !")
                break

            if screen_name in ['', '/']:
                continue

            if screen_name in ['/list', '/l']:
                print(f"\n📋 Écrans disponibles: {', '.join(gui.get_available_screens())}")
                continue

            if screen_name in ['/help', '/h']:
                get_help()
                continue

            # === RELOAD + RENDER (à chaque requête) ===
            current_img = gui.render_screen(screen_name)

            if current_img:
                display_image(current_img, f"Écran: {screen_name}")

                print()
            else:
                print(f"❌ Erreur: L'écran '{screen_name}' n'existe pas.")
                print(f"📋 Écrans disponibles: {', '.join(gui.get_available_screens())}")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption détectée. Au revoir !")
            break
        except EOFError:
            print("\n\n👋 Fin de la saisie. Au revoir !")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
