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
        'speed': 0.5          # Standard-Geschwindigkeit
    }
    
    def __init__(self):
        """Initialisiert den ServoKit Controller"""
        try:
            # Logger initialisieren
            self.logger = logging.getLogger('servo_controller')
            self.logger.setLevel(logging.DEBUG)
            
            # Config-Datei
            self.config_file = "servo_config.json"
            
            # Erstelle I2C Bus
            self.i2c = busio.I2C(board.SCL, board.SDA)
            
            # Erstelle ServoKit für Board 1
            self.kit1 = ServoKit(channels=16, i2c=self.i2c, address=0x40)
            
            # PWM Werte für verschiedene Positionen (basierend auf 16-bit Timer)
            # Berechnung: duty_cycle = (pulsewidth_ms * 65535) / (1000 / frequency)
            # Bei 50Hz: duty_cycle = pulsewidth_ms * 3277
            self.PWM_LEFT = 2500    # 0.76ms = -90° (links)
            self.PWM_CENTER = 4915  # 1.5ms = 0° (mitte)
            self.PWM_RIGHT = 7300   # 2.23ms = +90° (rechts)
            
            # Aktiviere alle Servos auf Board 1 mit direkter PWM Steuerung
            for i in range(8):
                # Setze PWM Frequenz auf 50Hz (Standard für Servos)
                self.kit1._pca.frequency = 50
                # Aktiviere den Kanal
                self.kit1._pca.channels[i].duty_cycle = self.PWM_LEFT
                
            self.logger.info("ServoKit 1 (0x40) erfolgreich initialisiert")
            
            # Versuche zweites Board zu initialisieren
            try:
                self.kit2 = ServoKit(channels=16, i2c=self.i2c, address=0x41)
                self.dual_board = True
                # Aktiviere alle Servos auf Board 2
                for i in range(8):
                    self.kit2._pca.frequency = 50
                    self.kit2._pca.channels[i].duty_cycle = self.PWM_LEFT
                self.logger.info("Zweites PCA9685 Board gefunden")
            except Exception as e:
                self.kit2 = None
                self.dual_board = False
                self.logger.warning(f"Zweites Board nicht gefunden, nutze nur Board 1: {str(e)}")
                
            # Konfiguration laden oder erstellen
            if not os.path.exists(self.config_file):
                self.create_default_config()
                
            self.config = self.load_config()
            
            # Servo-Status initialisieren
            self.servo_states = {}
            for i in range(16):
                if str(i) not in self.config:
                    self.config[str(i)] = {
                        'left_angle': 30,
                        'right_angle': 150,
                        'speed': 0.5
                    }
                    self.logger.warning(f"Servo {i} nicht in Konfiguration gefunden, füge Standard-Konfiguration hinzu")
                    
                self.servo_states[str(i)] = {
                    'position': None,
                    'current_angle': None,
                    'last_move': 0,
                    'error': False,
                    'initialized': False,
                    'status': 'unknown'
                }
            
            # Initialisiere Servos
            self.initialize_servos()
            
            # Speichere aktualisierte Konfiguration
            self.save_config()
            self.logger.info("Servo-Initialisierung abgeschlossen")
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung: {e}")
            raise
            
    def _is_servo_available(self, servo_num: int) -> bool:
        """Prüft ob ein Servo verfügbar und initialisiert ist"""
        # Prüfe ob Servo im gültigen Bereich
        if not (0 <= servo_num < 16):
            return False
            
        # Prüfe ob Servo initialisiert ist
        servo_state = self.servo_states.get(str(servo_num), {})
        return servo_state.get('initialized', False)
        
    def move_servo(self, servo_num: int, position: str) -> None:
        """Bewegt einen Servo in die angegebene Position"""
        try:
            # Prüfe ob Servo verfügbar
            if not self._is_servo_available(servo_num):
                raise Exception(f"Servo {servo_num + 1} nicht verfügbar")
                
            # Hole Konfiguration für den Servo
            servo_config = self.config.get(str(servo_num), {})
            left_angle = float(servo_config.get('left_angle', 30.0))  # Standard: 30°
            right_angle = float(servo_config.get('right_angle', 150.0))  # Standard: 150°
            
            # Bestimme Zielwinkel
            if position == 'left':
                target_angle = left_angle
            elif position == 'right':
                target_angle = right_angle
            else:
                raise ValueError(f"Ungültige Position: {position}")
                
            # Setze Winkel
            self.set_angle(servo_num, target_angle)
            
            # Aktualisiere Status
            self.servo_states[str(servo_num)]['position'] = position
            self.servo_states[str(servo_num)]['current_angle'] = target_angle
            self.servo_states[str(servo_num)]['last_move'] = time.time()
            
            self.logger.info(f"Servo {servo_num + 1} auf Position {position} ({target_angle}°) gesetzt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_num + 1}: {e}")
            self.servo_states[str(servo_num)]['error'] = True
            raise
            
    def move_servo_smooth(self, channel, start_duty, target_duty, steps=10):
        """Bewegt einen Servo sanft von start_duty zu target_duty"""
        current = start_duty
        step = (target_duty - start_duty) / steps
        
        for _ in range(steps):
            current += step
            channel.duty_cycle = int(current)
            time.sleep(0.02)  # 20ms pro Schritt
            
    def create_default_config(self):
        """Erstellt eine Standard-Konfiguration"""
        try:
            # Erstelle leeres Konfigurations-Dictionary
            config = {}
            
            # Füge Standard-Konfiguration für jedes Board hinzu
            for i in range(16):  # Erstes Board
                config[str(i)] = {
                    'left_angle': 30,
                    'right_angle': 150,
                    'speed': 0.5
                }
                
            if self.dual_board:
                for i in range(16):  # Zweites Board
                    config[str(i+16)] = {
                        'left_angle': 30,
                        'right_angle': 150,
                        'speed': 0.5
                    }
            
            # Speichere Konfiguration
            self.config = config
            self.save_config()
            
            self.logger.info("Standard-Konfiguration erstellt")
            return config
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Standard-Konfiguration: {e}")
            raise
            
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
                        'speed': 0.5
                    }
                    
            if self.dual_board:
                for i in range(16):  # Zweites Board
                    if str(i+16) not in config:
                        self.logger.warning(f"Servo {i+16} nicht in Konfiguration gefunden, füge Standard-Konfiguration hinzu")
                        config[str(i+16)] = {
                            'left_angle': 30,
                            'right_angle': 150,
                            'speed': 0.5
                        }
            
            self.logger.info("Konfiguration erfolgreich geladen")
            return config
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            return self.create_default_config()
            
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
            
    def set_angle(self, servo_num: int, angle: float) -> None:
        """Setzt einen Servo auf einen bestimmten Winkel"""
        try:
            # Validiere Winkel
            if not (0 <= angle <= 180):
                raise ValueError(f"Winkel muss zwischen 0° und 180° liegen (war: {angle})")
                
            # Setze Winkel je nach Board
            if servo_num < 8:
                self.kit1.servo[servo_num].angle = angle
            else:
                if not self.dual_board:
                    raise Exception(f"Servo {servo_num + 1} nicht verfügbar (kein zweites Board)")
                self.kit2.servo[servo_num-8].angle = angle
                
            self.logger.debug(f"Setze Servo {servo_num} auf {angle}°")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen des Winkels für Servo {servo_num + 1}: {e}")
            raise
            
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
            
    def get_servo_status(self, servo_id):
        """Gibt den Status eines Servos zurück"""
        status = {
            'initialized': False,
            'error': False,
            'position': None,
            'current_angle': None
        }
        
        try:
            # Prüfe ob Servo in Konfiguration
            if str(servo_id) in self.config:
                status['initialized'] = True
                if servo_id < 8:
                    status['current_angle'] = self.kit1.servo[servo_id].angle
                else:
                    if not self.dual_board:
                        raise Exception(f"Servo {servo_id} nicht verfügbar (kein zweites Board)")
                    status['current_angle'] = self.kit2.servo[servo_id-8].angle
                status['position'] = self.get_servo_position(servo_id)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Servo-Status {servo_id}: {e}")
            status['error'] = True
            
        return status
        
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
            if servo_num >= 8 and not self.dual_board:
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
        self.logger.info("Teste alle Servos...")
        
        # Teste jeden Servo
        for i in range(16):
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
            if self.test_servo(i):
                self.servo_states[str(i)].update({
                    'position': 'left',
                    'current_angle': 30,
                    'initialized': True,
                    'status': 'initialized'
                })
                self.logger.info(f"Servo {i} gefunden und initialisiert")
            else:
                self.servo_states[str(i)].update({
                    'initialized': False,
                    'status': 'not_found'
                })
                self.logger.warning(f"Servo {i} nicht gefunden oder nicht funktionsfähig")
                
        # Speichere den Status
        self.save_config()
        self.logger.info("Servo-Initialisierung abgeschlossen")
