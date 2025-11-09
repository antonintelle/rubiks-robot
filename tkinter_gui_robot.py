#!/usr/bin/env python3
# tkinter_gui_robot.py - Interface robot pour mode PRODUCTION
# ============================================================================
# Interface graphique dédiée au robot Rubik's Cube
# Version compacte pour écran 7" Raspberry Pi
# ============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading
import os
import subprocess
import sys

from robot_solver import RobotCubeSolver
try:
    from calibration_rubiks import load_color_calibration
except ImportError:
    # Si load_color_calibration n'existe pas, créer une fonction stub
    def load_color_calibration():
        return None


# ============================================================================
# Widget affichage des couleurs calibrées
# ============================================================================
class ColorVisualizationWidget(tk.Canvas):
    """Widget pour afficher la grille de couleurs calibrées"""

    def __init__(self, parent, **kwargs):
        # compact pour Pi 7"
        super().__init__(parent, width=260, height=70, bg='white', **kwargs)
        self.colors_data = None
        self.load_colors()

    def load_colors(self):
        """Charge les couleurs calibrées"""
        try:
            colors = load_color_calibration()
            self.colors_data = colors
            self.draw_colors()
        except Exception:
            self.colors_data = None
            self.draw_empty()

    def draw_colors(self):
        """Dessine les 6 couleurs calibrées sur une seule ligne (compacte)"""
        self.delete("all")

        if not self.colors_data:
            self.draw_empty()
            return

        color_names = ['red', 'orange', 'yellow', 'green', 'blue', 'white']
        labels = ['RED', 'ORG', 'YEL', 'GRN', 'BLU', 'WHT']

        square_size = 34
        padding = 6

        for i, (color_name, label) in enumerate(zip(color_names, labels)):
            x = padding + i * (square_size + padding)
            y = padding

            if color_name in self.colors_data:
                bgr = self.colors_data[color_name]
                r, g, b = int(bgr[0]), int(bgr[1]), int(bgr[2])
                color_hex = f'#{r:02x}{g:02x}{b:02x}'
            else:
                color_hex = '#CCCCCC'

            self.create_rectangle(
                x, y, x + square_size, y + square_size,
                fill=color_hex, outline='black', width=2
            )

            self.create_text(
                x + square_size//2, y + square_size//2,
                text=label, font=('Arial', 8, 'bold'),
                fill='black' if color_name in ['yellow', 'white'] else 'white'
            )

        # Ajuste la taille du canvas
        total_width = len(color_names) * (square_size + padding) + padding
        self.config(width=total_width, height=square_size + 2*padding)

    def draw_empty(self):
        """Affiche un message si pas de calibration"""
        self.delete("all")
        self.create_text(
            130, 35,
            text="Aucune calibration\nCliquez sur 'Calibrer Couleurs'",
            font=('Arial', 9),
            justify=tk.CENTER
        )

    def refresh(self):
        """Rafraîchit l'affichage"""
        self.load_colors()


