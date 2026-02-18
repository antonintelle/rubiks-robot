#!/bin/bash
# ============================================================================
#  3_main_robot_solveur.sh  (main_robot_solveur.sh)
#  -----------------------------------------------
#  Objectif :
#     Script de lancement “clé en main” du **mode robot** : exécute le pipeline
#     complet (capture → processing → solve → exécution) via `main_robot_solveur.py`,
#     après activation de l’environnement virtuel du projet.
#
#  Entrée principale :
#     - Exécution directe :
#         ./3_main_robot_solveur.sh
#         -> Lance : python3 main_robot_solveur.py
#
#  Étapes principales :
#     1) Affiche un message de démarrage (mode robot).
#     2) Active le venv :
#        - source ~/rubik-env/bin/activate
#        - si le venv est absent : affiche une erreur + conseille 0_install_pipeline.sh.
#     3) Se place dans le dossier projet :
#        - cd ~/rubiks-robot
#        - si absent : erreur + exit.
#     4) Lance le programme :
#        - python3 main_robot_solveur.py
#     5) Désactive le venv :
#        - deactivate
#        - affiche un message de fin.
#
#  Pré-requis :
#     - venv présent : ~/rubik-env (créé par 0_install_pipeline.sh)
#     - projet cloné : ~/rubiks-robot
#     - script Python : main_robot_solveur.py
# ============================================================================


echo "🤖 Lancement du solveur Rubik's Cube (mode robot)..."

VENV_DIR="$HOME/rubik-env"
PROJECT_DIR="$HOME/rubiks-robot"
SCRIPT="main_robot_solveur.py"
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


echo "✅ Fin du mode robot."