#!/bin/bash
# ============================================================
#  main_gui_robot.sh
#  Lance l’interface graphique Tkinter du robot Rubik's Cube
#  Compatible Raspberry Pi OS + environnement rubik-env
# ============================================================

echo "🚀 Lancement de l'interface graphique du robot..."

# --- Activation de l'environnement virtuel ---
if [ -d "$HOME/rubik-env" ]; then
    source "$HOME/rubik-env/bin/activate"
else
    echo "❌ Environnement virtuel non trouvé : ~/rubik-env"
    echo "👉 Exécute d'abord : ./0_install_pipeline_v4.sh"
    exit 1
fi

# --- Navigation vers le dossier du projet ---
cd "$HOME/rubik/pipeline-complet-rubik" || {
    echo "❌ Projet introuvable : ~/rubik/pipeline-complet-rubik"
    deactivate
    exit 1
}

# --- Vérification du script principal ---
if [ ! -f "tkinter_gui_robot.py" ]; then
    echo "❌ Fichier tkinter_gui_robot.py introuvable dans le projet."
    deactivate
    exit 1
fi

# --- Lancement du GUI ---
echo "🪟 Démarrage de tkinter_gui_robot.py..."
python3 tkinter_gui_robot.py

# --- Désactivation du venv ---
deactivate
echo "✅ Fin du programme (GUI robot)."
