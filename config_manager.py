#!/usr/bin/env python3
# ============================================================================
#  config_manager.py
#  -----------------
#  Objectif :
#     Gérer une **configuration centralisée** du robot (format JSON) avec :
#       - valeurs par défaut (DEFAULT_CONFIG),
#       - chargement/sauvegarde robuste dans config.json,
#       - accès pratique via chemins "section.cle" (get/set),
#       - raccourcis (properties) pour les sections courantes,
#       - singleton global via get_config().
#
#  Fichier de configuration :
#     - CONFIG_FILE = <dossier_du_script>/config.json
#     - Si absent : création automatique avec DEFAULT_CONFIG puis save().
#     - Si lecture échoue : fallback sur DEFAULT_CONFIG.
#
#  Entrées principales (API) :
#     - get_config() -> Config
#         Retourne l’instance unique (singleton) du gestionnaire de config.
#
#  Classe Config :
#     - load()  : charge config.json (ou crée défaut)
#     - save()  : écrit config.json (indent=2), crée le dossier parent si besoin
#
#     - get(key_path, default=None)
#         Lecture par chemin "a.b.c" dans le dict de config.
#
#     - set(key_path, value, save=True)
#         Écriture par chemin "a.b.c" (crée les sous-dicts manquants),
#         sauvegarde immédiate si save=True.
#
#     - get_section(section)
#         Retourne une section complète (dict) : "leds", "camera", "servos", etc.
#
#  Raccourcis pratiques :
#     - leds_enabled  : bool (leds.enabled)
#     - leds_config   : dict section leds
#     - camera_config : dict section camera
#     - servos_config : dict section servos
#
#  Structure DEFAULT_CONFIG (exemples) :
#     - leds : enabled, pin, count, brightness, color_temp
#     - camera : resolution, rotation
#     - servos : enabled, cube_holder, top_cover (pins + pulses)
#     - detection : yolo_model, confidence_threshold
#     - paths : tmp_dir, models_dir, output_dir
#
#  Exécution directe (__main__) :
#     - Petit “self-test” : lecture de clés, modification leds.brightness,
#       affichage section, test clé inexistante.
# ============================================================================


import json
import os
from pathlib import Path

# Chemin du fichier de configuration
CONFIG_FILE = Path(__file__).parent / "config.json"

# Configuration par défaut
DEFAULT_CONFIG = {
    "leds": {
        "enabled": True,
        "pin": 18,
        "count": 16,
        "brightness": 0.3,
        "color_temp": "neutral"
    },
    "camera": {
        "resolution": [640, 480],
        "rotation": 270
    },
    "servos": {
        "enabled": True,
        "cube_holder": {
            "pin": 12,
            "min_pulse": 500,
            "max_pulse": 2500
        },
        "top_cover": {
            "pin": 13,
            "min_pulse": 500,
            "max_pulse": 2500
        }
    },
    "detection": {
        "yolo_model": "best.pt",
        "confidence_threshold": 0.5
    },
    "paths": {
        "tmp_dir": "tmp",
        "models_dir": "models",
        "output_dir": "output"
    }
}


class Config:
    """Gestionnaire de configuration du robot"""
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = Path(config_file)
        self._config = None
        self.load()
    
    def load(self):
        """Charge la configuration depuis le fichier JSON"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
                print(f"✅ Configuration chargée depuis {self.config_file}")
            except Exception as e:
                print(f"⚠️ Erreur lors du chargement de la config : {e}")
                print("📝 Utilisation de la configuration par défaut")
                self._config = DEFAULT_CONFIG.copy()
        else:
            print(f"ℹ️ Fichier {self.config_file} non trouvé")
            print("📝 Création avec configuration par défaut")
            self._config = DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            # Créer le répertoire parent si nécessaire
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            print(f"✅ Configuration sauvegardée dans {self.config_file}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")
    
    def get(self, key_path, default=None):
        """
        Récupère une valeur de configuration en utilisant un chemin de clés
        
        Args:
            key_path: Chemin des clés séparées par des points (ex: "leds.enabled")
            default: Valeur par défaut si la clé n'existe pas
        
        Returns:
            La valeur trouvée ou la valeur par défaut
        
        Example:
            >>> config.get("leds.enabled")
            True
            >>> config.get("leds.brightness")
            0.3
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path, value, save=True):
        """
        Modifie une valeur de configuration
        
        Args:
            key_path: Chemin des clés séparées par des points
            value: Nouvelle valeur
            save: Si True, sauvegarde immédiatement dans le fichier
        
        Example:
            >>> config.set("leds.enabled", False)
            >>> config.set("leds.brightness", 0.5)
        """
        keys = key_path.split('.')
        current = self._config
        
        # Naviguer jusqu'à l'avant-dernière clé
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Définir la valeur
        current[keys[-1]] = value
        
        if save:
            self.save()
        
        print(f"✏️ Configuration mise à jour : {key_path} = {value}")
    
    def get_section(self, section):
        """
        Récupère une section complète de la configuration
        
        Args:
            section: Nom de la section (ex: "leds", "camera")
        
        Returns:
            Dict contenant la section ou None
        """
        return self._config.get(section, None)
    
    @property
    def leds_enabled(self):
        """Raccourci pour savoir si les LEDs sont activées"""
        return self.get("leds.enabled", True)
    
    @property
    def leds_config(self):
        """Raccourci pour obtenir toute la config LEDs"""
        return self.get_section("leds")
    
    @property
    def camera_config(self):
        """Raccourci pour obtenir toute la config caméra"""
        return self.get_section("camera")
    
    @property
    def servos_config(self):
        """Raccourci pour obtenir toute la config servos"""
        return self.get_section("servos")


# Instance globale de configuration (singleton pattern)
_config_instance = None

def get_config():
    """Retourne l'instance unique de configuration"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# Pour usage direct du module
if __name__ == "__main__":
    # Test du module
    config = get_config()
    
    print("\n=== Test de lecture ===")
    print(f"LEDs activées : {config.get('leds.enabled')}")
    print(f"Luminosité : {config.get('leds.brightness')}")
    print(f"Pin LEDs : {config.get('leds.pin')}")
    
    print("\n=== Test de modification ===")
    config.set("leds.brightness", 0.5)
    
    print("\n=== Section complète ===")
    print(f"Config LEDs : {config.leds_config}")
    
    print("\n=== Test de chemin inexistant ===")
    print(f"Valeur inexistante : {config.get('inexistant.chemin', 'VALEUR_PAR_DEFAUT')}")