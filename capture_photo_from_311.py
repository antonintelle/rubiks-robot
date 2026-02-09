#!/usr/bin/env python3
"""
capture_photo_from_311.py
-------------------------
Capture d'image compatible Windows & Raspberry Pi OS Bookworm.
→ Utilise Picamera2 sur Raspberry Pi
→ Utilise OpenCV sur Windows
→ Capture en continu jusqu’à ce que l’utilisateur tape 'q'
→ Pause manuelle entre chaque photo
→ Renvoie un JSON récapitulatif à la fin
"""

import sys, json, platform, datetime, time, os, cv2
from anneau_lumineux import eteindre, eclairage_capture_2_leds_preset
from typing import Optional, Tuple


class CameraInterface2:
    def __init__(self):
        self._picam2 = None
        self._locked = False
        self._locked_controls = None  # debug
        self._scan_leds_on = False

    def lock_for_scan_multiface(
        self,
        flip_cb,                         # callback: fait 1 flip (doit exister côté robot)
        n_samples: int = 4,              # 4 mesures (0,1,2,3) + 4e flip pour revenir au début
        size=(1280, 720),
        ev=0.5,
        warmup_s=1.2,                    # temps initial pour laisser AE/AWB se poser
        settle_after_flip_s=0.35,        # temps après flip (mécanique + AE/AWB)
        per_pose_timeout_s=1.8,          # max d'attente pour "stabilité" sur une pose
        stability_pts=8,                 # nb points récents utilisés pour tester stabilité
        tol=0.05,                        # 5% (comme Cubotino)
        min_exp=8000,
        max_gain=8.0,
        aggregate: str = "median",       # "median" (recommandé) ou "mean"
        debug: bool = False,
        max_exp=30000,
        min_gain=1.0,  # ou 0.8 selon caméra
    ):
        """
        Lock à la Cubotino :
        - AE ON + AWB ON
        - on lit ExposureTime / AnalogueGain / ColourGains sur plusieurs orientations (flip robot)
        - on agrège (médiane ou moyenne)
        - puis AE OFF + AWB OFF + valeurs figées
        - à la fin, on fait un flip supplémentaire pour revenir à l'état initial (si 4 flips = identité).
        """
        import time, platform

        system_name = platform.system().lower()
        if "linux" not in system_name:
            print("⚠️ lock_for_scan_multiface: non-linux, rien à faire.")
            return True

        try:
            from picamera2 import Picamera2
            from libcamera import controls
        except Exception as e:
            print(f"❌ Picamera2/libcamera indisponible: {e}")
            return False

        if flip_cb is None:
            raise ValueError("flip_cb est requis (fonction robot qui fait 1 flip).")

        # Fermer si déjà ouvert
        self.close()

        # Init cam
        self._picam2 = Picamera2()
        config = self._picam2.create_still_configuration(main={"size": size})
        self._picam2.configure(config)
        self._picam2.start()

        # Options utiles (comme legacy)
        try:
            self._picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
        except Exception:
            pass

        try:
            self._picam2.set_controls({"ExposureValue": float(ev)})
        except Exception:
            pass

        try:
            self._picam2.set_controls({"AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted})
        except Exception:
            pass

        try:
            self._picam2.set_controls({"AwbMode": controls.AwbModeEnum.Indoor})
        except Exception:
            pass

        try:
            self._picam2.set_controls({"AeExposureMode": controls.AeExposureModeEnum.Short})
        except Exception:
            pass

        # Optionnel : borne la durée de frame => borne indirectement l'expo max
        try:
            # (min,max) en µs : ici ~30 fps => expo ne pourra pas dépasser ~33ms
            self._picam2.set_controls({"FrameDurationLimits": (33333, 33333)})
            if debug: print("[LOCK-MULTI] FrameDurationLimits set to 33333us")
        except Exception as e:
            if debug: print(f"[LOCK-MULTI] FrameDurationLimits not supported: {e}")
            pass

        # 1) Mode auto (AE/AWB ON)
        self._picam2.set_controls({"AeEnable": True, "AwbEnable": True})
        time.sleep(warmup_s)

        # Warmup frames
        for _ in range(5):
            _ = self._picam2.capture_array()
            time.sleep(0.06)

        def _capture_meta():
            # force 1 frame avant de lire meta
            _ = self._picam2.capture_array()
            return self._picam2.capture_metadata()

        def _wait_stable(timeout_s: float):
            """
            Attends que ExposureTime, AnalogueGain et ColourGains soient "stables"
            (variation < tol sur stability_pts derniers points).
            Renvoie (exp, gain, (cg0, cg1), stable_bool).
            """
            t0 = time.time()
            exp_hist, gain_hist, c0_hist, c1_hist = [], [], [], []

            while time.time() - t0 < timeout_s:
                meta = _capture_meta()

                exp = meta.get("ExposureTime", None)
                gain = meta.get("AnalogueGain", None)
                cg = meta.get("ColourGains", None)

                if exp is None or gain is None or cg is None:
                    time.sleep(0.06)
                    continue

                exp = float(exp)
                gain = float(gain)
                cg0 = float(cg[0])
                cg1 = float(cg[1])

                exp_hist.append(exp)
                gain_hist.append(gain)
                c0_hist.append(cg0)
                c1_hist.append(cg1)

                if len(exp_hist) >= stability_pts:
                    def _ok(hist):
                        last = hist[-1]
                        avg = sum(hist[-stability_pts:]) / stability_pts
                        if avg <= 1e-9:
                            return False
                        ratio = last / avg
                        return (1.0 - tol) <= ratio <= (1.0 + tol)

                    if _ok(exp_hist) and _ok(gain_hist) and _ok(c0_hist) and _ok(c1_hist):
                        return int(exp_hist[-1]), float(gain_hist[-1]), (c0_hist[-1], c1_hist[-1]), True

                time.sleep(0.06)

            # timeout: dernier point si dispo
            if exp_hist:
                return int(exp_hist[-1]), float(gain_hist[-1]), (c0_hist[-1], c1_hist[-1]), False

            return None, None, None, False

        samples = []  # list of dicts: {"exp":..., "gain":..., "cg0":..., "cg1":..., "stable":...}

        # 2) Prendre n_samples mesures sur n_samples orientations,
        # puis flip final (n_samples flips au total) pour revenir à l'état initial.
        for i in range(n_samples):
            # attendre que la pose soit posée + AE/AWB se recale
            time.sleep(settle_after_flip_s)

            exp, gain, (cg0, cg1), stable = _wait_stable(per_pose_timeout_s)
            if exp is None:
                if debug:
                    print(f"[LOCK-MULTI] pose {i}: pas de meta exploitable")
            else:
                # clamps sécurité
                exp = max(int(exp), int(min_exp))
                if max_exp is not None:
                    exp = min(int(exp), int(max_exp))
                gain = min(float(gain), float(max_gain))

                samples.append({"exp": exp, "gain": gain, "cg0": cg0, "cg1": cg1, "stable": stable})
                if debug:
                    print(f"[LOCK-MULTI] pose {i}: exp={exp} gain={gain:.3f} cg=({cg0:.3f},{cg1:.3f}) stable={stable}")

            # flip vers orientation suivante
            flip_cb()

        if not samples:
            print("❌ lock_for_scan_multiface: aucun sample récupéré.")
            return False

        # 3) Agrégation (médiane recommandée)
        def _median(vals):
            vals = sorted(vals)
            n = len(vals)
            return vals[n // 2] if (n % 2 == 1) else 0.5 * (vals[n // 2 - 1] + vals[n // 2])

        exps = [s["exp"] for s in samples]
        gains = [s["gain"] for s in samples]
        c0s = [s["cg0"] for s in samples]
        c1s = [s["cg1"] for s in samples]

        if aggregate.lower() == "mean":
            exp_f = int(sum(exps) / len(exps))
            gain_f = float(sum(gains) / len(gains))
            cg_f = (float(sum(c0s) / len(c0s)), float(sum(c1s) / len(c1s)))
        else:
            exp_f = int(_median(exps))
            gain_f = float(_median(gains))
            cg_f = (float(_median(c0s)), float(_median(c1s)))

        # clamp final exposure
        exp_f = max(int(exp_f), int(min_exp))
        if max_exp is not None:
            exp_f = min(int(exp_f), int(max_exp))

        gain_f = max(float(gain_f), float(min_gain))
        gain_f = min(float(gain_f), float(max_gain))
     
        # 4) Figer en manuel
        ctrl = {
            "AeEnable": False,
            "AwbEnable": False,
            "ExposureTime": exp_f,
            "AnalogueGain": gain_f,
            "ColourGains": cg_f
        }
        self._picam2.set_controls(ctrl)
        time.sleep(0.2)

        self._locked = True
        self._locked_controls = ctrl

        print(f"✅ Camera locked for scan (multiface/{aggregate.lower()}): {ctrl}")
        return True


    def lock_for_scan(self, size=(1280, 720), warmup_s=1.0, settle_s=0.2, awb_profile_path="tmp/awb_profile.txt"):
        """
        Stable lock:
        - AE ON (bref) pour exposer correctement
        - AWB OFF + ColourGains FIXES (profil calibré)
        - puis AE OFF (ExposureTime/Gain figés)
        """
        system_name = platform.system().lower()
        if "linux" not in system_name:
            print("⚠️ lock_for_scan: non-linux, rien à faire.")
            return True

        try:
            from picamera2 import Picamera2
            from libcamera import controls
        except Exception as e:
            print(f"❌ Picamera2/libcamera indisponible: {e}")
            return False

        # Fermer si déjà ouvert
        self.close()

        self._picam2 = Picamera2()
        config = self._picam2.create_still_configuration(main={"size": size})
        self._picam2.configure(config)
        self._picam2.start()

        # AF optionnel
        try:
            self._picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
        except Exception:
            pass

        # --- 1) Charger gains AWB fixes (profil) ---
        gains = self._load_awb_profile(awb_profile_path)  # tu as déjà cette fonction
        if not gains:
            print(f"⚠️ Pas de profil AWB trouvé: {awb_profile_path}. Fais une calibration AWB d'abord.")
            # fallback: on laisse AWB auto (moins stable), mais au moins tu sais pourquoi
            self._picam2.set_controls({"AwbEnable": True})
            time.sleep(warmup_s)
            meta = self._picam2.capture_metadata()
            cg = meta.get("ColourGains", None)
            gains = tuple(cg) if cg else None

        # --- 2) AE ON pour exposer (mais AWB OFF) ---
        self._picam2.set_controls({"AeEnable": True, "AwbEnable": False})
        if gains:
            self._picam2.set_controls({"ColourGains": (float(gains[0]), float(gains[1]))})

        time.sleep(warmup_s)

        # warmup frames (OK de le mettre ici)
        for _ in range(3):
            _ = self._picam2.capture_array()
            time.sleep(0.05)

        # Lire metadata pour figer expo/gain
        meta = self._picam2.capture_metadata()
        exp = meta.get("ExposureTime", None)
        gain = meta.get("AnalogueGain", None)

        ctrl = {"AeEnable": False, "AwbEnable": False}
        if exp is not None:
            ctrl["ExposureTime"] = int(exp)
        if gain is not None:
            ctrl["AnalogueGain"] = float(gain)
        if gains:
            ctrl["ColourGains"] = (float(gains[0]), float(gains[1]))

        self._picam2.set_controls(ctrl)
        time.sleep(settle_s)

        self._locked = True
        self._locked_controls = ctrl
        print(f"✅ Camera locked for scan (stable): {ctrl}")
        return True

    def close(self):
        if self._picam2 is not None:
            try:
                self._picam2.stop()
                self._picam2.close()
            except Exception:
                pass
        self._picam2 = None
        self._locked = False
        self._locked_controls = None


    def capture_image(self,filename="capture.jpg", rotation=0):
        """Capture une seule image et la sauvegarde avec rotation éventuelle."""
        system_name = platform.system().lower()
        print(f"✅ Lancement sur plateforme = {system_name}")
        print(f"✅ Fichier de sortie = {filename}")
        print(f"🔄 Rotation demandée = {rotation}°")

        # Raspberry Pi (Picamera2)
        if "linux" in system_name:
            try:
                if self._picam2 is None:
                    raise RuntimeError(
                        "Camera not locked. Call lock_for_scan() before capture_image()."
                    )

                frame = self._picam2.capture_array()

                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                if rotation == 90:
                    frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)
                elif rotation == 180:
                    frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_180)
                elif rotation == 270:
                    frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)

                cv2.imwrite(filename, frame_bgr)
                time.sleep(0.3)

                print(f"✅ Image enregistrée : {filename}")
                return filename

            except Exception as e:
                print(f"❌ Erreur Picamera2 : {e}")
                return None

        # Windows / autres (OpenCV)
        else:
            try:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    print("❌ Impossible d’ouvrir la caméra (OpenCV)")
                    return None
                ret, frame = cap.read()
                cap.release()
                if not ret:
                    print("❌ Échec de capture d’image")
                    return None

                if rotation == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif rotation == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif rotation == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

                cv2.imwrite(filename, frame)
                print(f"✅ Image enregistrée : {filename}")
                return filename

            except Exception as e:
                print(f"❌ Erreur OpenCV : {e}")
                return None


    # ---------------------------------------------------------------------
    # Capture en boucle jusqu'à 'q'
    # ---------------------------------------------------------------------
    def capture_loop(self,rotation=180, folder="tmp"):
        """
        Capture en boucle : attend Entrée entre chaque image, 'q' pour quitter.

        Args:
            rotation (int): angle de rotation (0, 90, 180, 270)
            folder (str): dossier de sortie
        """
        os.makedirs(folder, exist_ok=True)
        filenames = []
        print("📸 Mode capture continue — appuie sur [Entrée] pour capturer, [q] pour quitter.\n")

        eclairage_capture_2_leds_preset()
        ok = self.lock_for_scan(size=(1280, 720), warmup_s=1.2)
        if not ok:
            raise RuntimeError("Camera lock failed")
        while True:
            key = input("➡️  Appuie sur [Entrée] pour capturer une image ou [q] pour quitter : ").strip().lower()
            if key == "q":
                print("🛑 Fin de la session de capture.")
                break

            timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            filename = os.path.join(folder, f"capture_{timestamp}.jpg")

            path = self.capture_image(filename, rotation)
            if path:
                filenames.append(path)
            else:
                print("⚠️ Capture échouée.")

        print(f"\n✅ {len(filenames)} images capturées.")
        eteindre()
        self.close()
        return filenames

