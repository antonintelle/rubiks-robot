#!/usr/bin/env python3
"""
Module de gestion tactile XPT2046
Gère la lecture du tactile en arrière-plan via thread
"""
import RPi.GPIO as GPIO
import time
import threading

class TouchHandler:
    """Gestionnaire tactile XPT2046"""
    
    # Calibration (moyenne de 2 mesures)
    X_MIN, X_MAX = 292, 3935
    Y_MIN, Y_MAX = 159, 3984
    
    # GPIO XPT2046
    IRQ = 17
    CS = 27
    CLK = 18
    MOSI = 23
    MISO = 19
    
    def __init__(self, on_press=None, on_release=None, on_move=None):
        """
        Initialise le gestionnaire tactile
        
        Args:
            on_press: Callback appelé au début du touch (x, y)
            on_release: Callback appelé au relâchement (x, y) - position finale
            on_move: Callback appelé pendant le mouvement (x, y)
        """
        self.on_press = on_press
        self.on_release = on_release
        self.on_move = on_move
        
        self._stop_event = threading.Event()
        self._thread = None
        self._last_touch = (None, None)
        self._lock = threading.Lock()
        self._is_touching = False  # État du touch
        
        # Init GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.IRQ, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.CS, GPIO.OUT)
        GPIO.setup(self.CLK, GPIO.OUT)
        GPIO.setup(self.MOSI, GPIO.OUT)
        GPIO.setup(self.MISO, GPIO.IN)
        GPIO.output(self.CS, GPIO.HIGH)
        GPIO.output(self.CLK, GPIO.LOW)
    
    def _spi_rw(self, data):
        """Communication SPI bit-bang"""
        result = []
        for byte in data:
            recv = 0
            for _ in range(8):
                GPIO.output(self.MOSI, byte & 0x80)
                byte <<= 1
                time.sleep(0.00001)
                GPIO.output(self.CLK, GPIO.HIGH)
                time.sleep(0.00001)
                recv = (recv << 1) | GPIO.input(self.MISO)
                GPIO.output(self.CLK, GPIO.LOW)
                time.sleep(0.00001)
            result.append(recv)
        return result
    
    def read_raw(self):
        """
        Lit position tactile brute
        
        Returns:
            (x_pixel, y_pixel) ou (None, None) si pas de touch
        """
        GPIO.output(self.CS, GPIO.LOW)
        time.sleep(0.0001)
        
        # Lecture X (0x90) et Y (0xD0)
        x_raw = ((self._spi_rw([0x90,0,0])[1] << 8) | self._spi_rw([0x90,0,0])[2]) >> 3
        y_raw = ((self._spi_rw([0xD0,0,0])[1] << 8) | self._spi_rw([0xD0,0,0])[2]) >> 3
        
        GPIO.output(self.CS, GPIO.HIGH)
        
        # Validation
        if not (100 < x_raw < 4000 and 100 < y_raw < 4000):
            return None, None
        
        # Conversion brut → pixel (X et Y inversés)
        x = int((self.X_MAX - x_raw) * 320 / (self.X_MAX - self.X_MIN))
        y = int((self.Y_MAX - y_raw) * 240 / (self.Y_MAX - self.Y_MIN))
        
        # Clamp
        return max(0, min(319, x)), max(0, min(239, y))
    
    def is_touched(self):
        """Retourne True si écran touché"""
        return GPIO.input(self.IRQ) == GPIO.LOW
    
    def get_touch(self):
        """
        Retourne dernière position touch (lecture thread-safe)
        
        Returns:
            (x, y) ou (None, None)
        """
        with self._lock:
            return self._last_touch
    
    def _poll_loop(self):
        """Boucle de polling tactile (thread interne)"""
        last_x, last_y = None, None
        press_notified = False
        
        while not self._stop_event.is_set():
            if self.is_touched():
                x, y = self.read_raw()
                
                if x is not None:
                    # Filtre anti-rebond (mouvement > 2 pixels)
                    if last_x is None or abs(x - last_x) > 2 or abs(y - last_y) > 2:
                        with self._lock:
                            self._last_touch = (x, y)
                            self._is_touching = True
                        
                        # PRESS - première détection
                        if not press_notified:
                            if self.on_press:
                                self.on_press(x, y)
                            press_notified = True
                        
                        # MOVE - déplacement
                        else:
                            if self.on_move:
                                self.on_move(x, y)
                        
                        last_x, last_y = x, y
                
                time.sleep(0.03)  # ~30 FPS
            else:
                # RELEASE - stylet levé
                if last_x is not None:
                    # Appel du callback RELEASE avec dernière position
                    if self.on_release:
                        self.on_release(last_x, last_y)
                    
                    with self._lock:
                        self._last_touch = (None, None)
                        self._is_touching = False
                    
                    last_x, last_y = None, None
                    press_notified = False
                
                time.sleep(0.01)
    
    def start(self):
        """Démarre le thread de polling tactile"""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
    
    def stop(self):
        """Arrête le thread de polling"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def cleanup(self):
        """Nettoyage GPIO"""
        self.stop()
