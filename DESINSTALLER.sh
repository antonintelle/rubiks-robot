#!/bin/bash
<<<<<<< HEAD
# ============================================================================
#  DESINSTALLER.sh
#  ---------------
#  Objectif :
#     Désinstaller proprement le pipeline Rubik’s Cube (symétrique de INSTALLER.sh)
#     en supprimant :
#       - l’environnement virtuel (~/rubik-env),
#       - les caches Python (__pycache__, *.pyc, *.pyo),
#       - les dossiers temporaires et logs (tmp/, logs/),
#       - les caches de tests (.pytest_cache, .coverage*),
#     tout en gérant les fichiers potentiellement créés avec sudo (owner root)
#     et en proposant des options interactives (garder/supprimer calibrations,
#     garder/supprimer captures, désactiver pigpiod, corriger permissions).
#
#  Entrée principale :
#     - Exécution directe :
#         ./DESINSTALLER.sh
#
#  Fonctionnement (résumé des étapes) :
#     1) Demande confirmation utilisateur (o/oui) avant suppression.
#     2) Supprime le venv : ~/rubik-env (rm -rf).
#     3) Nettoie __pycache__ / *.pyc / *.pyo (tentative user puis fallback sudo).
#     4) Supprime logs/ et tmp/ (tentative user puis fallback sudo).
#     5) Supprime caches de test (.pytest_cache, .coverage, .coverage.*).
#     6) Détecte les fichiers appartenant à root et propose leur suppression (sudo).
#     7) Propose de supprimer ou conserver les calibrations :
#        - rubiks_calibration.json
#        - rubiks_color_calibration.json
#     8) Propose de supprimer ou conserver les captures (captures/*).
#     9) Propose de désactiver et stopper pigpiod (systemctl).
#    10) Propose de corriger les permissions restantes (chown -R $USER).
#
#  Variables principales :
#     - VENV_DIR    = "$HOME/rubik-env"
#     - PROJECT_DIR = "$(pwd)"  (répertoire du projet, après cd dans le dossier script)
#
#  Notes :
#     - Script interactif : plusieurs prompts “o/N”.
#     - Utilise sudo uniquement si nécessaire (fichiers root, dossiers créés via sudo).
# ============================================================================

=======
>>>>>>> screen-gui
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "🧹 Désinstallation du pipeline Rubik's Cube"
echo "============================================================"
echo

<<<<<<< HEAD
# Variables (cohérentes avec 0_install_pipeline.sh)
VENV_DIR="$HOME/rubik-env"
PROJECT_DIR="$(pwd)"

echo "📋 Éléments à supprimer :"
echo "   • Environnement virtuel : $VENV_DIR"
echo "   • Caches Python (__pycache__, *.pyc)"
echo "   • Logs et fichiers temporaires (y compris ceux créés avec sudo)"
echo "   • Cache Pytest"
echo

# Confirmation utilisateur
read -p "⚠️  Confirmer la désinstallation ? (o/N) : " confirm
=======
read -p "⚠️  Cette action va supprimer l'environnement Python 'env' et les caches. Continuer ? (o/N) : " confirm
>>>>>>> screen-gui
confirm=${confirm,,}
if [[ "$confirm" != "o" && "$confirm" != "oui" ]]; then
    echo "❌ Opération annulée."
    exit 0
fi

<<<<<<< HEAD
echo
echo "🚀 Lancement de la désinstallation..."
echo

# ============================================================
# 1️⃣  Suppression de l'environnement virtuel
# ============================================================
if [ -d "$VENV_DIR" ]; then
    echo "🧱 Suppression de l'environnement virtuel..."
    rm -rf "$VENV_DIR"
    echo "   ✅ $VENV_DIR supprimé"
else
    echo "ℹ️  Aucun environnement virtuel trouvé à $VENV_DIR"
fi

# ============================================================
# 2️⃣  Nettoyage des caches Python (avec et sans sudo)
# ============================================================
echo
echo "🧹 Nettoyage des caches Python..."

# Tentative sans sudo d'abord
PYCACHE_COUNT=$(find "$PROJECT_DIR" -type d -name "__pycache__" 2>/dev/null | wc -l)
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    echo "   Suppression __pycache__ (utilisateur)..."
    find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Vérifier s'il en reste (créés avec sudo)
    REMAINING=$(find "$PROJECT_DIR" -type d -name "__pycache__" 2>/dev/null | wc -l)
    if [ "$REMAINING" -gt 0 ]; then
        echo "   ⚠️  $REMAINING __pycache__ nécessitent sudo..."
        sudo find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    fi
    echo "   ✅ __pycache__ supprimés"