# ---------------------------------------------------------------------
# LEDS
# ---------------------------------------------------------------------
    def leds_on_for_scan(self):
        eclairage_capture_2_leds_preset()
        self._scan_leds_on = True

    def leds_off(self):
        eteindre()
        self._scan_leds_on = False
# ---------------------------------------------------------------------
# Calibration des blancs
# ---------------------------------------------------------------------

    # ---------------------------------------------------------------------
    # AWB utils (Picamera2)
    # ---------------------------------------------------------------------
    def _awb_profile_path(self, folder="tmp", name="awb_profile.txt"):
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, name)

    def _save_awb_profile(self, r_gain: float, b_gain: float, path: str) -> None:
        with open(path, "w") as f:
            f.write(f"{r_gain:.4f},{b_gain:.4f}\n")

    def _load_awb_profile(self, path: str) -> Optional[Tuple[float, float]]:
        if not os.path.exists(path):
            return None
        try:
            raw = open(path, "r").read().strip()
            r, b = raw.split(",")
            return float(r), float(b)
        except Exception:
            return None

    def calibrate_awb_picamera2(
        self,
        warmup_s: float = 1.0,
        settle_s: float = 6.0,
        size=(1280, 720),
        save_to: Optional[str] = None
    ) -> Optional[Tuple[float, float]]:
        """
        Calibre AWB sur Raspberry Pi (Picamera2) dans les conditions robot.
        - LEDs supposées déjà allumées (menu gère ça).
        - Met AWB auto, attend, récupère ColourGains, puis fige AWB.
        Retourne (r_gain, b_gain) ou None.
        """
        system_name = platform.system().lower()
        if "linux" not in system_name:
            print("⚠️ Calibration AWB Picamera2 dispo seulement sur Raspberry Pi (linux).")
            return None

        try:
            from picamera2 import Picamera2
            from libcamera import controls
        except Exception as e:
            print(f"❌ Picamera2/libcamera indisponible: {e}")
            return None

        picam2 = Picamera2()
        try:
            config = picam2.create_still_configuration(main={"size": size})
            picam2.configure(config)
            picam2.start()

            # Autofocus si dispo (optionnel)
            try:
                picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
            except Exception:
                pass

            # AWB auto ON + warmup
            picam2.set_controls({"AwbEnable": True})
            time.sleep(warmup_s)

            # Laisser converger AWB/AE
            t0 = time.time()
            while time.time() - t0 < settle_s:
                time.sleep(0.5)

            # Lire les gains AWB calculés (ColourGains)
            meta = picam2.capture_metadata()
            gains = meta.get("ColourGains", None)
            if not gains or len(gains) < 2:
                print("❌ Impossible de lire ColourGains (AWB pas prêt). Augmente settle_s.")
                return None

            r_gain = float(gains[0])
            b_gain = float(gains[1])

            print(f"✓ Gains AWB obtenus : R={r_gain:.4f}  B={b_gain:.4f}")

            # Figer AWB + appliquer gains
            picam2.set_controls({"AwbEnable": False})
            time.sleep(0.2)
            picam2.set_controls({"ColourGains": (r_gain, b_gain)})
            time.sleep(0.2)

            if save_to:
                self._save_awb_profile(r_gain, b_gain, save_to)
                print(f"✓ Profil AWB sauvegardé : {save_to}")

            return (r_gain, b_gain)

        except Exception as e:
            print(f"❌ Erreur calibration AWB: {e}")
            return None
        finally:
            try:
                picam2.stop()
                picam2.close()
            except Exception:
                pass

    def capture_image_with_awb_profile(
        self,
        filename="capture.jpg",
        rotation=180,
        r_gain: Optional[float] = None,
        b_gain: Optional[float] = None,
        size=(1280, 720),
    ):
        """
        Variante de capture_image qui applique un profil AWB (Picamera2 linux).
        Sur Windows, retombe sur capture_image normal.
        """
        system_name = platform.system().lower()

        # Windows / autres => capture_image classique
        if "linux" not in system_name:
            return self.capture_image(filename, rotation)

        try:
            from picamera2 import Picamera2
            from libcamera import controls
            picam2 = Picamera2()
            config = picam2.create_still_configuration(main={"size": size})
            picam2.configure(config)
            picam2.start()

            try:
                picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
            except Exception:
                pass

            # Si profil fourni => AWB fixe
            if r_gain is not None and b_gain is not None:
                picam2.set_controls({"AwbEnable": False})
                time.sleep(0.1)
                picam2.set_controls({"ColourGains": (float(r_gain), float(b_gain))})
                time.sleep(0.1)
            else:
                # sinon tu gardes ton comportement actuel : AWB figé sans gains = pas idéal
                picam2.set_controls({"AwbEnable": False})
                time.sleep(0.1)

            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            if rotation == 90:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_180)
            elif rotation == 270:
                frame_bgr = cv2.rotate(frame_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)

            cv2.imwrite(filename, frame_bgr)
            picam2.stop()
            picam2.close()
            time.sleep(0.2)
            print(f"✅ Image enregistrée : {filename}")
            return filename

        except Exception as e:
            print(f"❌ Erreur capture_image_with_awb_profile : {e}")
            return None

    # ---------------------------------------------------------------------
    # Sous-menu AWB + LEDs (style capture_loop)
    # ---------------------------------------------------------------------
    def awb_menu(self, rotation=180, folder="tmp"):
        """
        Sous-menu interactif pour gérer LEDs + calibration AWB + photo test.
        """
        os.makedirs(folder, exist_ok=True)
        profile_path = self._awb_profile_path(folder, "awb_profile.txt")
        current = self._load_awb_profile(profile_path)  # (r,b) ou None

        def led_on():
            try:
                eclairage_capture_2_leds_preset()
                print("✓ LEDs ON")
            except Exception as e:
                print(f"✗ Erreur LEDs ON: {e}")

        def led_off():
            try:
                eteindre()
                print("✓ LEDs OFF")
            except Exception as e:
                print(f"✗ Erreur LEDs OFF: {e}")

        print("\n" + "=" * 60)
        print("MENU AWB (Picamera2) + LEDs — MODE ROBOT")
        print("=" * 60)
        print(f"Profil actuel: {current if current else 'Aucun'}")
        print(f"Fichier profil: {profile_path}")

        leds_state = False

        try:
            while True:
                print("\nOptions:")
                print("  1) LEDs ON")
                print("  2) LEDs OFF")
                print("  3) Calibrer AWB (feuille blanche à la place du cube)")
                print("  4) Photo test (avec profil si dispo)")
                print("  5) Charger profil depuis disque")
                print("  6) Afficher profil actuel")
                print("  0) Quitter")

                choice = input("Ton choix : ").strip()

                if choice == "1":
                    led_on()
                    leds_state = True

                elif choice == "2":
                    led_off()
                    leds_state = False

                elif choice == "3":
                    if not leds_state:
                        led_on()
                        leds_state = True

                    input("\n➡️ Place une feuille blanche (ou gris neutre) à la place du cube, puis [Entrée]... ")

                    gains = self.calibrate_awb_picamera2(
                        warmup_s=1.0,
                        settle_s=6.0,
                        size=(1280, 720),
                        save_to=profile_path
                    )
                    if gains:
                        current = gains
                        print(f"✅ Nouveau profil: {current}")
                    else:
                        print("⚠️ Calibration échouée.")

                elif choice == "4":
                    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                    filename = os.path.join(folder, f"awb_test_{timestamp}.jpg")

                    r_gain = current[0] if current else None
                    b_gain = current[1] if current else None

                    if not leds_state:
                        led_on()
                        leds_state = True

                    path = self.capture_image_with_awb_profile(
                        filename=filename,
                        rotation=rotation,
                        r_gain=r_gain,
                        b_gain=b_gain,
                    )
                    if path:
                        print(f"✅ Photo test: {path}")
                    else:
                        print("⚠️ Photo test échouée.")

                elif choice == "5":
                    loaded = self._load_awb_profile(profile_path)
                    if loaded:
                        current = loaded
                        print(f"✅ Profil chargé: {current}")
                    else:
                        print("⚠️ Aucun profil trouvé ou fichier invalide.")

                elif choice == "6":
                    print(f"Profil actuel: {current if current else 'Aucun'}")

                elif choice == "0":
                    print("🛑 Sortie menu AWB.")
                    break

                else:
                    print("⚠️ Choix invalide.")

        finally:
            # Sécurité : éteindre en sortant
            led_off()


# ---------------------------------------------------------------------
# Mode exécution directe → JSON de sortie
# ---------------------------------------------------------------------
if __name__ == "__main__":
    rotation = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    folder = sys.argv[2] if len(sys.argv) > 2 else "tmp"
    camera = CameraInterface2()
    
    files = camera.capture_loop(rotation, folder)

    result = {
        "success": len(files) > 0,
        "count": len(files),
        "files": files,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    print(json.dumps(result))
