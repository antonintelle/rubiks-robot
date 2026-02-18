#!/usr/bin/env python3
# ============================================================================
#  console_colors.py
#  -----------------
#  Objectif :
#     Petit utilitaire d’affichage console **coloré et lisible** (Linux / Windows),
#     afin d’uniformiser les sorties texte des scripts du projet.
#     S’appuie sur `colorama` pour garantir le support des codes ANSI, notamment
#     sous Windows.
#
#  Entrées principales (API) :
#     - print_header(title: str)
#         Affiche un en-tête “bannière” : lignes cyan + titre centré en jaune.
#
#     - print_menu_option(index: str, text: str, color=Fore.GREEN)
#         Affiche une option de menu stylée (index coloré + texte en blanc).
#
#     - print_warning(msg: str)
#         Affiche un warning préfixé ⚠️, en jaune.
#
#     - print_error(msg: str)
#         Affiche une erreur préfixée ❌, en rouge.
#
#     - print_success(msg: str)
#         Affiche un succès préfixé ✅, en vert.
#
#  Initialisation :
#     - colorama.init(autoreset=True)
#       -> évite de “polluer” les prints suivants (reset automatique des styles).
#
#  Dépendances :
#     - colorama (init, Fore, Style)
#
#  Notes :
#     - Module volontairement minimal : uniquement des helpers d’affichage,
#       sans logique métier.
# ============================================================================


from colorama import init, Fore, Style

# Initialisation automatique (Windows + Linux)
init(autoreset=True)

def print_header(title: str):
    """Affiche un en-tête stylé et coloré."""
    line = "=" * 60
    print(Fore.CYAN + Style.BRIGHT + line)
    print(Fore.YELLOW + Style.BRIGHT + title.center(60))
    print(Fore.CYAN + Style.BRIGHT + line + Style.RESET_ALL)

def print_menu_option(index: str, text: str, color=Fore.GREEN):
    """Affiche une ligne de menu stylée."""
    print(color + f"{index}. " + Fore.WHITE + text)

def print_warning(msg: str):
    print(Fore.YELLOW + Style.BRIGHT + "⚠️  " + msg)

def print_error(msg: str):
    print(Fore.RED + Style.BRIGHT + "❌ " + msg)

def print_success(msg: str):
    print(Fore.GREEN + Style.BRIGHT + "✅ " + msg)
