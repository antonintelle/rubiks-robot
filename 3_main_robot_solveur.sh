#!/bin/bash
# ============================================================
#  main_robot_solveur.sh
#  Lance le mode robot du solveur Rubik's Cube
# ============================================================

echo "🤖 Lancement du solveur Rubik's Cube (mode robot)..."

# --- Activation de l'environnement virtuel ---
if [ -d "$HOME/rubik-env" ]; then
    source "$HOME/rubik-env/bin/activate"
else
    echo "❌ Environnement virtuel non trouvé : ~/rubik-env"
    echo "➡️  Lance d'abord 0_install_pipeline.sh"
    exit 1
fi

# --- Aller dans le dossier projet ---
cd "$HOME/rubik/pipeline-complet-rubik" || {
    echo "❌ Dossier du projet introuvable."
    exit 1
}

# --- Lancer le script Python ---
python3 main_robot_solveur.py

# --- Désactivation propre ---
deactivate
echo "✅ Fin du mode robot."
