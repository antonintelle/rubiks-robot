#!/bin/bash
# ============================================================================
#  5_test_moteur.sh
#  ---------------
#  Objectif :
#     Script de lancement “quick test” pour valider le **pilotage moteur/servos**
#     du robot via `robot_servo.py`, en activant l’environnement virtuel puis en
#     lançant l’interface de test en mode terminal.
#
#  Entrée principale :
#     - Exécution directe :
#         ./5_test_moteur.sh
#         -> Lance : python3 robot_servo.py
#
#  Étapes principales :
#     1) Affiche un message de démarrage.
#     2) Active le venv :
#        - source ~/rubik-env/bin/activate
#        - si absent : affiche une erreur + conseille 0_install_pipeline.sh, puis exit.
#     3) Se place dans le dossier projet :
#        - cd ~/rubiks-robot
#        - si absent : erreur + deactivate + exit.
#     4) Vérifie la présence du script robot :
#        - robot_servo.py doit exister, sinon erreur + deactivate + exit.
#     5) Lance l’interface de test des servos :
#        - python3 robot_servo.py
#     6) Désactive le venv et termine proprement.
#
#  Notes :
#     - Ce script sert à isoler les tests matériels (pigpio/servos) du reste du pipeline.
#     - Sur Raspberry Pi : `pigpiod` doit être actif pour que robot_servo fonctionne.
# ============================================================================


echo "🚀 Lancement de l’interface de test..."

# --- Activation de l'environnement virtuel ---
if [ -d "$HOME/rubik-env" ]; then
    source "$HOME/rubik-env/bin/activate"
else
    echo "❌ Environnement virtuel non trouvé : ~/rubik-env"
    echo "👉 Exécute d'abord : ./0_install_pipeline.sh"
    exit 1
fi

# --- Navigation vers le dossier du projet ---
cd "$HOME/rubiks-robot" || {
    echo "❌ Projet introuvable : ~/rubik/pipeline-complet-rubik"
    deactivate
    exit 1
}

# --- Vérification du script principal ---
if [ ! -f "robot_servo.py" ]; then
    echo "❌ Fichier robot_servo.py introuvable dans le projet."
    deactivate
    exit 1
fi

# --- Lancement du GUI texte ---
echo "🖥️  Démarrage de robot_servo.py..."
python3 robot_servo.py

# --- Désactivation du venv ---
deactivate
echo "✅ Fin du programme (interface texte)."