else
    echo "   ℹ️  Aucun dossier __pycache__ trouvé"
fi

# Fichiers .pyc
PYC_COUNT=$(find "$PROJECT_DIR" -type f -name "*.pyc" 2>/dev/null | wc -l)
if [ "$PYC_COUNT" -gt 0 ]; then
    echo "   Suppression .pyc (utilisateur)..."
    find "$PROJECT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Vérifier s'il en reste (créés avec sudo)
    REMAINING=$(find "$PROJECT_DIR" -type f -name "*.pyc" 2>/dev/null | wc -l)
    if [ "$REMAINING" -gt 0 ]; then
        echo "   ⚠️  $REMAINING .pyc nécessitent sudo..."
        sudo find "$PROJECT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    fi
    echo "   ✅ Fichiers .pyc supprimés"
else
    echo "   ℹ️  Aucun fichier .pyc trouvé"
fi

# Fichiers .pyo
find "$PROJECT_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
sudo find "$PROJECT_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true

# ============================================================
# 3️⃣  Suppression des logs et temporaires (avec sudo)
# ============================================================
echo
echo "🗑️  Suppression des fichiers temporaires..."

if [ -d "$PROJECT_DIR/logs" ]; then
    # Essayer sans sudo d'abord
    rm -rf "$PROJECT_DIR/logs" 2>/dev/null || sudo rm -rf "$PROJECT_DIR/logs"
    echo "   ✅ Dossier logs/ supprimé"
else
    echo "   ℹ️  Pas de dossier logs/"
fi

if [ -d "$PROJECT_DIR/tmp" ]; then
    # Essayer sans sudo d'abord
    rm -rf "$PROJECT_DIR/tmp" 2>/dev/null || sudo rm -rf "$PROJECT_DIR/tmp"
    echo "   ✅ Dossier tmp/ supprimé"
else
    echo "   ℹ️  Pas de dossier tmp/"
fi

# ============================================================
# 4️⃣  Suppression des caches de test
# ============================================================
echo
echo "🧪 Suppression des caches de test..."

if [ -d "$PROJECT_DIR/.pytest_cache" ]; then
    rm -rf "$PROJECT_DIR/.pytest_cache" 2>/dev/null || sudo rm -rf "$PROJECT_DIR/.pytest_cache"
    echo "   ✅ Cache Pytest supprimé"
else
    echo "   ℹ️  Pas de cache Pytest"
fi

if [ -d "$PROJECT_DIR/.coverage" ]; then
    rm -rf "$PROJECT_DIR/.coverage" 2>/dev/null || sudo rm -rf "$PROJECT_DIR/.coverage"
    echo "   ✅ Cache Coverage supprimé"
fi

# Fichiers de test
find "$PROJECT_DIR" -type f -name ".coverage.*" -delete 2>/dev/null || true
sudo find "$PROJECT_DIR" -type f -name ".coverage.*" -delete 2>/dev/null || true

# ============================================================
# 5️⃣  Nettoyage des fichiers créés par sudo (captures, etc.)
# ============================================================
echo
echo "🔒 Vérification des fichiers créés avec sudo..."

# Compter les fichiers appartenant à root
ROOT_FILES=$(find "$PROJECT_DIR" -user root 2>/dev/null | wc -l)
if [ "$ROOT_FILES" -gt 0 ]; then
    echo "   ⚠️  $ROOT_FILES fichier(s) appartenant à root détectés"
    echo "   📁 Exemples :"
    find "$PROJECT_DIR" -user root 2>/dev/null | head -5
    echo
    read -p "   Supprimer ces fichiers avec sudo ? (o/N) : " del_root
    del_root=${del_root,,}
    if [[ "$del_root" = "o" || "$del_root" = "oui" ]]; then
        # Supprimer fichiers root dans les dossiers connus
        for dir in captures logs tmp; do
            if [ -d "$PROJECT_DIR/$dir" ]; then
                sudo find "$PROJECT_DIR/$dir" -user root -delete 2>/dev/null || true
            fi
        done
        echo "   ✅ Fichiers root supprimés"
    else
        echo "   ℹ️  Fichiers root conservés"
        echo "   💡 Pour les supprimer manuellement :"
        echo "      sudo find $PROJECT_DIR -user root -delete"
    fi
else
    echo "   ✅ Aucun fichier root trouvé"
fi

# ============================================================
# 6️⃣  Question : Garder les calibrations ?
# ============================================================
echo
echo "📊 Fichiers de calibration :"

CALIB_FILES=(
    "rubiks_calibration.json"
    "rubiks_color_calibration.json"
)

HAS_CALIB=false
for file in "${CALIB_FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        echo "   • $file"
        HAS_CALIB=true
    fi
