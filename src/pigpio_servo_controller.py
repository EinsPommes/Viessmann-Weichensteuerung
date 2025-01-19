import pigpio
import json
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor
import glob
import board
import busio
from adafruit_servokit import ServoKit

# Raspberry Pi spezifische I2C Pins
SCL = board.SCL  # GPIO 3 (Pin 5)
SDA = board.SDA  # GPIO 2 (Pin 3)

class ServoSafetyMonitor:
    def __init__(self, config=None):
        self.movement_counts = {}  # Zählt Bewegungen pro Servo
        self.last_movement = {}    # Zeitpunkt der letzten Bewegung
        self.error_counts = {}     # Zählt Fehler pro Servo
        self.locked_servos = set() # Gesperrte Servos
        
        # Standard-Grenzwerte
        self.config = {
            'MAX_MOVEMENTS_PER_MINUTE': 30,
            'MIN_MOVEMENT_INTERVAL': 0.5,
            'MAX_ERRORS': 3,
            'LOCK_DURATION': 300,
            'BACKUP_ENABLED': True,
            'MAX_BACKUPS': 10,
            'BACKUP_INTERVAL': 3600,
            'ERROR_THRESHOLD': 5,
            'GLOBAL_LOCK_DURATION': 600
        }
        
        # Konfiguration laden wenn vorhanden
        if config and 'SERVO_CONFIG' in config and 'SAFETY' in config['SERVO_CONFIG']:
            self.config.update(config['SERVO_CONFIG']['SAFETY'])
            
    def can_move(self, servo_id):
        """Prüft, ob ein Servo bewegt werden darf"""
        now = time.time()
        
        # Prüfe ob Servo gesperrt ist
        if servo_id in self.locked_servos:
            lock_time = self.last_movement.get(servo_id, 0)
            if now - lock_time >= self.config['LOCK_DURATION']:
                self.locked_servos.remove(servo_id)
                self.error_counts[servo_id] = 0
            else:
                return False
                
        # Initialisiere Zähler wenn nötig
        if servo_id not in self.movement_counts:
            self.movement_counts[servo_id] = []
            
        # Entferne alte Bewegungen (älter als 1 Minute)
        self.movement_counts[servo_id] = [t for t in self.movement_counts[servo_id] 
                                        if now - t <= 60]
        
        # Prüfe Bewegungsfrequenz
        if len(self.movement_counts[servo_id]) >= self.config['MAX_MOVEMENTS_PER_MINUTE']:
            return False
            
        # Prüfe Mindestintervall
        last_move = self.last_movement.get(servo_id, 0)
        if now - last_move < self.config['MIN_MOVEMENT_INTERVAL']:
            return False
            
        return True
        
    def record_movement(self, servo_id):
        """Zeichnet eine Bewegung auf"""
        now = time.time()
        if servo_id not in self.movement_counts:
            self.movement_counts[servo_id] = []
        self.movement_counts[servo_id].append(now)
        self.last_movement[servo_id] = now
        
    def record_error(self, servo_id):
        """Zeichnet einen Fehler auf"""
        if servo_id not in self.error_counts:
            self.error_counts[servo_id] = 0
        self.error_counts[servo_id] += 1
        
        # Sperre Servo bei zu vielen Fehlern
        if self.error_counts[servo_id] >= self.config['MAX_ERRORS']:
            self.locked_servos.add(servo_id)
            self.last_movement[servo_id] = time.time()
            
            # Prüfe ob globale Sperre nötig
            total_errors = sum(self.error_counts.values())
            if total_errors >= self.config['ERROR_THRESHOLD']:
                # Sperre alle Servos
                for sid in range(8):
                    self.locked_servos.add(sid)
                    self.last_movement[sid] = time.time() + self.config['GLOBAL_LOCK_DURATION']

