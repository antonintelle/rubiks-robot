#!/bin/bash
# ============================================================
#  4_test_moteur.sh
#  Lance l’interface texte (mode terminal) pour tester le moteur
# ============================================================

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
cd "$HOME/rubik/pipeline-complet-rubik" || {
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