done

if [ "$HAS_CALIB" = true ]; then
    echo
    read -p "⚠️  Supprimer aussi les fichiers de calibration ? (o/N) : " del_calib
    del_calib=${del_calib,,}
    if [[ "$del_calib" = "o" || "$del_calib" = "oui" ]]; then
        for file in "${CALIB_FILES[@]}"; do
            if [ -f "$PROJECT_DIR/$file" ]; then
                rm -f "$PROJECT_DIR/$file" 2>/dev/null || sudo rm -f "$PROJECT_DIR/$file"
                echo "   ✅ $file supprimé"
            fi
        done
    else
        echo "   ℹ️  Fichiers de calibration conservés"
    fi
else
    echo "   ℹ️  Aucun fichier de calibration trouvé"
fi

# ============================================================
# 7️⃣  Question : Nettoyer les images de test ?
# ============================================================
echo
if [ -d "$PROJECT_DIR/captures" ] && [ "$(ls -A "$PROJECT_DIR/captures" 2>/dev/null)" ]; then
    CAPTURE_COUNT=$(ls -1 "$PROJECT_DIR/captures" 2>/dev/null | wc -l)
    echo "📸 $CAPTURE_COUNT image(s) de test dans captures/"
    read -p "   Supprimer les captures ? (o/N) : " del_captures
    del_captures=${del_captures,,}
    if [[ "$del_captures" = "o" || "$del_captures" = "oui" ]]; then
        # Essayer sans sudo d'abord, puis avec si nécessaire
        rm -rf "$PROJECT_DIR/captures"/* 2>/dev/null || sudo rm -rf "$PROJECT_DIR/captures"/*
        echo "   ✅ Captures supprimées"
    else
        echo "   ℹ️  Captures conservées"
    fi
fi

# ============================================================
# 8️⃣  Optionnel : Désactiver pigpiod
# ============================================================
echo
echo "🔧 Services système :"
if systemctl is-enabled pigpiod >/dev/null 2>&1; then
    echo "   • pigpiod est activé au démarrage"
    read -p "   Désactiver pigpiod ? (o/N) : " disable_pigpiod
    disable_pigpiod=${disable_pigpiod,,}
    if [[ "$disable_pigpiod" = "o" || "$disable_pigpiod" = "oui" ]]; then
        sudo systemctl disable pigpiod
        sudo systemctl stop pigpiod
        echo "   ✅ pigpiod désactivé et arrêté"
    else
        echo "   ℹ️  pigpiod reste activé"
    fi
else
    echo "   ℹ️  pigpiod n'est pas activé"
fi

# ============================================================
# 9️⃣  Correction des permissions restantes
# ============================================================
echo
echo "🔐 Vérification des permissions..."

# Trouver les fichiers/dossiers qui ne sont pas accessibles
PERMISSION_ISSUES=$(find "$PROJECT_DIR" ! -user "$USER" 2>/dev/null | wc -l)
if [ "$PERMISSION_ISSUES" -gt 0 ]; then
    echo "   ⚠️  $PERMISSION_ISSUES fichier(s) avec permissions différentes"
    read -p "   Corriger les permissions (chown vers $USER) ? (o/N) : " fix_perms
    fix_perms=${fix_perms,,}
    if [[ "$fix_perms" = "o" || "$fix_perms" = "oui" ]]; then
        sudo chown -R "$USER:$USER" "$PROJECT_DIR" 2>/dev/null || true
        echo "   ✅ Permissions corrigées"
    else
        echo "   ℹ️  Permissions non modifiées"
    fi
else
    echo "   ✅ Permissions correctes"
fi

# ============================================================
# 🎯  Résumé final
# ============================================================
echo
echo "============================================================"
echo "✅ Désinstallation terminée avec succès"
echo "============================================================"
echo
echo "📋 Résumé :"
echo "   ✅ Environnement virtuel supprimé"
echo "   ✅ Caches Python nettoyés"
echo "   ✅ Fichiers temporaires supprimés"
echo "   ✅ Fichiers sudo gérés"
echo

if [ "$HAS_CALIB" = true ]; then
    if [[ "$del_calib" = "o" || "$del_calib" = "oui" ]]; then
        echo "   ✅ Calibrations supprimées"
    else
        echo "   ℹ️  Calibrations conservées"
    fi
fi

echo
echo "💡 Pour réinstaller :"
echo "   ./INSTALLER.sh"
echo
echo "🔍 Si des fichiers persistent :"
echo "   find . -user root  # Trouver fichiers root"
echo "   sudo chown -R \$USER:\$USER .  # Corriger permissions"
echo
echo "============================================================"
=======
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
>>>>>>> screen-gui