class PiGPIOServoController:
    def __init__(self, pi, servo_pins, config_file='config.json', use_servokit=False):
        """Initialisiert den Servo-Controller"""
        self.pi = pi
        self.servo_pins = servo_pins
        self.config_file = config_file
        self.use_servokit = use_servokit
        self.kit = None
        
        # Logger einrichten
        self.logger = logging.getLogger('servo_controller')
        self.logger.setLevel(logging.DEBUG)
        
        # Safety Monitor initialisieren
        self.safety_monitor = ServoSafetyMonitor()
        
        # ServoKit initialisieren wenn gewünscht
        if self.use_servokit:
            try:
                # ServoKit mit 8 Kanälen initialisieren
                self.kit = ServoKit(channels=8)
                self.logger.info("ServoKit erfolgreich initialisiert")
                
            except Exception as e:
                self.logger.error(f"Fehler bei ServoKit-Initialisierung: {e}")
                raise
        
        # Konfiguration laden oder Standardkonfiguration erstellen
        if not os.path.exists(config_file):
            self.create_default_config()
        self.load_config()
        
        # Servo-Status initialisieren
        self.servo_states = {}
        for i in range(8):  # Nur 8 Kanäle
            self.servo_states[i] = {
                'position': None,
                'current_angle': None,
                'last_move': 0,
                'error': False,
                'move_count': 0
            }
            
    def create_default_config(self):
        """Erstellt eine Standard-Konfiguration"""
        config = {}
        for i in range(8):
            config[str(i)] = {
                'left_angle': 0,
                'right_angle': 180,
                'speed': 1.0
            }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
            
    def angle_to_pulse_pigpio(self, angle):
        """Konvertiert einen Winkel (0-180) in einen Pulswert (500-2500) für PIGPIO"""
        return int(500 + (2500 - 500) * angle / 180)
        
    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            if not self.use_servokit or self.kit is None:
                self.logger.error("ServoKit nicht initialisiert")
                return False
                
            if str(servo_id) not in self.config:
                self.logger.error(f"Keine Konfiguration für Servo {servo_id}")
                return False
            
            # Überprüfe ob Servo-ID im gültigen Bereich (0-7)
            if servo_id >= 8:
                self.logger.error(f"Servo-ID {servo_id} außerhalb des gültigen Bereichs (0-7)")
                return False
            
            servo_config = self.config[str(servo_id)]
            angle = servo_config['left_angle'] if direction == 'left' else servo_config['right_angle']
            
            self.logger.debug(f"Bewege Servo {servo_id} nach {direction} (Winkel: {angle})")
            
            try:
                self.kit.servo[servo_id].angle = angle
                time.sleep(0.1)  # Kurze Pause nach Bewegung
                self.logger.info(f"Servo {servo_id} erfolgreich bewegt zu {direction} (Winkel: {angle})")
                
                # Status aktualisieren
                self.servo_states[servo_id]['position'] = direction
                self.servo_states[servo_id]['current_angle'] = angle
                self.servo_states[servo_id]['last_move'] = time.time()
                self.servo_states[servo_id]['error'] = False
                self.servo_states[servo_id]['move_count'] += 1
                
                return True
                
            except Exception as e:
                self.logger.error(f"ServoKit Fehler bei Servo {servo_id}: {e}")
                self.servo_states[servo_id]['error'] = True
                return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {e}")
            self.servo_states[servo_id]['error'] = True
            return False
            
    def cleanup(self):
        """Räumt auf und gibt Ressourcen frei"""
        try:
            if self.use_servokit and self.kit is not None:
                # Alle Servos auf 0
                for i in range(8):
                    self.kit.servo[i].angle = 0
            else:
                # PIGPIO aufräumen
                for pin in self.servo_pins:
                    if pin is not None:
                        self.pi.set_servo_pulsewidth(pin, 0)
        except Exception as e:
            self.logger.error(f"Fehler beim Cleanup: {e}")

    def load_config(self):
        """Lädt die Konfiguration oder erstellt eine neue"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {'servos': {}}  # Erstelle leere Konfiguration
                self.save_config()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            self.config = {'servos': {}}  # Fallback auf leere Konfiguration

    def save_config(self):
        """Speichert die Konfiguration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
            return False

    def get_servo_config(self, servo_id):
        """Gibt die Konfiguration eines Servos zurück"""
        try:
            if not 0 <= servo_id < len(self.servo_pins):
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")
                
            if not self.config or 'servos' not in self.config:
                # Standard-Konfiguration
                return {
                    'left_angle': 45,
                    'right_angle': 135,
                    'speed': 0.1
                }
                
            servo_config = self.config['servos'].get(str(servo_id))
            if not servo_config:
                # Standard-Konfiguration für diesen Servo
                return {
                    'left_angle': 45,
                    'right_angle': 135,
                    'speed': 0.1
                }
                
            # Füge aktuelle Position hinzu
            servo_config['current_angle'] = self.servo_states[servo_id]['current_angle']
            return servo_config
            
        except Exception as e:
            self.logger.error(f"Fehler beim Lesen der Servo-Konfiguration: {e}")
            # Standard-Konfiguration im Fehlerfall
            return {
                'left_angle': 45,
                'right_angle': 135,
                'speed': 0.1
            }

    def set_servo_config(self, servo_id, config):
        """Setzt die Konfiguration für einen Servo"""
        try:
            if not 0 <= servo_id < len(self.servo_pins):
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")
                
            # Validiere Konfiguration
            if 'left_angle' not in config or 'right_angle' not in config:
                raise ValueError("Linker und rechter Winkel müssen angegeben werden")
                
            if not (0 <= config['left_angle'] <= 180):
                raise ValueError("Linker Winkel muss zwischen 0 und 180 sein")
                
            if not (0 <= config['right_angle'] <= 180):
                raise ValueError("Rechter Winkel muss zwischen 0 und 180 sein")
                
            if 'speed' in config and not (0 <= config['speed'] <= 1):
                raise ValueError("Geschwindigkeit muss zwischen 0 und 1 sein")
            
            # Erstelle servos Dict falls nicht vorhanden
            if 'servos' not in self.config:
                self.config['servos'] = {}
            
            # Speichere Konfiguration
            self.config['servos'][str(servo_id)] = config
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der Servo-Konfiguration: {str(e)}")
            raise

    def set_servo_angle(self, servo_id: int, angle: float):
        """
        Setzt den Winkel für einen Servo
        :param servo_id: ID des Servos (0-7)
        :param angle: Winkel in Grad (0-180)
        """
        try:
            # Prüfe ob der Servo existiert
            if not 0 <= servo_id < len(self.servo_pins):
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")

            # Prüfe ob der Winkel gültig ist
            if not 0 <= angle <= 180:
                raise ValueError(f"Ungültiger Winkel: {angle}")

            # Hole GPIO-Pin
            gpio_pin = self.servo_pins[servo_id]
            if gpio_pin is None:
                raise ValueError(f"Kein GPIO-Pin für Servo {servo_id} konfiguriert")

            # Berechne PWM-Wert (500-2500µs)
            # Runde auf ganze Zahlen um Zittern zu vermeiden
            pwm = round(500 + (angle * 2000.0 / 180.0))
            
            # Setze PWM-Signal
            self.logger.debug(f"Setze Servo {servo_id} auf {angle}° (PWM: {pwm}µs)")
            
            # Setze PWM-Signal einmal und beende es nach kurzer Zeit
            self.pi.set_servo_pulsewidth(gpio_pin, pwm)
            time.sleep(0.5)  # Warte bis der Servo die Position erreicht hat
            self.pi.set_servo_pulsewidth(gpio_pin, 0)  # Stoppe PWM
            
            # Speichere aktuelle Position
            self.servo_states[servo_id]['current_angle'] = angle
            self.servo_states[servo_id]['last_move'] = time.time()
            self.servo_states[servo_id]['error'] = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen des Servo-Winkels: {str(e)}")
            self.servo_states[servo_id]['error'] = True
            raise

    def check_movement_allowed(self, servo_id):
        """Prüft ob eine Bewegung erlaubt ist (Überlastschutz)"""
        try:
            state = self.servo_states[servo_id]
            config = self.get_servo_config(servo_id)
            current_time = time.time()
            
            # Prüfe minimales Zeitintervall zwischen Bewegungen
            if current_time - state['last_move'] < config.get('min_move_interval', 0.5):
                raise ValueError(f"Servo {servo_id} bewegt sich zu schnell!")
            
            # Prüfe maximale Bewegungen pro Minute
            if current_time - state['last_move'] < 60:  # Innerhalb einer Minute
                if state['move_count'] >= config.get('max_moves_per_minute', 30):
                    raise ValueError(f"Servo {servo_id} hat das Bewegungslimit erreicht!")
            else:
                # Reset Zähler nach einer Minute
                state['move_count'] = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"Bewegungsprüfung fehlgeschlagen: {e}")
            return False

    def move_servo(self, servo_id, direction):
        """
        Bewegt einen Servo in die angegebene Richtung
        :param servo_id: ID des Servos (0-7)
        :param direction: Richtung ('left' oder 'right')
        """
        try:
            # Prüfe Parameter
            if not 0 <= servo_id < len(self.servo_pins):
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")
            if direction not in ['left', 'right']:
                raise ValueError(f"Ungültige Richtung: {direction}")
                
            # Hole GPIO-Pin
            gpio_pin = self.servo_pins[servo_id]
            if gpio_pin is None:
                raise ValueError(f"Kein GPIO-Pin für Servo {servo_id} konfiguriert")
                
            # Hole Konfiguration
            config = self.get_servo_config(servo_id)
            self.logger.info(f"Bewege Servo {servo_id} nach {direction}")
            self.logger.debug(f"Konfiguration: {config}")
            
            # Standard-Winkel falls keine Konfiguration
            if not config:
                config = {
                    'left_angle': 45,
                    'right_angle': 135,
                    'speed': 0.1
                }
            
            # Setze Winkel je nach Richtung
            angle = config['left_angle'] if direction == 'left' else config['right_angle']
            
            # Bewege Servo
            success = self.set_servo_angle(servo_id, angle)
            
            if success:
                # Aktualisiere Status
                self.servo_states[servo_id]['position'] = direction
                self.servo_states[servo_id]['current_angle'] = angle
                self.servo_states[servo_id]['last_move'] = time.time()
                self.servo_states[servo_id]['error'] = False
                self.servo_states[servo_id]['move_count'] += 1
                return True
            else:
                self.servo_states[servo_id]['error'] = True
                return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {str(e)}")
            # Schalte PWM aus im Fehlerfall
            try:
                if gpio_pin is not None:
                    self.pi.set_servo_pulsewidth(gpio_pin, 0)
                    self.logger.info(f"PWM ausgeschaltet für Pin {gpio_pin} (nach Fehler)")
            except:
                pass
            self.servo_states[servo_id]['error'] = True
            return False

    def set_servo_speed(self, servo_id, speed):
        """Setzt die Geschwindigkeit eines Servos (0.1-1.0)"""
        try:
            if servo_id < 0 or servo_id >= len(self.servo_pins):
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")
                
            if speed < 0.1 or speed > 1.0:
                raise ValueError(f"Ungültige Geschwindigkeit: {speed}")
                
            # Speichere Geschwindigkeit in Konfiguration
            config = self.get_servo_config(servo_id)
            config['speed'] = speed
            self.set_servo_config(servo_id, **config)
            
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der Servo-Geschwindigkeit: {e}")
            return False

    def cleanup(self):
        """Setzt alle Servos auf 0 und beendet die PWM-Signale"""
        for pin in self.servo_pins:
            if pin is not None:
                self.pi.set_servo_pulsewidth(pin, 0)  # Stoppe PWM

