#!/bin/bash
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
    exit 1
fi

# --- Navigation vers le dossier du projet ---
cd "$HOME/rubik/pipeline-complet-rubik" || {
    echo "❌ Projet introuvable : ~/rubik/pipeline-complet-rubik"
    deactivate
    exit 1
}

# --- Vérification du script principal ---
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
echo "✅ Fin du programme (interface texte)."
