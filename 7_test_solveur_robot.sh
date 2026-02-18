#!/bin/bash
# ============================================================================
#  7_test_solveur_robot.sh
#  -----------------------
#  Objectif :
#     Script de lancement “quick test” pour vérifier l’exécution **interactive**
#     d’une séquence Singmaster sur le robot, via `test_solveur_robot.py`.
#     Il s’assure que :
#       - l’environnement virtuel `rubik-env` est présent,
#       - le projet est disponible dans le bon dossier,
#       - le script de test existe,
#       - le lancement se fait avec le Python du venv (et via sudo -E si nécessaire).
#
#  Entrée principale :
#     - Exécution directe :
#         ./7_test_solveur_robot.sh
#         -> Lance : sudo -E ~/rubik-env/bin/python3 test_solveur_robot.py
#
#  Paramètres / chemins utilisés :
#     - VENV_DIR    = "$HOME/rubik-env"
#     - PROJECT_DIR = "$HOME/rubiks-robot"
#     - SCRIPT      = "test_solveur_robot.py"
#     - VENV_PY     = "$VENV_DIR/bin/python3"
#
#  Étapes principales :
#     1) Vérifie que le Python du venv existe et est exécutable.
#     2) Se place dans le dossier projet (cd).
#     3) Vérifie la présence du script de test.
#     4) Lance le test avec `sudo -E` :
#        - utile si l’exécution nécessite des droits matériels (ex: NeoPixel / /dev/mem).
#     5) Affiche un message de fin.
#
#  Notes :
#     - Le commentaire “main_text_gui.sh” en en-tête est un héritage de copie :
#       ce script lance bien `test_solveur_robot.py`.
#     - Si tu n’as pas besoin de privilèges root pour ce test, tu peux remplacer
#       `sudo -E` par un appel direct à "$VENV_PY".
# ============================================================================


echo "🚀 Lancement de l’interface texte du solveur Rubik's Cube..."

VENV_DIR="$HOME/rubik-env"
PROJECT_DIR="$HOME/rubiks-robot"
SCRIPT="test_solveur_robot.py"
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
