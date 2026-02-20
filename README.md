<<<<<<< HEAD
# 🤖 Rubik’s Robot Solver
**Vision + Calibration + Solveur + Robot (servos) + UI (texte) = cube qui finit par céder**

> Objectif : prendre 6 photos, comprendre les couleurs, encoder le cube, calculer une solution… puis **faire exécuter la solution par un robot**.  
> Bonus : logs, callbacks de progression, écran TFT (ou simulé), anneau lumineux, bouton STOP, keypad, et un fichier de config JSON pour tout piloter.

---

## 🧠 Le pipeline (le vrai, le beau, l’essentiel)

Le projet est construit autour d’un pipeline stable et instrumenté par des **événements de progression** (console / JSONL / TFT) :

```
(1) CAPTURE   -> 6 images F,R,B,L,U,D (caméra + LED + lock AE/AWB)
(2) ROI       -> extraction face (bbox/quad calibré, option YOLO)
(3) VISION    -> découpe 3×3 + classification couleurs (robuste reflets)
(4) ENCODAGE  -> conversion vers cubestring 54 chars (URFDLB)
(5) SOLVE     -> Kociemba / Two-Phase => solution Singmaster
(6) ROBOT     -> conversion en mouvements Cubotino-like (F/S/R) + exécution servos
```

### 📡 Progress / UI temps réel
Chaque étape émet des événements (`capture_started`, `detect_face`, `solving_completed`, `execute_move`, …) via :
- `progress.emit()` : standardise `{ts, event, ...}` et **ne casse pas** si un listener plante.
- `progress_listeners.py` :
  - **console_clean_listener** : affiche seulement les événements majeurs
  - **jsonl_file_listener** : écrit un fichier `.jsonl` par run (super utile pour debug live)
- `tft_listener.py` + `tft_driver.py` :
  - écran TFT **simulé** dans `tmp/tft_screen.txt` (lisible avec `tail -f`)

---

## 🧩 Modes d’utilisation

### 1) 🧑‍✈️ Mode Texte (menu console) — le couteau suisse
C’est l’entrée principale pour calibration, capture, debug, solve, robot, utilitaires :

```bash
python3 text_gui.py
```

Sur Raspberry Pi (script) :
```bash
./1_text_gui.sh
```

### 2) 🤖 Mode Robot Automatique (pipeline complet)
Mode “je lance et le robot fait le reste” :

```bash
python3 main_robot_solveur.py
```

Sur Pi (script) :
```bash
./3_main_robot_solveur.sh
```

---

## ⚙️ Configuration : `config.json` (le panneau de contrôle)

Le projet utilise un fichier de configuration JSON centralisé, géré par :
- `config_manager.py` : charge/sauvegarde `config.json`, accès par chemins (`"leds.enabled"`, `"camera.rotation"`, etc.)
- `config_cli.py` : petit CLI pour lire/modifier la config sans toucher au code

### 📌 Exemples (CLI)
Afficher toute la config :
```bash
python3 config_cli.py show
```

Lire une valeur :
```bash
python3 config_cli.py get leds.enabled
```

Activer/désactiver LEDs :
```bash
python3 config_cli.py leds on
python3 config_cli.py leds off
```

Régler luminosité :
```bash
python3 config_cli.py leds brightness 0.12
```

Réinitialiser :
```bash
python3 config_cli.py reset
```

> Astuce : ce fichier est idéal pour adapter rapidement le robot à un autre cube, une autre lumière, ou une autre caméra.

---

## 📸 Capture d’images (caméra + lock + LED)

`capture_photo_from_311.py` gère :
- Raspberry Pi (Picamera2 / libcamera) avec verrouillage **AE/AWB** (crucial)
- Windows (fallback OpenCV)
- anneau NeoPixel (presets “vision”, 2 LEDs pour limiter les reflets)
- capture interactive (Entrée pour shooter)

Images attendues :
```
tmp/F.jpg tmp/R.jpg tmp/B.jpg tmp/L.jpg tmp/U.jpg tmp/D.jpg
```

---

## 🎯 Calibration (ROI + couleurs)

### 1) Calibration ROI (zones des faces)
`calibration_roi.py` :
- calibration manuelle **bbox** (2 clics) ou **quad** (4 coins TL/TR/BR/BL)
- sauvegarde `rubiks_calibration.json`
- option auto via YOLO (si dispo)

### 2) Calibration couleurs
`calibration_colors.py` :
- calibration interactive par clic sur cellules
- sauvegarde `rubiks_color_calibration.json`
- sampling robuste (rejet des pixels specular) + heuristiques (yellow/orange, faces “shiny”)

### Menu global calibration
`calibration_rubiks.py` : menu + stats + dump JSON des calibrations.

---

## 👁️ Vision : image → 3×3 → couleurs
`process_images_cube.py` :
- extrait la face via ROI (bbox/quad), warp 300×300
- découpe grille 3×3
- classification robuste via `analyze_colors_simple()`
- retourne un `FacesDict` (structures partagées dans `types_shared.py`)

---

