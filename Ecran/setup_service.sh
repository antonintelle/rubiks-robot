#!/bin/bash

# ========================================
# Générateur rubiks-gui.service + venv
# UNIQUEMENT root (sudo) requis
# ========================================

# VÉRIFICATION ROOT
if [[ $EUID -ne 0 ]]; then
   echo "❌ Ce script doit être lancé avec sudo !"
   echo "💡 Usage: sudo ./setup_service.sh"
   exit 1
fi

echo "🔧 [ROOT] Installation Rubiks GUI Service + Venv..."

# 1. DÉTECTION DU PROJET (même dossier que ce script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_PATH="$PROJECT_DIR/rubiks_env"
MAIN_SCRIPT="$PROJECT_DIR/main.py"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"

echo "📁 Projet détecté : $PROJECT_DIR"

# VÉRIFICATIONS
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ main.py manquant dans $PROJECT_DIR"
    exit 1
fi

if [ ! -f "$REQUIREMENTS" ]; then
    echo "❌ requirements.txt manquant dans $PROJECT_DIR"
    exit 1
fi

USERNAME=$(logname 2>/dev/null || whoami)

echo "✅ Utilisateur : $USERNAME"
echo "✅ main.py : OK"
echo "✅ requirements.txt : OK"

# 2. INSTALLER/CREUSER VENV
echo "🐍 Installation venv + dépendances..."
if [ ! -d "$VENV_PATH" ]; then
    echo "   Création venv..."
    apt update -qq
    apt install -y python3-venv python3-pip >/dev/null
    python3 -m venv "$VENV_PATH"
fi

# Activer venv et installer
$VENV_PATH/bin/pip install --upgrade pip >/dev/null
$VENV_PATH/bin/pip install -r "$REQUIREMENTS" -q

echo "✅ Venv installé : $VENV_PATH"

# 3. GÉNÉRER LE SERVICE
cat > /etc/systemd/system/rubiks-gui.service << EOF
[Unit]
Description=Interface graphique Rubiks Cube via GPIO
After=multi-user.target

[Service]
Type=simple
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_PATH/bin/python $MAIN_SCRIPT
ExecStop=/usr/bin/pkill -f main.py
Restart=on-failure
RestartSec=1s
StandardOutput=journal
StandardError=journal
TimeoutStartSec=30s
TimeoutStopSec=10s

[Install]
WantedBy=multi-user.target
EOF

# 4. ACTIVATION AUTOMATIQUE
systemctl daemon-reload
systemctl enable rubiks-gui.service
systemctl start rubiks-gui.service

echo "🚀 Service installé et DÉMARRÉ !"
echo ""
echo "📊 COMMANDES:"
echo "   Logs live    : journalctl -u rubiks-gui.service -f"
echo "   Arrêter      : systemctl stop rubiks-gui.service"
echo "   Redémarrer   : systemctl restart rubiks-gui.service"
echo "   Statut       : systemctl status rubiks-gui.service"
echo ""
echo "🎉 Installation TERMINÉE !"
