#!/bin/bash
<<<<<<< HEAD
# ============================================================================
#  INSTALLER.sh
#  ------------
#  Objectif :
#     Script “wrapper” ultra simple pour lancer l’installation du projet Rubik’s
#     Cube en déléguant tout le travail au script principal `0_install_pipeline.sh`.
#
#  Entrée principale :
#     - Exécution directe :
#         ./INSTALLER.sh
#         -> Lance : bash ./0_install_pipeline.sh
#
#  Comportement :
#     1) Active le mode strict :
#        - set -e : stoppe immédiatement au premier échec.
#     2) Se place dans le répertoire du script :
#        - cd "$(dirname "$0")"
#     3) Vérifie la présence de 0_install_pipeline.sh :
#        - si présent : l’exécute
#        - sinon      : affiche une erreur et quitte (exit 1)
#
#  Notes :
#     - À utiliser comme point d’entrée “install” unique pour éviter d’appeler
#       directement 0_install_pipeline.sh (plus simple pour l’utilisateur).
# ============================================================================

=======
# ============================================================
#  INSTALLER.sh
#  Lance 0_install_pipeline.sh pour le pipeline Rubik's Cube
# ============================================================
>>>>>>> screen-gui

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
