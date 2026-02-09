#!/bin/bash
# ============================================================
#  4_test_ecran.sh
#  Lance l’interface texte (mode terminal) pour tester le TFT
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
