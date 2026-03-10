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
Contributeurs : Galdric T., Alexi A., Antonin T., Gabriel D. et Noah S.
