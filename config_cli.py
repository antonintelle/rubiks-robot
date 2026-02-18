#!/usr/bin/env python3
# ============================================================================
#  config_cli.py
#  -------------
#  Objectif :
#     Fournir une **interface en ligne de commande (CLI)** pour consulter et modifier
#     la configuration du robot CUBOTino via le module `config_manager`.
#     Permet notamment :
#       - d’afficher toute la config ou une section,
#       - de lire/écrire une valeur par “chemin” (ex: leds.enabled),
#       - d’activer/désactiver les LEDs et régler leur luminosité,
#       - de réinitialiser la configuration aux valeurs par défaut.
#
#  Entrée principale :
#     - Exécution directe (__main__) :
#         python config_cli.py [commande] [options]
#
#  Commandes supportées :
#     - help | -h | --help
#         Affiche l’aide + exemples.
#
#     - show [section]
#         Affiche la configuration complète (config._config) ou une section
#         (via config.get_section(section)).
#
#     - get <chemin>
#         Récupère une valeur via config.get(chemin)
#         Exemple : get leds.enabled
#
#     - set <chemin> <valeur>
#         Modifie une valeur via config.set(chemin, valeur)
#         Conversion “intelligente” des types :
#           * true/on/yes  -> True
#           * false/off/no -> False
#           * numériques   -> int ou float
#           * sinon        -> str
#
#     - leds on|off
#         Active/désactive les LEDs (config.set("leds.enabled", ...))
#
#     - leds brightness [0-1]
#         Affiche la luminosité actuelle si non fournie,
#         sinon force la valeur dans [0.0, 1.0] puis sauvegarde.
#
#     - reset
#         Réinitialise config._config à DEFAULT_CONFIG (copie) puis config.save()
#
#  Fonctions utilitaires :
#     - afficher_aide() : banner + usage + liste des commandes
#     - afficher_config(section=None) : rendu d’un dict complet/section
#     - afficher_dict(d, indent=0) : affichage récursif avec icônes (✅/❌/📌/📁)
#
#  Dépendances :
#     - config_manager.get_config() : accès singleton config + méthodes get/set/save
#     - DEFAULT_CONFIG (importé uniquement dans la commande reset)
#
#  Notes :
#     - La commande reset modifie directement config._config puis appelle save().
#     - Le CLI n’effectue pas de validation métier avancée (hors clamp brightness),
#       il délègue la cohérence globale à config_manager.
# ============================================================================

import sys
from config_manager import get_config


def afficher_aide():
    """Affiche l'aide du script"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          Configuration du robot CUBOTino - Gestionnaire       ║
╚═══════════════════════════════════════════════════════════════╝

USAGE:
    python config_cli.py [commande] [options]

COMMANDES:
    show                  Affiche toute la configuration
    show [section]        Affiche une section (leds, camera, servos, etc.)
    
    get [chemin]          Récupère une valeur (ex: leds.enabled)
    set [chemin] [valeur] Modifie une valeur (ex: leds.brightness 0.5)
    
    leds on|off           Active/désactive les LEDs
    leds brightness [0-1] Change la luminosité
    
    reset                 Réinitialise la configuration par défaut

EXEMPLES:
    python config_cli.py show
    python config_cli.py show leds
    python config_cli.py get leds.enabled
    python config_cli.py set leds.brightness 0.8
    python config_cli.py leds on
    python config_cli.py leds brightness 0.5
    python config_cli.py reset
    """)


def afficher_config(section=None):
    """Affiche la configuration complète ou une section"""
    config = get_config()
    
    if section:
        section_data = config.get_section(section)
        if section_data:
            print(f"\n📋 Configuration de la section '{section}':")
            print("─" * 50)
            afficher_dict(section_data, indent=0)
        else:
            print(f"❌ Section '{section}' non trouvée")
    else:
        print("\n📋 Configuration complète:")
        print("─" * 50)
        afficher_dict(config._config, indent=0)


def afficher_dict(d, indent=0):
    """Affiche un dictionnaire de manière lisible"""
    for key, value in d.items():
        if isinstance(value, dict):
            print("  " * indent + f"📁 {key}:")
            afficher_dict(value, indent + 1)
        else:
            icon = "✅" if value == True else "❌" if value == False else "📌"
            print("  " * indent + f"{icon} {key}: {value}")


def main():
    """Fonction principale du CLI"""
    if len(sys.argv) < 2:
        afficher_aide()
        return
    
    commande = sys.argv[1].lower()
    config = get_config()
    
    # Commande: show
    if commande == "show":
        if len(sys.argv) > 2:
            afficher_config(sys.argv[2])
        else:
            afficher_config()
    
    # Commande: get
    elif commande == "get":
        if len(sys.argv) < 3:
            print("❌ Usage: python config_cli.py get [chemin]")
            return
        
        chemin = sys.argv[2]
        valeur = config.get(chemin)
        
        if valeur is not None:
            print(f"📌 {chemin} = {valeur}")
        else:
            print(f"❌ Clé '{chemin}' non trouvée")
    
    # Commande: set
    elif commande == "set":
        if len(sys.argv) < 4:
            print("❌ Usage: python config_cli.py set [chemin] [valeur]")
            return
        
        chemin = sys.argv[2]
        valeur_str = sys.argv[3]
        
        # Conversion intelligente du type
        if valeur_str.lower() in ['true', 'on', 'yes']:
            valeur = True
        elif valeur_str.lower() in ['false', 'off', 'no']:
            valeur = False
        elif valeur_str.replace('.', '').replace('-', '').isdigit():
            valeur = float(valeur_str) if '.' in valeur_str else int(valeur_str)
        else:
            valeur = valeur_str
        
        config.set(chemin, valeur)
        print(f"✅ {chemin} = {valeur}")
    
    # Commande: leds
    elif commande == "leds":
        if len(sys.argv) < 3:
            print("❌ Usage: python config_cli.py leds [on|off|brightness]")
            return
        
        sous_commande = sys.argv[2].lower()
        
        if sous_commande in ["on", "off"]:
            activer = (sous_commande == "on")
            config.set("leds.enabled", activer)
            print(f"{'✅ LEDs activées' if activer else '🔴 LEDs désactivées'}")
        
        elif sous_commande == "brightness":
            if len(sys.argv) < 4:
                luminosite_actuelle = config.get("leds.brightness")
                print(f"💡 Luminosité actuelle : {luminosite_actuelle}")
                print("Usage: python config_cli.py leds brightness [0-1]")
                return
            
            try:
                luminosite = float(sys.argv[3])
                luminosite = max(0.0, min(1.0, luminosite))
                config.set("leds.brightness", luminosite)
                print(f"💡 Luminosité changée : {luminosite}")
            except ValueError:
                print("❌ La luminosité doit être un nombre entre 0 et 1")
        
        else:
            print(f"❌ Sous-commande '{sous_commande}' inconnue")
    
    # Commande: reset
    elif commande == "reset":
        from config_manager import DEFAULT_CONFIG
        config._config = DEFAULT_CONFIG.copy()
        config.save()
        print("✅ Configuration réinitialisée aux valeurs par défaut")
    
    # Commande: help
    elif commande in ["help", "-h", "--help"]:
        afficher_aide()
    
    # Commande inconnue
    else:
        print(f"❌ Commande '{commande}' inconnue")
        print("Utilisez 'python config_cli.py help' pour voir l'aide")


if __name__ == "__main__":
    main()