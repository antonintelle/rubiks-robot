#!/bin/bash
# ============================================================================
#  4_test_ecran.sh
#  ---------------
#  Objectif :
#     Script de lancement “quick test” pour vérifier l’affichage TFT via le module
#     `ecran/tft.py`, en activant l’environnement virtuel du projet puis en lançant
#     l’interface de test en mode terminal.
#
#  Entrée principale :
#     - Exécution directe :
#         ./4_test_ecran.sh
#         -> Lance : python3 ecran/tft.py
#
#  Étapes principales :
#     1) Active le venv :
#        - source ~/rubik-env/bin/activate
#        - si absent : affiche une erreur + conseille 0_install_pipeline.sh.
#
#     2) Se place dans le dossier projet :
#        - cd ~/rubiks-robot
#        - si absent : erreur + deactivate + exit.
#
#     3) Vérifie la présence du script de test :
#        - ecran/tft.py doit exister, sinon erreur + deactivate + exit.
#
#     4) Lance le test TFT :
#        - python3 ecran/tft.py
#
#     5) Désactive le venv et termine proprement :
#        - deactivate
#
#  Notes :
#     - Ce script sert uniquement à tester l’écran (ou le driver TFT) indépendamment
#       du pipeline complet.
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
if [ ! -f "ecran/tft.py" ]; then
    echo "❌ Fichier ecran/tft.py introuvable dans le projet."
    deactivate
    exit 1
fi

# --- Lancement du GUI texte ---
echo "🖥️  Démarrage de ecran/tft.py..."
python3 ecran/tft.py

# --- Désactivation du venv ---
deactivate
echo "✅ Fin du programme (interface texte)."
