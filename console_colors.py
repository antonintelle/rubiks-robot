# ============================================================================
#  console_colors.py
#  -----------------
#  Utilitaire pour affichage coloré multiplateforme (Linux / Windows)
#  Utilise colorama pour supporter les codes ANSI sur tous les systèmes.
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
