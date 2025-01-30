import time
import json
import os
import logging
from adafruit_servokit import ServoKit
import board
import busio

class ServoKitController:
    """Klasse zur Steuerung der Servos über den ServoKit"""
    
    # Standard-Konfiguration für neue Servos
    DEFAULT_CONFIG = {
        'left_angle': 30.0,    # Standardwinkel für linke Position
        'right_angle': 150.0,  # Standardwinkel für rechte Position
        'speed': 0.1          # Standard-Geschwindigkeit
    }
    
    def __init__(self):
        """Initialisiert den ServoKit Controller"""
        try:
            # Logger initialisieren
            self.logger = logging.getLogger('servo_controller')
            self.logger.setLevel(logging.DEBUG)
            
            # Config-Datei
            self.config_file = "src/config.json"
            
            # Lade Konfiguration
            self.config = self.load_config()
            
            # Erstelle I2C Bus
            self.i2c = busio.I2C(board.SCL, board.SDA)
            
            # PCA9685 Register-Adressen
            MODE1 = 0x00
            PRESCALE = 0xFE
            LED0_ON_L = 0x06
            
            # Erstelle ServoKit für Board 1
            self.kit1 = ServoKit(channels=16, i2c=self.i2c, address=0x40)
            self.kit1._pca.frequency = 50  # Setze Frequenz auf 50Hz
            
<<<<<<< HEAD
            # PWM Werte für verschiedene Positionen (basierend auf 16-bit Timer)
            self.PWM_LEFT = 2500    # 0.76ms = -90° (links)
            self.PWM_CENTER = 4915  # 1.5ms = 0° (mitte)
            self.PWM_RIGHT = 7300   # 2.23ms = +90° (rechts)
            
            self.logger.info("ServoKit 1 (0x40) erfolgreich initialisiert")
            
            # Initialisiere Konfiguration
            if not os.path.exists(self.config_file):
                self.config = self.create_default_config()
            else:
                self.config = self.load_config()

            # Initialisiere Servo-Status
            self.servo_states = {}
            for i in range(16):  # Ein Board mit 16 Servos
                self.servo_states[str(i)] = {
                    'position': None,
                    'current_angle': None,
                    'last_move': 0,
                    'error': False,
                    'initialized': True,
                    'status': 'initialized'
                }
            
=======
            # Setze alle Kanäle auf 0 bevor wir die Frequenz ändern
            for i in range(16):
                reg_base = LED0_ON_L + (i * 4)
                self.kit1._pca._write_byte(reg_base, 0)
                self.kit1._pca._write_byte(reg_base + 1, 0)
                self.kit1._pca._write_byte(reg_base + 2, 0)
                self.kit1._pca._write_byte(reg_base + 3, 0)
            
            # Setze die PWM-Frequenz auf 50Hz (Standard für Servos)
            self.kit1._pca.frequency = 50
            
            # Setze alle Servos auf Mittelposition (1.5ms Puls)
            pulse_width = int(1.5 * 4096 / 20)  # 1.5ms bei 50Hz
            for i in range(16):
                reg_base = LED0_ON_L + (i * 4)
                self.kit1._pca._write_byte(reg_base + 2, pulse_width & 0xFF)
                self.kit1._pca._write_byte(reg_base + 3, (pulse_width >> 8) & 0x0F)
            
            self.logger.info("ServoKit 1 (0x40) erfolgreich initialisiert")
            
            # Versuche zweites Board zu initialisieren
            try:
                self.kit2 = ServoKit(channels=16, i2c=self.i2c, address=0x41)
                self.dual_board = True
                
                # Das gleiche für Board 2
                for i in range(16):
                    reg_base = LED0_ON_L + (i * 4)
                    self.kit2._pca._write_byte(reg_base, 0)
                    self.kit2._pca._write_byte(reg_base + 1, 0)
                    self.kit2._pca._write_byte(reg_base + 2, 0)
                    self.kit2._pca._write_byte(reg_base + 3, 0)
                
                self.kit2._pca.frequency = 50
                
                for i in range(16):
                    reg_base = LED0_ON_L + (i * 4)
                    self.kit2._pca._write_byte(reg_base + 2, pulse_width & 0xFF)
                    self.kit2._pca._write_byte(reg_base + 3, (pulse_width >> 8) & 0x0F)
                
                self.logger.info("Zweites PCA9685 Board gefunden")
            except Exception as e:
                self.kit2 = None
                self.dual_board = False
                self.logger.warning(f"Zweites Board nicht gefunden, nutze nur Board 1: {str(e)}")
            
            # Servo-Status initialisieren
            self.servo_states = {}
            
            self.logger.info("Servo-Controller erfolgreich initialisiert")
            
