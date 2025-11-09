#!/bin/bash
# ============================================================
#  INSTALLER.sh
#  Lance 0_install_pipeline.sh pour le pipeline Rubik's Cube
# ============================================================

set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "🚀 Installation du pipeline Rubik's Cube (Linux / Raspberry Pi)"
echo "============================================================"
echo

if [ -f "./0_install_pipeline.sh" ]; then
    echo "⚙️  Lancement de 0_install_pipeline.sh ..."
    bash "./0_install_pipeline.sh"
else
    echo "❌ Fichier 0_install_pipeline.sh introuvable."
    exit 1
fi

echo
echo "✅ Installation terminée."
echo "============================================================"