## 🔤 Encodage : couleurs → cubestring URFDLB (54 chars)
`processing_rubiks.py` :
- applique les corrections d’orientation “robot/cam” (rotations face par face)
- re-oriente le cube pour Kociemba (yaw)
- construit le mapping couleur→lettre via les centres
- valide la cubestring (54 chars, 9× chaque lettre, centres cohérents)
- propose plein de helpers de debug (arêtes impossibles, paires manquantes, etc.)

---

## 🧮 Solveur
`solver_wrapper.py` :
- `method="kociemba"` (standard)
- `method="k2"` via RubikTwoPhase (import lazy)

---

## 🤖 Robot : exécution des mouvements

### Servo / mécanique
`robot_servo.py` :
- pigpio + pilotage 2 servos (plateau bas + couvercle haut)
- primitives : `flip_open/close/up`, `spin_out/mid`, `rotate_out/mid`
- menus de test + calibration PWM

### Conversion solution → mouvements robot
`robot_moves_cubotino.py` :
- parse une solution Singmaster (`"R U R' U'"`)
- convertit vers le format compact Cubotino
- s’appuie sur **Cubotino_T_moves.py** (crédits au projet CUBOTino ❤️)
- exécute les mouvements (F/S/R) sur le hardware (ou en dry-run)

### Orchestrateur pipeline robot
`robot_solver.py` :
- encapsule le pipeline complet (capture → vision → encode → solve → execute)
- gère `stop_flag` / arrêt d’urgence
- remonte tous les événements vers les listeners

---

## 💡 LED ring / Keypad / TFT
- `anneau_lumineux.py` : presets “vision” + effets + extinction “hard”
- `keypad_controller.py` + `auto.py` : keypad 4×4 (scan + autolearn)
- `tft_driver.py` / `tft_listener.py` : écran TFT (ou simulation fichier)

---

## 🧰 Installation (Raspberry Pi)
Installer :
```bash
./INSTALLER.sh
```

Désinstaller proprement :
```bash
./DESINSTALLER.sh
```

Le setup Pi crée un venv standard :
- `~/rubik-env`
- installe apt + pip + pigpio/picamera2/lgpio
- vérifie via `check_dependencies.py`

---

## 📁 Arborescence (résumé utile)
```
.
├── text_gui.py                     # menu console principal
├── main_robot_solveur.py           # mode robot complet (pipeline + listeners)
├── robot_solver.py                 # orchestrateur pipeline (capture->execute)
├── rubiks_operations.py            # API métier centrale (UI-friendly)
├── capture_photo_from_311.py       # capture + lock AE/AWB + LED ring
├── process_images_cube.py          # vision (ROI->warp->grid->colors)
├── processing_rubiks.py            # encodage URFDLB + validations + debug
├── solver_wrapper.py               # solveurs (kociemba / two-phase)
├── robot_moves_cubotino.py         # solution -> mouvements robot + exécution
├── robot_servo.py                  # primitives servos (pigpio)
├── calibration_roi.py              # calibration ROI bbox/quad (+ YOLO option)
├── calibration_colors.py           # calibration couleurs + heuristiques reflets
├── calibration_rubiks.py           # menu calibration global + stats
├── progress.py / progress_listeners.py   # events pipeline + JSONL/console
├── tft_driver.py / tft_listener.py       # écran TFT (ou simulé)
├── config_manager.py / config_cli.py     # config.json + CLI
├── tmp/ logs/ captures/                   # dossiers runtime
└── rubiks_*.json                          # calibrations persistantes
```

---

## ✅ Checklist “ça marche”
1. `./INSTALLER.sh`
2. `python3 text_gui.py`
3. Calibration ROI → génère `rubiks_calibration.json`
4. (Optionnel mais conseillé) Calibration couleurs → `rubiks_color_calibration.json`
5. Capture images (menu)
6. Conversion / debug
7. Solve + URL (Twizzle / alg)
8. Mode robot (avec logs JSONL + TFT simulé)

---

## ❤️ Crédits
- **CUBOTino** : conversion mouvements robot (merci pour le partage du code et de l’approche).
- Projet pédagogique Rubik’s Cube : vision + robotique + pipeline instrumenté.
---

=======
# 🤖 ROBOT RÉSOLVEUR DE RUBIK’S CUBE  
**Vision + Calibration + Solveur + Robotisation**

---

## 🧩 DESCRIPTION GLOBALE
Ce projet implémente un **système complet et autonome** de résolution de Rubik’s Cube :
1. 📸 Capture les 6 faces du cube via caméra (Picamera2 / webcam)  
2. 🎨 Détecte les couleurs avec OpenCV et calibration HSV  
3. 🧠 Encode le cube au format **Singmaster (URFDLB)**  
4. 🧮 Résout le cube via **Kociemba** ou **RubikTwoPhase**  
5. 🤖 Exécute les mouvements sur un **robot physique** (servos, GPIO, Keypad, anneau lumineux)

Le projet fonctionne aussi bien en **mode GUI (Tkinter)** qu’en **mode texte (CLI)**, sur **Windows** ou **Raspberry Pi OS**.

---

## 🛠️ STRUCTURE DU PROJET

