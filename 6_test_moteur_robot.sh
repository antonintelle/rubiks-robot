#!/bin/bash
# ============================================================================
#  6_test_moteur_robot.sh
#  ----------------------
#  Objectif :
#     Script de lancement “quick test” pour valider rapidement les **mouvements**
#     du robot en exécutant le script de test `test_quick_moves.py`, en s’assurant
#     que :
#       - l’environnement virtuel `rubik-env` est disponible,
#       - le projet est bien présent dans le bon dossier,
#       - l’exécution se fait avec le Python du venv,
#       - le lancement est fait via `sudo -E` (utile si accès matériel requis).
#
#  Entrée principale :
#     - Exécution directe :
#         ./6_test_moteur_robot.sh
#         -> Lance : sudo -E ~/rubik-env/bin/python3 test_quick_moves.py
#
#  Paramètres / chemins utilisés :
#     - VENV_DIR    = "$HOME/rubik-env"
#     - PROJECT_DIR = "$HOME/rubiks-robot"
#     - SCRIPT      = "test_quick_moves.py"
#     - VENV_PY     = "$VENV_DIR/bin/python3"
#
#  Étapes principales :
#     1) Vérifie que le Python du venv existe et est exécutable.
#     2) Se place dans le dossier projet.
#     3) Vérifie la présence du script de test.
#     4) Lance le test avec sudo -E (accès GPIO/NeoPixel selon config).
#
#  Notes :
#     - Le bandeau “main_text_gui.sh” dans le fichier est un héritage de copie :
#       ce script lance en réalité `test_quick_moves.py`.
#     - Si tu n’as pas besoin de privilèges root pour ce test, tu peux remplacer
#       `sudo -E` par un appel direct à "$VENV_PY".
# ============================================================================


echo "🚀 Lancement de l’interface texte du solveur Rubik's Cube..."

VENV_DIR="$HOME/rubik-env"
PROJECT_DIR="$HOME/rubiks-robot"
SCRIPT="test_quick_moves.py"
VENV_PY="$VENV_DIR/bin/python3"

# --- Vérification venv ---
if [ ! -x "$VENV_PY" ]; then
    echo "❌ Python du venv introuvable/exécutable : $VENV_PY"
    echo "👉 Vérifie ton venv : $VENV_DIR"
    exit 1
fi

# --- Navigation vers le dossier du projet ---
cd "$PROJECT_DIR" || {
    echo "❌ Projet introuvable : $PROJECT_DIR"
    exit 1
}

# --- Vérification du script principal ---
if [ ! -f "$SCRIPT" ]; then
    echo "❌ Fichier $SCRIPT introuvable dans le projet."
    exit 1
fi

# --- Lancement (NeoPixel => besoin sudo pour /dev/mem) ---
echo "🖥️  Démarrage de $SCRIPT (avec sudo, python du venv)..."
sudo -E "$VENV_PY" "$SCRIPT"

echo "✅ Fin du programme (interface texte)."