# ============================================================================
# Interface principale
# ============================================================================
class RobotGUI:
    """Interface graphique pour le mode production robot"""

    def __init__(self, root):
        self.root = root
        self.root.title("🤖 RUBIK'S CUBE ROBOT - MODE PRODUCTION")
        # Compact pour écran 7"

        # Dimensions souhaitées
        window_width = 820
        window_height = 820
        self.root.geometry(f"{window_width}x{window_height}")  # d'abord la taille

        # On attend que la fenêtre existe pour calculer correctement
        def center_window():
            self.root.update_idletasks()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = int((screen_width / 2) - (window_width / 2))
            y = int((screen_height / 2) - (window_height / 2))
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Centre la fenêtre juste après l'apparition
        self.root.after(100, center_window)

        # Facultatif : la placer brièvement au premier plan
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(500, lambda: self.root.attributes('-topmost', False))


        # --- Style global gris clair pour les GROS boutons (tk.Button) ---
        self.default_button_style = {
            "bg": "#e0e0e0",
            "activebackground": "#d0d0d0",
            "font": ("Arial", 9, "bold"),
            "relief": tk.GROOVE
        }

        # Solveur robot
        self.solver = RobotCubeSolver(image_folder="tmp", debug="text")

        # Flag d'arrêt d'urgence
        self.stop_event = threading.Event()
        self.solver.stop_flag = self.stop_event
        self.emergency_stop_active = False

        # Variables
        self.status_var = tk.StringVar(value="⚪ En attente")
        self.colors_status_var = tk.StringVar(value="❓ Non vérifié")

        self.cubestring_var = tk.StringVar()
        self.solution_var = tk.StringVar()
        self.robot_solution_var = tk.StringVar(value="")
        self.move_count_var = tk.StringVar(value="0")

        self.current_move_var = tk.StringVar(value="-")
        self.next_move_var = tk.StringVar(value="-")
        self.remaining_moves_var = tk.StringVar(value="")

        self.progress_current = tk.IntVar(value=0)
        self.progress_total = tk.IntVar(value=0)

        # Statuts des étapes
        self.step1_status = tk.StringVar(value="⚪")
        self.step2_status = tk.StringVar(value="⚪")
        self.step3_status = tk.StringVar(value="⚪")
        self.step4_status = tk.StringVar(value="⚪")

        # Gestion fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Construction UI
        self.setup_ui()
        self.init_keypad()
        self.check_calibration_status()

    # --------------------------------------------------------------------
    # Gestion du clavier matriciel (Keypad 4x4)
    # --------------------------------------------------------------------
    def init_keypad(self):
        """Initialise le clavier externe 4x4 si présent."""
        self.keypad = None

        if not KeypadController:
            self.log("ℹ️ Aucun module KeypadController détecté (mode Windows).")
            return

        def on_keypad_key(key: str):
            """Callback exécutée à chaque touche appuyée sur le clavier."""
            key = key.upper()
            actions = {
                "0": self.run_full_sequence,
                "1": self.capture_state,
                "2": self.execute_movements,
                "C": self.calibrate_colors,
                "A": self.emergency_stop,
            }

            if key in actions:
                self.log(f"🎹 Touche {key} → exécution de {actions[key].__name__}()")
                try:
                    actions[key]()
                except Exception as e:
                    self.log(f"⚠️ Erreur pendant l’exécution de {actions[key].__name__}: {e}")
            else:
                self.log(f"🔹 Touche {key} pressée (aucune action associée)")

        try:
            self.keypad = KeypadController(callback=on_keypad_key)
            self.log("🎹 Clavier externe connecté (Keypad 4x4).")
        except Exception as e:
            self.log(f"⚠️ Impossible d’initialiser le clavier externe : {e}")
            self.keypad = None

    # ========================================================================
    # FERMETURE
    # ========================================================================
    def on_closing(self):
        """Fermeture propre sans arrêt d'urgence intempestif"""
        if not self.stop_event.is_set():
            # Nettoyage du clavier externe s'il est actif
            if hasattr(self, "keypad") and self.keypad:
                self.keypad.cleanup()
                self.log("🎹 Clavier externe arrêté proprement.")            
            self.log("👋 Fermeture de l'application.")            
            self.root.destroy()
        else:
            if messagebox.askyesno("Confirmation", "Une séquence est en cours. Voulez-vous vraiment forcer l'arrêt ?"):
                self.solver.emergency_stop()
                # Nettoyage du clavier externe s'il est actif
                if hasattr(self, "keypad") and self.keypad:
                    self.keypad.cleanup()
                    self.log("🎹 Clavier externe arrêté proprement.")                
                self.log("🔴 Arrêt d'urgence suite à fermeture.")
                self.root.destroy()

    # ========================================================================
    # CONSTRUCTION DE L'INTERFACE
    # ========================================================================
    def setup_ui(self):
        """Construit l'interface complète"""
        # Barre supérieure
        self.create_header()

        # Section calibration
        self.create_calibration_section()

        # Séparateur compact
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)

        # Section séquence de résolution
        self.create_sequence_section()

        # Séparateur compact
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)

        # Console
        self.create_console()

    def create_header(self):
        """Barre de statut avec STOP + SÉQUENCE COMPLÈTE côte à côte"""
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=4)

        # Zone de gauche : statut texte
        ttk.Label(header, text="Statut :", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Label(header, textvariable=self.status_var, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)

        # Zone de droite : boutons d’action (STOP + Séquence complète)
        right_frame = ttk.Frame(header)
        right_frame.pack(side=tk.RIGHT)

        # 🔴 STOP compact (A)
        tk.Button(
            right_frame,
            text="STOP (A)",
            font=('Arial', 9, 'bold'),
            bg='#cc0000',
            fg='white',
            activebackground='#aa0000',
            activeforeground='white',
            command=self.emergency_stop,
            padx=8,
            pady=3,
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=(4, 0))

        # 🚀 Séquence complète (0)
        tk.Button(
            right_frame,
            text="PIPELINE COMPLET [0]",
            font=('Arial', 9, 'bold'),
            command=self.run_full_sequence,
            bg="#e0e0e0",
            activebackground="#d0d0d0",
            relief=tk.GROOVE,
            padx=10,
            pady=3,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=(0, 6))


    def create_calibration_section(self):
        """Section calibration des couleurs"""
        cal_frame = ttk.LabelFrame(self.root, text="📐 CALIBRATION DES COULEURS", padding=8)
        cal_frame.pack(fill=tk.X, padx=8, pady=4)

        # Statut
        status_frame = ttk.Frame(cal_frame)
        status_frame.pack(fill=tk.X, pady=3)

        ttk.Label(status_frame, text="Statut:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.colors_status_var,
                 font=('Arial', 9)).pack(side=tk.LEFT, padx=4)

        # Ligne regroupant le bouton et les couleurs
        row_frame = ttk.Frame(cal_frame)
        row_frame.pack(fill=tk.X, pady=2)

        # Bouton "Calibrer" à gauche (gris) — avec préfixe C
        tk.Button(
            row_frame,
            text="CALIBRER\nLES COULEURS\n[C]",
            command=self.calibrate_colors,
            width=14,
            height=3,
            **self.default_button_style
        ).pack(side=tk.LEFT, padx=(0, 6), fill=tk.Y)

        # Cadre "Couleurs calibrées actuelles" à droite
        viz_frame = ttk.LabelFrame(row_frame, text="Couleurs calibrées actuelles", padding=4)
        viz_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.color_viz = ColorVisualizationWidget(viz_frame)
        self.color_viz.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

    def create_sequence_section(self):
        """Section séquence de résolution"""
        seq_frame = ttk.LabelFrame(self.root, text="🤖 SÉQUENCE DE RÉSOLUTION", padding=8)
        seq_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Étape 1 : Capture
        self.create_step_1(seq_frame)

        # Étape 2 : Encodage + Résolution
        self.create_step_2(seq_frame)

        # Étape 3 : Exécution
        self.create_step_3(seq_frame)

        # Étape 4 : Retour état initial
        self.create_step_4(seq_frame)

        # Etape qui permet de tout lier
        #self.create_step_full(seq_frame)

    def create_step_1(self, parent):
        """Étape 1 : Capture état initial"""
        step_frame = ttk.Frame(parent)
        step_frame.pack(fill=tk.X, pady=3)

        ttk.Label(step_frame, textvariable=self.step1_status,
                 font=('Arial', 11)).pack(side=tk.LEFT, padx=4)

        # GROS bouton gris
        tk.Button(
            step_frame,
            text="CAPTURER ÉTAT INITIAL [1]",
            command=self.capture_state,
            **self.default_button_style
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def create_step_2(self, parent):
        """Étape 2 : Encodage + Résolution"""
        step_frame = ttk.Frame(parent)
        step_frame.pack(fill=tk.X, pady=3)

        ttk.Label(step_frame, textvariable=self.step2_status,
                 font=('Arial', 11)).pack(side=tk.LEFT, padx=4)

        # GROS bouton gris
        tk.Button(
            step_frame,
            text="ENCODER ET RÉSOUDRE [2]",
            command=self.encode_and_solve,
            **self.default_button_style
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Résultats
        result_frame = ttk.Frame(parent)
        result_frame.pack(fill=tk.X, pady=4, padx=20)

        # Code Singmaster
        code_frame = ttk.Frame(result_frame)
        code_frame.pack(fill=tk.X, pady=2)
        ttk.Label(code_frame, text="Code Singmaster:", width=18).pack(side=tk.LEFT)
        ttk.Entry(code_frame, textvariable=self.cubestring_var,
                 font=('Courier', 9), state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(code_frame, text="📋", width=3,
                 command=lambda: self.copy_to_clipboard(self.cubestring_var.get())).pack(side=tk.LEFT)

        # Solutions groupées
        sol_group = ttk.LabelFrame(result_frame, text="Solutions", padding=6)
        sol_group.pack(fill=tk.X, pady=4)

        # Solution humaine
        sol_hum_frame = ttk.Frame(sol_group)
        sol_hum_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sol_hum_frame, text="Humaine:", width=12).pack(side=tk.LEFT)
        ttk.Entry(sol_hum_frame, textvariable=self.solution_var,
                 font=('Courier', 9), state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(sol_hum_frame, text="📋", width=3,
                 command=lambda: self.copy_to_clipboard(self.solution_var.get())).pack(side=tk.LEFT)

        # Solution robot
        sol_robot_frame = ttk.Frame(sol_group)
        sol_robot_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sol_robot_frame, text="Robot:", width=12).pack(side=tk.LEFT)
        ttk.Entry(sol_robot_frame, textvariable=self.robot_solution_var,
                 font=('Courier', 9), state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(sol_robot_frame, text="📋", width=3,
                 command=lambda: self.copy_to_clipboard(self.robot_solution_var.get())).pack(side=tk.LEFT)

        # Nombre de mouvements
        count_frame = ttk.Frame(result_frame)
        count_frame.pack(fill=tk.X, pady=2)
        ttk.Label(count_frame, text="Nombre de mouvements:", width=18).pack(side=tk.LEFT)
        ttk.Label(count_frame, textvariable=self.move_count_var,
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)

    def create_step_3(self, parent):
        """Étape 3 : Exécution mouvements"""
        step_frame = ttk.Frame(parent)
        step_frame.pack(fill=tk.X, pady=3)

        ttk.Label(step_frame, textvariable=self.step3_status,
                 font=('Arial', 11)).pack(side=tk.LEFT, padx=4)

        # GROS bouton gris
        tk.Button(
            step_frame,
            text="EXÉCUTER LES MOUVEMENTS [3]",
            command=self.execute_movements,
            **self.default_button_style
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Zone de progression
        prog_frame = ttk.LabelFrame(parent, text="Progression des mouvements", padding=8)
        prog_frame.pack(fill=tk.X, pady=4, padx=20)

        # Mouvement en cours et suivant
        move_frame = ttk.Frame(prog_frame)
        move_frame.pack(fill=tk.X, pady=2)

        ttk.Label(move_frame, text="Mouvement en cours:").pack(side=tk.LEFT)
        ttk.Label(move_frame, textvariable=self.current_move_var,
                 font=('Courier', 13, 'bold'), foreground='blue').pack(side=tk.LEFT, padx=8)

        ttk.Label(move_frame, text="Prochain:").pack(side=tk.LEFT, padx=(16, 0))
        ttk.Label(move_frame, textvariable=self.next_move_var,
                 font=('Courier', 11)).pack(side=tk.LEFT, padx=8)

        # Barre de progression
        self.progress_bar = ttk.Progressbar(
            prog_frame,
            mode='determinate',
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=4)

        # Compteur
        self.progress_label = ttk.Label(prog_frame, text="0/0 (0%)", font=('Arial', 10))
        self.progress_label.pack()

        # Mouvements restants
        ttk.Label(prog_frame, text="Mouvements restants:").pack(anchor=tk.W, pady=(6, 0))
        ttk.Label(
            prog_frame,
            textvariable=self.remaining_moves_var,
            font=('Courier', 9),
            foreground='gray'
        ).pack(anchor=tk.W)

    def create_step_4(self, parent):
        """Étape 4 : Retour état initial"""
        step_frame = ttk.Frame(parent)
        step_frame.pack(fill=tk.X, pady=3)

        ttk.Label(step_frame, textvariable=self.step4_status,
                 font=('Arial', 11)).pack(side=tk.LEFT, padx=4)

        # GROS bouton gris
        tk.Button(
            step_frame,
            text="RETOUR ÉTAT INITIAL [4]",
            command=self.return_initial_state,
            state='disabled',  # À implémenter
            **self.default_button_style
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def create_step_full(self, parent):
        """Étape spéciale : lancer toute la séquence 1 → 3"""
        step_frame = ttk.Frame(parent)
        step_frame.pack(fill=tk.X, pady=6)

        ttk.Label(step_frame, text="🔁", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)

        # GROS bouton gris pour tout exécuter
        tk.Button(
            step_frame,
            text="🚀 LANCER SÉQUENCE COMPLÈTE (1 → 3)",
            command=self.run_full_sequence,
            **self.default_button_style
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)


    def create_console(self):
        """Console de logs"""
        console_frame = ttk.LabelFrame(self.root, text="📺 CONSOLE", padding=4)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Scrolled text
        self.console = scrolledtext.ScrolledText(
            console_frame,
            height=6,         # compact
            wrap=tk.WORD,
            font=('Courier', 9)
        )
        self.console.pack(fill=tk.BOTH, expand=True)

        # Message initial
        self.log("⚪ Système prêt")

    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================
    def log(self, message, level="INFO"):
        """Ajoute un message à la console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.root.update_idletasks()

    def copy_to_clipboard(self, text):
        """Copie du texte dans le presse-papiers"""
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.log("📋 Copié dans le presse-papiers")
        else:
            messagebox.showwarning("Attention", "Rien à copier")

    def check_calibration_status(self):
        """Vérifie le statut de la calibration des couleurs"""
        try:
            colors = load_color_calibration()
            if colors and len(colors) == 6:
                self.colors_status_var.set("✅ Calibré (6 couleurs)")
            else:
                self.colors_status_var.set("⚠️ Incomplet")
        except Exception:
            self.colors_status_var.set("❌ Non calibré")

    def update_progress(self, current, total):
        """Met à jour la barre de progression"""
        if total > 0:
            percent = (current / total) * 100
            self.progress_bar['value'] = percent
            self.progress_label.config(text=f"{current}/{total} ({percent:.0f}%)")
        else:
            self.progress_bar['value'] = 0
            self.progress_label.config(text="0/0 (0%)")
        self.root.update_idletasks()

    # ========================================================================
    # CALIBRATION COULEURS
    # ========================================================================
    def calibrate_colors(self):
        """Lance la calibration interactive des couleurs dans une console, avec tolérance par défaut."""
        script_path = os.path.join(os.getcwd(), "calibration_colors.py")

        if not os.path.exists(script_path):
            messagebox.showerror("Erreur", f"Fichier introuvable : {script_path}")
            return

        default_tolerance = 40

        self.log(f"🎨 Lancement de la calibration interactive (tolérance = {default_tolerance})...")
        self.root.withdraw()

        def run_calibration():
            try:
                if os.name == "nt":
                    process = subprocess.Popen(
                        [sys.executable, script_path, "--tolerance", str(default_tolerance)],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    process = subprocess.Popen(
                        [sys.executable, script_path, "--tolerance", str(default_tolerance)]
                    )

                # Attendre la fin
                returncode = process.wait()

                def refresh_after():
                    self.root.deiconify()
                    if returncode == 0:
                        self.log("✅ Calibration terminée - rechargement des couleurs...")
                    else:
                        self.log(f"⚠️ Calibration terminée avec code {returncode}")
                    try:
                        from calibration_colors import load_color_calibration as _load
                        new_colors = _load()
                        if new_colors:
                            self.colors_status_var.set("✅ Calibré (6 couleurs)")
                            self.color_viz.refresh()
                            self.log(f"🎨 Couleurs rechargées : {list(new_colors.keys())}")
                        else:
                            self.colors_status_var.set("⚠️ Calibration incomplète")
                    except Exception as e:
                        self.log(f"❌ Erreur rechargement calibration : {e}")

                self.root.after(200, refresh_after)

            except Exception as e:
                self.log(f"❌ Erreur calibration : {e}")
                self.root.after(200, self.root.deiconify)

        threading.Thread(target=run_calibration, daemon=True).start()

    # ========================================================================
    # ÉTAPE 1 : CAPTURE
    # ========================================================================
    def capture_state(self):
        """Capture l'état initial du cube"""
        self.log("📸 Démarrage capture état initial...")
        self.status_var.set("🟡 Capture en cours...")
        self.step1_status.set("🟡")

        def capture_progress(face, current, total, status):
            if status == "capturing":
                self.log(f"  📸 Capture face {face} ({current}/{total})")
            elif status == "completed":
                self.log(f"  ✅ Face {face} capturée")
            elif status == "loaded":
                self.log(f"  📁 Face {face} chargée")

        def run_capture():
            try:
                self.solver.capture_all_faces(capture_progress)
                self.log("✅ Capture terminée - 6 faces")
                self.status_var.set("✅ Capture OK")
                self.step1_status.set("✅")
            except Exception as e:
                self.log(f"❌ Erreur capture: {e}", "ERROR")
                self.status_var.set("❌ Erreur capture")
                self.step1_status.set("❌")

        thread = threading.Thread(target=run_capture, daemon=True)
        thread.start()

    # ========================================================================
    # ÉTAPE 2 : ENCODAGE + RÉSOLUTION
    # ========================================================================
    def encode_and_solve(self):
        """Encode le cube, calcule la solution et la convertit pour le robot."""
        self.log("🧩 Démarrage encodage et résolution...")
        self.status_var.set("🟡 Encodage en cours...")
        self.step2_status.set("🟡")

        from robot_moves import convert_to_robot_singmaster

        def detect_progress(face, current, total, status):
            if status == "processing":
                self.log(f"  🔍 Analyse face {face} ({current}/{total})")
            elif status == "completed":
                self.log(f"  ✅ Face {face} analysée")

        def solve_progress(status):
            status_messages = {
                "calibration_started": "  🔧 Calibration YOLO...",
                "calibration_completed": "  ✅ Calibration terminée",
                "detection_started": "  🔍 Détection des couleurs...",
                "detection_completed": "  ✅ Détection terminée",
                "conversion_started": "  🔄 Conversion Kociemba...",
                "conversion_completed": "  ✅ Conversion terminée",
                "solving_started": "  🧩 Résolution en cours...",
                "solving_completed": "  ✅ Solution calculée"
            }
            if status in status_messages:
                self.log(status_messages[status])

        def run_encode_solve():
            try:
                # === Lancer la résolution classique ===
                cube_string, solution = self.solver.run(
                    do_solve=True,
                    do_execute=False,
                    auto_calibrate=True,
                    detect_callback=detect_progress,
                    solve_callback=solve_progress
                )

                # === Conversion robot ===
                robot_solution = convert_to_robot_singmaster(solution)

                # === Mise à jour interface ===
                self.cubestring_var.set(cube_string)
                self.solution_var.set(solution)
                self.robot_solution_var.set(robot_solution)

                # Nombre de mouvements
                move_count = len(solution.split())
                self.move_count_var.set(str(move_count))

                self.log(f"✅ Cube encodé: {cube_string}")
                self.log(f"✅ Solution: {solution} ({move_count} mouvements)")
                self.log(f"🤖 Solution pour le robot: {robot_solution}")

                self.status_var.set("✅ Solution prête")
                self.step2_status.set("✅")

            except Exception as e:
                self.log(f"❌ Erreur encodage: {e}", "ERROR")
                self.status_var.set("❌ Erreur encodage")
                self.step2_status.set("❌")

        thread = threading.Thread(target=run_encode_solve, daemon=True)
        thread.start()

    # ========================================================================
    # ÉTAPE 3 : EXÉCUTION
    # ========================================================================
    def execute_movements(self):
        """Exécute les mouvements sur le robot"""
        solution = self.solution_var.get()

        if not solution:
            messagebox.showwarning("Attention", "Pas de solution à exécuter.\nVeuillez d'abord encoder et résoudre le cube.")
            return

        self.log("▶️ Démarrage exécution des mouvements...")
        self.status_var.set("🟡 Exécution en cours...")
        self.step3_status.set("🟡")

        # Réinitialiser le flag d'arrêt
        self.stop_event.clear()

        def execute_progress(current, total, move, next_move, status):
            # Mise à jour interface
            self.current_move_var.set(move or "-")
            self.next_move_var.set(next_move or "-")
            self.update_progress(current, total)

            # Mouvements restants (afficher 10 prochains)
            if total and 0 <= current <= total:
                moves = solution.split()
                remaining = moves[current:current+10]
                self.remaining_moves_var.set(" ".join(remaining) + ("..." if current+10 < total else ""))
            else:
                self.remaining_moves_var.set("")

            # Logs
            if status == "executing":
                self.log(f"  ▶️ Mouvement {current}/{total}: {move}")
            elif status == "completed":
                self.log(f"  ✅ Mouvement {current}/{total}: {move} terminé")
            elif status == "finished":
                self.log(f"✅ Séquence terminée ({total} mouvements)")
                self.status_var.set("✅ Exécution terminée")
                self.step3_status.set("✅")
            elif status == "stopped":
                self.log(f"🔴 ARRÊTÉ à {current}/{total}")
                self.status_var.set("🔴 Arrêt d'urgence")
                self.step3_status.set("🔴")

        def run_execution():
            try:
                self.solver.execute_moves(solution, execute_progress)
            except Exception as e:
                self.log(f"❌ Erreur exécution: {e}", "ERROR")
                self.status_var.set("❌ Erreur exécution")
                self.step3_status.set("❌")

        thread = threading.Thread(target=run_execution, daemon=True)
        thread.start()

    # ========================================================================
    # ÉTAPE 4 : RETOUR ÉTAT INITIAL (À IMPLÉMENTER)
    # ========================================================================
    def return_initial_state(self):
        """Retourne le cube à l'état initial"""
        # TODO: Implémenter la logique de retour
        messagebox.showinfo("Info", "🚧 Fonctionnalité à implémenter")
        self.log("🚧 Retour état initial - À venir")

    # ========================================================================
    # ARRÊT D'URGENCE
    # ========================================================================
    def emergency_stop(self):
        """Active l'arrêt d'urgence."""
        self.emergency_stop_active = True
        self.stop_event.set()
        try:
            self.solver.emergency_stop()
        except Exception:
            pass
        self.log("🔴 ARRÊT D'URGENCE ACTIVÉ", "ERROR")
        self.status_var.set("🔴 Arrêt d'urgence")
        messagebox.showwarning(
            "Arrêt d'urgence",
            "Le robot a été arrêté.\n\nVérifiez l'état du cube avant de continuer."
        )

    # ========================================================================
    # FULL SEQUENCE
    # ========================================================================        
    def run_full_sequence(self):
        """Enchaîne automatiquement capture → résolution → exécution, avec arrêt d'urgence fonctionnel."""
        self.log("🚀 Séquence complète démarrée")
        self.status_var.set("🟡 Séquence complète en cours...")
        self.emergency_stop_active = False
        self.stop_event.clear()

        def wait_for_capture():
            if self.emergency_stop_active or self.stop_event.is_set():
                self.log("🔴 Séquence complète interrompue (capture annulée)")
                self.status_var.set("🔴 Arrêt d'urgence pendant capture")
                return
            if self.step1_status.get() == "✅":
                self.log("➡️ Capture terminée — lancement résolution")
                self.encode_and_solve()
                self.root.after(1000, wait_for_solution)
            else:
                self.root.after(1000, wait_for_capture)

        def wait_for_solution():
            if self.emergency_stop_active or self.stop_event.is_set():
                self.log("🔴 Séquence complète interrompue (résolution annulée)")
                self.status_var.set("🔴 Arrêt d'urgence pendant résolution")
                return
            if self.step2_status.get() == "✅":
                self.log("➡️ Résolution terminée — lancement exécution")
                self.execute_movements()
            else:
                self.root.after(1000, wait_for_solution)

        # Étape 1 : démarrage de la capture
        self.capture_state()
        wait_for_capture()

# ========================================================================
#  INTÉGRATION CLAVIER EXTERNE (KEYPAD)
# ========================================================================
try:
    from keypad_controller import KeypadController
except ImportError:
    KeypadController = None

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================
def main():
    root = tk.Tk()
    app = RobotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