>>>>>>> 0040156a9d902821e6b3f4f85bd2630116956bdf
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung: {str(e)}")
            raise
            
    def get_servo_status(self, servo_id):
        """Liefert den Status eines Servos"""
        try:
            # Hole Status aus servo_states
            status = self.servo_states.get(str(servo_id), {})
            if not status:
                return {
                    'initialized': False,
                    'error': True,
                    'status': 'error',
                    'message': 'Servo nicht gefunden'
                }
            return status
        except Exception as e:
            return {
                'initialized': False,
                'error': True,
                'status': 'error',
                'message': str(e)
            }

    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            # Prüfe ob Servo verfügbar ist
            if servo_id >= 16:
                raise Exception("Ungültige Servo-ID")
            if self.kit1 is None:
                raise Exception("Board nicht verfügbar")

            # Hole Konfiguration für den Servo
<<<<<<< HEAD
            config = self.config.get(str(servo_id), self.DEFAULT_CONFIG)
=======
            servo_config = self.config.get(str(servo_num), {})
            left_angle = float(servo_config.get('left_angle', 30.0))  # Standard: 30°
            right_angle = float(servo_config.get('right_angle', 150.0))  # Standard: 150°
            speed = float(servo_config.get('speed', 0.1))
>>>>>>> 0040156a9d902821e6b3f4f85bd2630116956bdf
            
            # Setze Winkel basierend auf Richtung
            if direction == 'left':
                angle = config['left_angle']
            else:
                angle = config['right_angle']
                
<<<<<<< HEAD
            # Bewege Servo
            self.kit1.servo[servo_id].angle = angle
=======
            # Hole aktuellen Winkel
            current_angle = self.servo_states[str(servo_num)].get('current_angle', target_angle)
            
            # Berechne Schritte basierend auf der Geschwindigkeit
            steps = int(abs(target_angle - current_angle) / speed)
            steps = max(10, min(steps, 100))  # Mindestens 10, maximal 100 Schritte
            
            # Setze Winkel schrittweise
            self.set_angle(servo_num, target_angle, steps=steps)
>>>>>>> 0040156a9d902821e6b3f4f85bd2630116956bdf
            
            # Aktualisiere Status
            self.servo_states[str(servo_id)].update({
                'position': direction,
                'current_angle': angle,
                'last_move': time.time(),
                'error': False,
                'status': 'initialized'
            })
            
            return {'status': 'success', 'position': direction}
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {str(e)}")
            if str(servo_id) in self.servo_states:
                self.servo_states[str(servo_id)]['error'] = True
                self.servo_states[str(servo_id)]['status'] = 'error'
            raise
            
    def load_config(self):
        """Lädt die Konfiguration aus der JSON-Datei"""
        try:
            if not os.path.exists(self.config_file):
                return self.create_default_config()
                
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Prüfe ob alle Servos in der Konfiguration sind
            for i in range(16):  # Ein Board
                if str(i) not in config:
                    config[str(i)] = self.DEFAULT_CONFIG.copy()
            
            return config
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            return self.create_default_config()
            
    def create_default_config(self):
        """Erstellt eine Standard-Konfiguration"""
        try:
            # Erstelle leeres Konfigurations-Dictionary
            config = {}
            
            # Füge Standard-Konfiguration für jedes Board hinzu
            for i in range(16):  # Ein Board
                config[str(i)] = {
                    'left_angle': 30,
                    'right_angle': 150,
                    'speed': 0.1
                }
<<<<<<< HEAD
=======
                
            if self.dual_board:
                for i in range(16):  # Zweites Board
                    config[str(i+16)] = {
                        'left_angle': 30,
                        'right_angle': 150,
                        'speed': 0.1
                    }