```
.
├── INSTALLER.bat / INSTALLER.sh         # Lance l’installation complète
├── DESINSTALLER.bat / DESINSTALLER.sh   # Désinstallation propre
│
├── 0_install_pipeline.sh / .ps1 / .bat  # Installation pipeline (Linux/Win)
├── 1_text_gui.sh / .bat                 # Lancement mode texte
├── 2_gui_robot.sh / .bat                # Lancement GUI robot
├── 3_main_robot_solveur.sh / .bat       # Lancement pipeline complet
│
├── text_gui.py                          # Interface texte (menu complet)
├── tkinter_gui_robot.py                 # Interface graphique robot
│
├── robot_solver.py                      # Pipeline global (capture → solve)
├── robot_moves.py                       # Conversion et exécution mouvements
├── processing_rubiks.py                 # Encodage Singmaster
├── process_images_cube.py               # Vision + détection couleurs
├── calibration_colors.py / roi.py / rubiks.py
│                                        # Modules de calibration
├── solver_wrapper.py                    # Solveurs Kociemba / TwoPhase
├── url_convertor.py                     # Génération d’URL (alg.cubing.net)
├── rubiks_operations.py                 # API métier centrale
│
├── tmp/                                 # Images temporaires (faces)
├── captures/                            # Photos capturées
├── rubiks_calibration.json              # Calibration ROI
├── rubiks_color_calibration.json        # Calibration HSV couleurs
├── history.json                         # Historique des opérations
│
├── requirements_pi.txt                  # Dépendances Raspberry Pi
├── requirements_windows.txt             # Dépendances Windows
└── README.md                            # Ce document 🙂
```

---

## 💻 INSTALLATION

### 🔹 Windows
```powershell
.\INSTALLER.bat
```

ou manuellement :
```powershell
python -m venv env
.\env\Scripts\activate
pip install -r requirements_windows.txt
```

### 🔹 Raspberry Pi / Linux
```bash
bash INSTALLER.sh
```

ou :
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements_pi.txt
```

---

## 🧰 DÉPENDANCES PRINCIPALES

| Catégorie | Librairies |
|------------|-------------|
| Vision | `opencv-python`, `numpy`, `Pillow`, `matplotlib` |
| Solveur | `kociemba`, `RubikTwoPhase` |
| GUI | `tkinter`, `colorama` |
| GPIO / Robot | `lgpio`, `adafruit-circuitpython-neopixel`, `rpi_ws281x` |
| IA (optionnel) | `ultralytics` (YOLOv8 pour calibration auto ROI) |

---

## 🚀 LANCEMENT

### 🧭 Mode Texte (terminal)
```bash
python text_gui.py
```

### 🖥️ Mode Graphique (Tkinter)
```bash
python tkinter_gui_robot.py
```

### 🧠 Mode Robot Automatique
```bash
python main_robot_solveur.py
```

---

## 🔧 CALIBRATION

### Étape 1 – ROI
```bash
python calibration_roi.py
```

### Étape 2 – Couleurs
```bash
python calibration_colors.py
```

### Vérification
```bash
python text_gui.py → option c1
```

---

## 📸 CAPTURE D’IMAGES
```bash
python capture_photo_from_311.py
```

---

## ⚙️ PIPELINE DE TRAITEMENT

```
[Images 6 faces]
   ↓
[Détection ROI + Couleurs]
   ↓
[Encodage URFDLB (54 chars)]
   ↓
[Solveur Kociemba / TwoPhase]
   ↓
[Exécution physique des mouvements]
```

---

## 🤖 PILOTAGE ROBOT

```
U R2 F' L B D
↓
x2 D x2 z D2 z' ...
```

---

## ⚡ ARRÊT D’URGENCE

- GUI : bouton rouge “STOP (A)”  
- Keypad : touche **A**  
- Code :
```python
solver.emergency_stop()
```

---

## 🧾 FICHIERS DE RÉFÉRENCE

| Fichier | Rôle |
|----------|------|
| `rubiks_calibration.json` | Coordonnées ROI par face |
| `rubiks_color_calibration.json` | Moyennes HSV des couleurs calibrées |
| `rubiks_singmaster.txt` | Dernier encodage URFDLB |
| `history.json` | Journal des opérations |

---

## 🧪 TESTS ET DEBUG

```bash
pytest -v
```

Depuis le menu texte :
- `v1` → Diagnostic couleurs  
- `v2` → Debug vision et rotations  
- `p1` → Test pipeline rapide  
- `p2` → Mode robot complet  

---

## 🧹 ENTRETIEN ET NETTOYAGE
```bash
python -c "from rubiks_operations import RubiksOperations; RubiksOperations().cleanup_tmp_files(confirm=False)"
```

---

## 💡 ASTUCES

- `url_convertor.py` → lien alg.cubing.net ou Twizzle :
```bash
python -c "from url_convertor import convert_to_url; print(convert_to_url('R U R\' U\'', site='alg'))"
```

---

## ❤️ AUTEURS & LICENCE

Projet pédagogique open-source  
**© 2025 – Projet Rubik’s Cube (vision + robotique)**  
Licence MIT  
Contributeurs : Galdric T. & collaborateurs
>>>>>>> screen-gui