class PCA9685ServoController:
    def __init__(self, config_file='config.json'):
        """Initialisiert den Servo-Controller"""
        self.config_file = config_file
        self.logger = logging.getLogger('servo_controller')
        
        # Initialisiere I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c)
        self.pca.frequency = 50  # Standard-Frequenz für Servos
        
        # Lade oder erstelle Konfiguration
        self.load_config()
        
        # Servo-Status initialisieren
        self.servo_states = {}
        for i in range(16):
            self.servo_states[i] = {
                'position': None,
                'current_angle': None,
                'last_move': 0,
                'error': False
            }
            
    def load_config(self):
        """Lädt die Servo-Konfiguration aus der Datei"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Standard-Konfiguration
                self.config = {}
                for i in range(16):
                    self.config[str(i)] = {
                        'left_angle': 0,    # 0 Grad
                        'right_angle': 180,  # 180 Grad
                        'speed': 100        # Geschwindigkeit (0-100)
                    }
                self.save_config()
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            raise
            
    def save_config(self):
        """Speichert die Servo-Konfiguration in der Datei"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
            raise
            
    def angle_to_pulse(self, angle):
        """Konvertiert einen Winkel (0-180) in einen Pulswert (0-65535)"""
        # Typische Servo-Werte: 2.5% (0°) bis 12.5% (180°) des Zyklus
        pulse_min = 1638  # 2.5% von 65535
        pulse_max = 8192  # 12.5% von 65535
        return int(pulse_min + (pulse_max - pulse_min) * angle / 180)
            
    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            if str(servo_id) not in self.config:
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")
                
            servo_config = self.config[str(servo_id)]
            angle = servo_config['left_angle'] if direction == 'left' else servo_config['right_angle']
            
            # Konvertiere Winkel in Pulswert
            pulse = self.angle_to_pulse(angle)
            
            # Setze PWM über PCA9685
            self.pca.channels[servo_id].duty_cycle = pulse
            
            # Aktualisiere Status
            self.servo_states[servo_id]['position'] = direction
            self.servo_states[servo_id]['current_angle'] = angle
            self.servo_states[servo_id]['last_move'] = time.time()
            self.servo_states[servo_id]['error'] = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {e}")
            self.servo_states[servo_id]['error'] = True
            return False
            
    def cleanup(self):
        """Räumt auf und gibt Ressourcen frei"""
        try:
            # Deaktiviere alle PWM-Kanäle
            for i in range(16):
                self.pca.channels[i].duty_cycle = 0
        except Exception as e:
            self.logger.error(f"Fehler beim Cleanup: {e}")
