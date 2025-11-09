#!/usr/bin/env python3
# ============================================================
# keypad_controller.py  –  Gestion du clavier matriciel 4x4 (lgpio)
# ============================================================
# Compatible Raspberry Pi OS Bookworm, sans sudo.
# Mapping confirmé avec GPIO 22,19,16,20,26,13,5,6
# ------------------------------------------------------------

import lgpio
import threading
import time


class KeypadController:
    """
    Gère un clavier matriciel 4×4 connecté au Raspberry Pi via lgpio.
    Appelle une fonction callback à chaque touche pressée.
    """

    def __init__(self, callback=None, poll_delay=0.05):
        """
        :param callback: fonction appelée avec la touche détectée
        :param poll_delay: délai (s) entre deux balayages de la matrice
        """
        # === Disposition réelle du clavier ===
        self.KEYPAD = [
            ["1", "4", "7", "*"],
            ["2", "5", "8", "0"],
            ["3", "6", "9", "#"],
            ["A", "B", "C", "D"],
        ]

        # === Brochage matériel validé ===
        # Lignes = Noir, Vert, Orange, Jaune
        self.ROW_PINS = [26, 13, 5, 6]
        # Colonnes = Marron, Blanc, Violet, Bleu
        self.COL_PINS = [22, 19, 16, 20]

        self.callback = callback
        self.poll_delay = poll_delay
        self._stop_flag = False

        # Ouverture du chip GPIO principal
        self.chip = lgpio.gpiochip_open(0)

        # Configuration : lignes en sortie (haut) / colonnes en entrée (pull-up)
        for r in self.ROW_PINS:
            lgpio.gpio_claim_output(self.chip, r, 1)
        for c in self.COL_PINS:
            lgpio.gpio_claim_input(self.chip, c, lgpio.SET_PULL_UP)

        # Thread de scrutation
        self.thread = threading.Thread(target=self._poll_keys, daemon=True)
        self.thread.start()

    # ------------------------------------------------------------
    def _poll_keys(self):
        """Boucle de balayage du clavier."""
        pressed = set()
        while not self._stop_flag:
            for r_idx, r_pin in enumerate(self.ROW_PINS):
                lgpio.gpio_write(self.chip, r_pin, 0)
                for c_idx, c_pin in enumerate(self.COL_PINS):
                    if lgpio.gpio_read(self.chip, c_pin) == 0:
                        key = self.KEYPAD[r_idx][c_idx]
                        if key not in pressed:
                            pressed.add(key)
                            if self.callback:
                                threading.Thread(
                                    target=self.callback, args=(key,), daemon=True
                                ).start()
                    else:
                        key = self.KEYPAD[r_idx][c_idx]
                        if key in pressed:
                            pressed.remove(key)
                lgpio.gpio_write(self.chip, r_pin, 1)
            time.sleep(self.poll_delay)

    # ------------------------------------------------------------
    def cleanup(self):
        """Arrête le thread et libère les GPIO."""
        self._stop_flag = True
        time.sleep(self.poll_delay * 2)
        lgpio.gpiochip_close(self.chip)


# ============================================================
# === Fonctions principales pour intégration ou test =========
# ============================================================

def main_keypad():
    """Permet de tester le clavier 4x4 directement."""
    print("=== TEST CLAVIER 4×4 (lgpio) ===")
    print("Appuie sur les touches (Ctrl+C pour quitter)")

    def show_key(k):
        print(f"[KEYPAD] Touche détectée : {k}")

    kp = KeypadController(callback=show_key)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        kp.cleanup()
        print("\nFin du test du clavier.")


if __name__ == "__main__":
    main_keypad()
