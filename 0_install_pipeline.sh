#!/bin/bash
# ============================================================
#  0_install_pipeline.sh (v6.0)
#  Installation complète du pipeline Rubik's Cube - Raspberry Pi
#
#  ✅ Réentrant (mode rapide --fast)
#  ✅ Choix interactif : réinstallation complète ou mise à jour
#  ✅ Utilise requirements_pi.txt
#  ✅ Exécute check_dependencies.py
# ============================================================

set -e
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR"

echo "🚀 Lancement depuis : $BASE_DIR"

# ------------------------------------------------------------
# 🧱  Choix utilisateur : reset complet ou update
# ------------------------------------------------------------
VENV_DIR="$HOME/rubik-env"
echo
echo "=============================================="
echo "🧱  Installation Rubik's Cube - Raspberry Pi"
echo "=============================================="
if [ -d "$VENV_DIR" ]; then
    echo "Un environnement virtuel existe déjà à : $VENV_DIR"
    echo
    echo "Que souhaitez-vous faire ?"
    echo "  [1] 🔥 Réinstaller complètement (supprimer et recréer)"
    echo "  [2] ♻️  Mettre à jour (garder l'environnement existant)"
    echo
    read -p "Choix [2 par défaut] : " USER_CHOICE
    USER_CHOICE=${USER_CHOICE:-2}
    if [ "$USER_CHOICE" = "1" ]; then
        echo "🔥 Suppression de l'ancien environnement virtuel..."
        rm -rf "$VENV_DIR"
    else
        echo "♻️ Mise à jour de l'environnement existant."
    fi
else
    echo "Aucun environnement virtuel trouvé, création d'un nouveau."
fi

# ------------------------------------------------------------
# 1️⃣  Mise à jour du système
# ------------------------------------------------------------
if [[ "$1" != "--fast" ]]; then
    echo "📦 Mise à jour du système..."
    sudo apt update -y
    sudo apt full-upgrade -y
else
    echo "⏩ Mode rapide activé : pas de mise à jour système"
fi

# ------------------------------------------------------------
# 2️⃣  Installation des paquets système nécessaires
# ------------------------------------------------------------
echo "⚙️ Installation des paquets système..."
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-opencv \
  python3-picamera2 \
  python3-libcamera \
  libcamera-dev \
  python3-gpiozero \
  python3-colorzero \
  python3-tk \
  python3-pil \
  python3-pil.imagetk \
  python3-numpy \
  python3-matplotlib \
  python3-dev \
  libffi-dev \
  build-essential \
  dos2unix \
  git curl wget pkg-config \
  rpicam-apps \
  python3-spidev \
  python3-rpi.gpio \
  python3-lgpio

echo "🔧 Activation de pigpiod au démarrage..."
sudo systemctl enable pigpiod
echo "ℹ️ pigpiod sera démarré automatiquement au prochain reboot."

echo "🔧 Activation du SPI..."
sudo raspi-config nonint do_spi 0

# ------------------------------------------------------------
# 3️⃣  Création / activation de l’environnement virtuel
# ------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "🧱 Création de l'environnement virtuel rubik-env..."
    python3 -m venv "$VENV_DIR"
else
    echo "♻️ Utilisation de l'environnement virtuel existant."
fi

echo "🔗 Autorisation d’accès aux paquets système dans le venv..."
sed -i 's/include-system-site-packages = .*/include-system-site-packages = true/' "$VENV_DIR/pyvenv.cfg" 2>/dev/null || true
if ! grep -q "include-system-site-packages = true" "$VENV_DIR/pyvenv.cfg"; then
    echo "include-system-site-packages = true" >> "$VENV_DIR/pyvenv.cfg"
fi

source "$VENV_DIR/bin/activate"

# ------------------------------------------------------------
# 4️⃣  Installation / mise à jour des dépendances Python
# ------------------------------------------------------------
echo "🐍 Mise à jour de pip et outils..."
pip install --upgrade pip setuptools wheel

REQ_FILE="$BASE_DIR/requirements_pi.txt"
echo "🔧 Installation des dépendances Python depuis $REQ_FILE..."

if [ -f "$REQ_FILE" ]; then
    pip install --upgrade -r "$REQ_FILE" || true
else
    echo "⚠️ Fichier requirements_pi.txt introuvable, tentative de fallback..."
    pip install Pillow colorama ultralytics kociemba RubikTwoPhase || true
fi

# ------------------------------------------------------------
# 5️⃣  Nettoyage numpy / matplotlib (doublons)
# ------------------------------------------------------------
echo "🧹 Nettoyage des doublons (numpy, matplotlib, picamera2)..."
pip uninstall -y numpy matplotlib opencv-python picamera2 >/dev/null 2>&1 || true


# ------------------------------------------------------------
# 6️⃣  Vérifications caméra et Tkinter
# ------------------------------------------------------------
echo "📸 Vérification de la caméra..."
if rpicam-hello -t 1000 &>/dev/null; then
    echo "✅ Caméra détectée et fonctionnelle."
else
    echo "⚠️ Caméra non détectée — vérifier le câble CSI."
fi

echo "🔁 Test NumPy / Picamera2..."
python3 - <<'PY'
try:
    import numpy, picamera2
    print("✅ NumPy & Picamera2 OK :", numpy.__version__)
except Exception as e:
    print("⚠️ Erreur compatibilité :", e)
PY


echo "🪟 Vérification Tkinter..."
python3 - <<'PY'
try:
    import tkinter
    tkinter.Tk().destroy()
    print("✅ Tkinter OK")
except Exception as e:
    print("⚠️ Tkinter non fonctionnel :", e)
PY

echo "🖥️ Vérification écran TFT ST7735..."
python3 - <<'PY'
try:
    from luma.core.interface.serial import spi
    from luma.lcd.device import st7735
    print("🟢 luma.lcd et ST7735 : OK (import réussi)")
except Exception as e:
    print("🔴 ERREUR : impossible d'importer luma.lcd/st7735 :", e)
PY

# ------------------------------------------------------------
# 7️⃣  Conversion CRLF → LF
# ------------------------------------------------------------
find "$BASE_DIR" -type f \( -name "*.py" -o -name "*.sh" \) -exec dos2unix {} \; >/dev/null 2>&1
echo "✅ Conversion des fichiers terminée."

# ------------------------------------------------------------
# 8️⃣  Vérification des dépendances Python (check_dependencies)
# ------------------------------------------------------------
if [ -f "$BASE_DIR/check_dependencies.py" ]; then
    echo "🔍 Exécution du script check_dependencies.py..."
    python3 "$BASE_DIR/check_dependencies.py" || true
else
    echo "⚠️ check_dependencies.py manquant, vérification sautée."
fi

# ------------------------------------------------------------
# 🔟  Informations finales
# ------------------------------------------------------------
echo
echo "🎯 Installation terminée avec succès !"
echo "💡 Pour lancer ton projet :"
echo "   ./main_text_gui.sh"
echo "   ./main_gui_robot.sh"
echo
echo "✅ Environnement Python : $VENV_DIR"
echo "==============================================================="
