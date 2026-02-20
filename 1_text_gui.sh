#!/bin/bash
<<<<<<< HEAD
# ============================================================================
#  main_text_gui.sh  (alias: 1_text_gui.sh)
#  ---------------------------------------
#  Objectif :
#     Script de lancement de l’interface **texte** du projet Rubik’s Cube
#     en s’assurant que :
#       - le projet est bien présent dans le bon dossier,
#       - l’environnement virtuel `rubik-env` est disponible,
#       - le lancement se fait avec le Python du venv,
#       - l’exécution est faite via `sudo -E` (nécessaire pour NeoPixel / /dev/mem).
#
#  Entrée principale :
#     - Exécution directe :
#         ./main_text_gui.sh
#         -> Lance : sudo -E ~/rubik-env/bin/python3 text_gui.py
#
#  Paramètres / chemins utilisés :
#     - VENV_DIR    = "$HOME/rubik-env"
#     - PROJECT_DIR = "$HOME/rubiks-robot"
#     - SCRIPT      = "text_gui.py"
#     - VENV_PY     = "$VENV_DIR/bin/python3"
#
#  Sécurité / vérifications :
#     1) Vérifie que $VENV_PY existe et est exécutable, sinon exit 1.
#     2) Vérifie que $PROJECT_DIR existe (cd), sinon exit 1.
#     3) Vérifie que text_gui.py est présent dans le dossier projet, sinon exit 1.
#
#  Notes :
#     - `sudo -E` conserve l’environnement (utile si variables/venv nécessaires).
#     - Si tu n’utilises pas de NeoPixel, tu peux retirer sudo et lancer directement
#       "$VENV_PY" "$SCRIPT".
# ============================================================================

echo "🚀 Lancement de l’interface texte du solveur Rubik's Cube..."

VENV_DIR="$HOME/rubik-env"
PROJECT_DIR="$HOME/rubiks-robot"
SCRIPT="text_gui.py"
VENV_PY="$VENV_DIR/bin/python3"

# --- Vérification venv ---
if [ ! -x "$VENV_PY" ]; then
    echo "❌ Python du venv introuvable/exécutable : $VENV_PY"
    echo "👉 Vérifie ton venv : $VENV_DIR"
=======
# ============================================================
#  main_text_gui.sh
#  Lance l’interface texte (mode terminal) du solveur Rubik's Cube
#  Compatible Raspberry Pi OS + environnement rubik-env
# ============================================================

echo "🚀 Lancement de l’interface texte du solveur Rubik's Cube..."

# --- Activation de l'environnement virtuel ---
if [ -d "$HOME/rubik-env" ]; then
    source "$HOME/rubik-env/bin/activate"
else
    echo "❌ Environnement virtuel non trouvé : ~/rubik-env"
    echo "👉 Exécute d'abord : ./0_install_pipeline_v4.sh"
>>>>>>> screen-gui
    exit 1
fi

# --- Navigation vers le dossier du projet ---
<<<<<<< HEAD
cd "$PROJECT_DIR" || {
    echo "❌ Projet introuvable : $PROJECT_DIR"
=======
cd "$HOME/rubik/pipeline-complet-rubik" || {
    echo "❌ Projet introuvable : ~/rubik/pipeline-complet-rubik"
    deactivate
>>>>>>> screen-gui
    exit 1
}

# --- Vérification du script principal ---
<<<<<<< HEAD
if [ ! -f "$SCRIPT" ]; then
    echo "❌ Fichier $SCRIPT introuvable dans le projet."
    exit 1
fi

# --- Lancement (NeoPixel => besoin sudo pour /dev/mem) ---
echo "🖥️  Démarrage de $SCRIPT (avec sudo, python du venv)..."
sudo -E "$VENV_PY" "$SCRIPT"

=======
if [ ! -f "text_gui.py" ]; then
    echo "❌ Fichier text_gui.py introuvable dans le projet."
    deactivate
    exit 1
fi

# --- Lancement du GUI texte ---
echo "🖥️  Démarrage de text_gui.py..."
python3 text_gui.py

# --- Désactivation du venv ---
deactivate
>>>>>>> screen-gui
echo "✅ Fin du programme (interface texte)."
