#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "🧹 Désinstallation du pipeline Rubik's Cube"
echo "============================================================"
echo

read -p "⚠️  Cette action va supprimer l'environnement Python 'env' et les caches. Continuer ? (o/N) : " confirm
confirm=${confirm,,}
if [[ "$confirm" != "o" && "$confirm" != "oui" ]]; then
    echo "❌ Opération annulée."
    exit 0
fi

if [ -d "./env" ]; then
    echo "🧱 Suppression de l'environnement virtuel..."
    rm -rf ./env
else
    echo "ℹ️  Aucun environnement virtuel trouvé."
fi

echo "🧹 Nettoyage des fichiers temporaires..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

if [ -d "./logs" ]; then
    echo "🗑️  Suppression du dossier logs..."
    rm -rf ./logs
fi

if [ -d "./.pytest_cache" ]; then
    echo "🧪 Suppression du cache Pytest..."
    rm -rf "./.pytest_cache"
fi

echo
echo "✅ Désinstallation terminée avec succès."
echo "============================================================"