>>>>>>> 0040156a9d902821e6b3f4f85bd2630116956bdf
            
            # Speichere Konfiguration
            self.config = config
            self.save_config()
            
            self.logger.info("Standard-Konfiguration erstellt")
            return config
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Standard-Konfiguration: {e}")
            raise
            
<<<<<<< HEAD
=======
    def load_config(self):
        """Lädt die Konfiguration aus der Datei"""
        try:
            # Prüfe ob Datei existiert
            if not os.path.exists(self.config_file):
                self.logger.warning(f"Konfigurationsdatei {self.config_file} nicht gefunden")
                return self.create_default_config()
                
            # Lade Konfiguration
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Prüfe ob Konfiguration gültig ist
            if not isinstance(config, dict):
                raise ValueError("Ungültiges Konfigurations-Format")
                
            # Füge fehlende Servos hinzu
            for i in range(16):  # Erstes Board
                if str(i) not in config:
                    self.logger.warning(f"Servo {i} nicht in Konfiguration gefunden, füge Standard-Konfiguration hinzu")
                    config[str(i)] = {
                        'left_angle': 30,
                        'right_angle': 150,
                        'speed': 0.1
                    }
                    
            if self.dual_board:
                for i in range(16):  # Zweites Board
                    if str(i+16) not in config:
                        self.logger.warning(f"Servo {i+16} nicht in Konfiguration gefunden, füge Standard-Konfiguration hinzu")
                        config[str(i+16)] = {
                            'left_angle': 30,
                            'right_angle': 150,
                            'speed': 0.1
                        }
            
            self.logger.info("Konfiguration erfolgreich geladen")
            return config
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            return self.create_default_config()
            
>>>>>>> 0040156a9d902821e6b3f4f85bd2630116956bdf
    def save_config(self):
        """Speichert die Konfiguration in der JSON-Datei"""
        try:
            # Erstelle eine Kopie der Konfiguration nur mit Servo-Daten
            servo_config = {}
            
            # Füge nur gültige Servo-Konfigurationen hinzu
            for servo_id, config in self.config.items():
                # Überspringe nicht-numerische Keys
                if not servo_id.isdigit():
                    continue
                    
                if not isinstance(config, dict):
                    self.logger.warning(f"Überspringe ungültige Konfiguration für Servo {servo_id}")
                    continue
                    
                # Stelle sicher dass alle erforderlichen Felder vorhanden sind
                servo_data = {}
                for field in ['left_angle', 'right_angle', 'speed']:
                    if field in config:
                        try:
                            servo_data[field] = float(config[field])
                        except (ValueError, TypeError):
                            servo_data[field] = float(self.DEFAULT_CONFIG[field])
                    else:
                        servo_data[field] = float(self.DEFAULT_CONFIG[field])
                
                servo_config[servo_id] = servo_data
            
            # Speichere in Datei
            with open(self.config_file, 'w') as f:
                json.dump(servo_config, f, indent=4)
                
            self.logger.info("Konfiguration erfolgreich gespeichert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
            raise
            
    def set_angle(self, servo_num: int, angle: float, steps=10) -> None:
        """Setzt einen Servo auf einen bestimmten Winkel"""
        try:
<<<<<<< HEAD
            # Validiere Winkel
            if not (0 <= angle <= 180):
                raise ValueError(f"Winkel muss zwischen 0° und 180° liegen (war: {angle})")
                
            # Setze Winkel je nach Board
            if servo_num >= 16:
                raise Exception("Ungültige Servo-ID")
            self.kit1.servo[servo_num].angle = angle
                
            self.logger.debug(f"Setze Servo {servo_num} auf {angle}°")
=======
            # Bestimme Board und Channel
            if servo_num < 16:
                kit = self.kit1
                channel = servo_num
            else:
                if not self.dual_board:
                    raise Exception("Zweites Board nicht verfügbar")
                kit = self.kit2
                channel = servo_num - 16
            
            # Hole Servo-Konfiguration
            servo_config = self.config.get('SERVO_CONFIG', {}).get('SERVOS', [])[servo_num]
            left_angle = float(servo_config.get('left_angle', 0))
            right_angle = float(servo_config.get('right_angle', 180))
            
            # Validiere Winkel
            if not (left_angle <= angle <= right_angle):
                raise ValueError(f"Winkel {angle} außerhalb des erlaubten Bereichs ({left_angle}° - {right_angle}°)")
            
            # Hole aktuellen Winkel
            current_angle = self.servo_states[str(servo_num)].get('current_angle')
            if current_angle is None:
                current_angle = angle
            
            # Berechne Schritte
            angle_diff = angle - current_angle
            angle_step = angle_diff / steps if steps > 0 else angle_diff
            
            # Bewege schrittweise
            for step in range(steps):
                current_angle += angle_step
                # Normalisiere den Winkel auf den Servo-Bereich
                normalized_angle = ((current_angle - left_angle) / (right_angle - left_angle)) * 180
                kit.servo[channel].angle = normalized_angle
                time.sleep(0.02)  # 20ms Pause zwischen den Schritten
            
            # Stelle sicher, dass der endgültige Winkel exakt stimmt
            normalized_angle = ((angle - left_angle) / (right_angle - left_angle)) * 180
            kit.servo[channel].angle = normalized_angle
            
            # Aktualisiere Status
            self.servo_states[str(servo_num)]['current_angle'] = angle
>>>>>>> 0040156a9d902821e6b3f4f85bd2630116956bdf
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen des Winkels für Servo {servo_num}: {e}")
            self.servo_states[str(servo_num)]['error'] = True
            raise
            
    def move_to_angle(self, servo, current_angle, target_angle, step_size=1):
        """Bewegt einen Servo langsam zu einem Zielwinkel"""
        if current_angle < target_angle:
            for angle in range(int(current_angle), int(target_angle), step_size):
                servo.angle = angle
                time.sleep(0.05)  # 50ms Pause zwischen den Schritten
        else:
            for angle in range(int(current_angle), int(target_angle), -step_size):
                servo.angle = angle
                time.sleep(0.05)  # 50ms Pause zwischen den Schritten
        servo.angle = target_angle  # Stelle sicher, dass der endgültige Winkel exakt erreicht wird
        
    def calibrate_servo(self, servo_id, left_angle, right_angle):
        """Kalibriert einen Servo mit neuen Winkeln"""
        try:
            # Prüfe Eingabewerte
            left_angle = float(left_angle)
            right_angle = float(right_angle)
            
            if left_angle < 0 or left_angle > 90 or right_angle < 90 or right_angle > 180:
                raise ValueError("Winkel müssen zwischen 0° und 180° liegen")
                
            if abs(right_angle - left_angle) < 30:
                raise ValueError("Differenz zwischen links und rechts muss mindestens 30 Grad betragen")
                
            # Teste beide Positionen
            self.set_angle(servo_id, left_angle)
            time.sleep(0.5)
            self.set_angle(servo_id, right_angle)
            time.sleep(0.5)
            self.set_angle(servo_id, left_angle)
            
            # Wenn kein Fehler aufgetreten ist, speichere die neuen Werte
            self.config[str(servo_id)].update({
                'left_angle': left_angle,
                'right_angle': right_angle
            })
            
            # Aktualisiere Status
            self.servo_states[str(servo_id)].update({
                'error': False,
                'initialized': True,
                'position': 'left',
                'current_angle': left_angle
            })
            
            # Speichere Konfiguration
            self.save_config()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Kalibrierung von Servo {servo_id}: {e}")
            return False
            
    def get_servo_position(self, servo_id):
        """Ermittelt die aktuelle Position eines Servos (links/rechts)"""
        try:
            if str(servo_id) not in self.servo_states:
                return None
                
            return self.servo_states[str(servo_id)].get('position')
            
        except Exception as e:
            self.logger.error(f"Fehler beim Ermitteln der Servo-Position {servo_id}: {e}")
            return None
            
    def cleanup(self):
        """Räumt auf und gibt Ressourcen frei"""
        try:
            # Hier können Aufräumarbeiten durchgeführt werden
            pass
        except Exception as e:
            self.logger.error(f"Fehler beim Aufräumen: {e}")
            
    def __del__(self):
        """Destruktor"""
        self.cleanup()
        
    def test_servo(self, servo_num: int) -> bool:
        """Testet ob ein Servo funktioniert"""
        try:
            # Prüfe Board-Verfügbarkeit
            if servo_num >= 16:
                return False
                
            # Versuche den Servo zu bewegen
            try:
                # Mittelposition
                self.logger.debug(f"Bewege Servo {servo_num} sanft zur Mitte...")
                self.set_angle(servo_num, 90)
                time.sleep(0.1)
                
                # Nach rechts
                self.logger.debug(f"Bewege Servo {servo_num} sanft nach rechts...")
                self.set_angle(servo_num, 150)
                time.sleep(0.1)
                
                # Nach links
                self.logger.debug(f"Bewege Servo {servo_num} sanft nach links...")
                self.set_angle(servo_num, 30)
                time.sleep(0.1)
                
                # Zurück zur Startposition
                self.set_angle(servo_num, 30)
                
                return True
                
            except Exception as e:
                self.logger.debug(f"Servo {servo_num} reagiert nicht: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Testen von Servo {servo_num}: {e}")
            return False
            
    def initialize_servos(self):
        """Initialisiert und testet alle Servos"""
        self.logger.info("Initialisiere alle Servos...")
        
<<<<<<< HEAD
        # Teste jeden Servo
        for i in range(16):
            # Initialisiere Status
            self.servo_states[str(i)] = {
                'position': None,
                'current_angle': None,
                'last_move': 0,
                'error': False,
                'initialized': True,
                'status': 'initialized'
            }
=======
        # Lade die Servo-Konfigurationen
        servo_configs = self.config.get('SERVO_CONFIG', {}).get('SERVOS', [])
        if not servo_configs:
            self.logger.error("Keine Servo-Konfigurationen gefunden!")
            return
>>>>>>> 0040156a9d902821e6b3f4f85bd2630116956bdf
            
        # Test-Winkel für die Initialisierung
        start_angle = 90.0  # Startposition
        end_angle = 85.0    # Endposition
        step_size = 0.1     # Sehr kleine Schritte für sanfte Bewegung
            
        # Initialisiere jeden Servo
        for i, servo_config in enumerate(servo_configs):
            try:
                # Initialisiere Status
                self.servo_states[str(i)] = {
                    'position': None,
                    'current_angle': None,
                    'last_move': 0,
                    'error': False,
                    'initialized': False,
                    'status': 'unknown'
                }
                
                # Teste den Servo
                self.logger.info(f"Initialisiere Servo {i} mit Bewegung von {start_angle}° nach {end_angle}°")
                
                try:
                    # Hole den richtigen Servo
                    if i < 16:
                        servo = self.kit1.servo[i]
                    else:
                        if not self.dual_board:
                            raise Exception("Zweites Board nicht verfügbar")
                        servo = self.kit2.servo[i-16]
                    
                    # Setze auf Startposition
                    servo.angle = start_angle
                    time.sleep(0.5)  # Warte eine halbe Sekunde
                    
                    # Bewege sehr langsam zur Endposition
                    current_angle = start_angle
                    while current_angle > end_angle:
                        current_angle -= step_size
                        if current_angle < end_angle:
                            current_angle = end_angle
                        servo.angle = current_angle
                        time.sleep(0.01)  # 10ms Pause zwischen den Schritten
                    
                    # Markiere als erfolgreich initialisiert
                    self.servo_states[str(i)].update({
                        'position': 'initialized',
                        'current_angle': end_angle,
                        'initialized': True,
                        'status': 'initialized'
                    })
                    self.logger.info(f"Servo {i} erfolgreich initialisiert")
                    
                except Exception as e:
                    self.servo_states[str(i)].update({
                        'initialized': False,
                        'status': 'error',
                        'error': True
                    })
                    self.logger.warning(f"Fehler bei der Initialisierung von Servo {i}: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Fehler beim Laden der Konfiguration für Servo {i}: {str(e)}")
                self.servo_states[str(i)] = {
                    'initialized': False,
                    'status': 'config_error',
                    'error': True
                }
        
        self.logger.info("Servo-Initialisierung abgeschlossen")
