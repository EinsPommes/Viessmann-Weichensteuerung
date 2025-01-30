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
            self.kit1._pca.frequency = 50  # Setze Frequenz auf 50Hz
            
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
            config = self.config.get(str(servo_id), self.DEFAULT_CONFIG)
            
            # Setze Winkel basierend auf Richtung
            if direction == 'left':
                angle = config['left_angle']
            else:
                angle = config['right_angle']
                
            # Bewege Servo
            self.kit1.servo[servo_id].angle = angle
            
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
            if servo_num >= 16:
                raise Exception("Ungültige Servo-ID")
            self.kit1.servo[servo_num].angle = angle
                
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
        self.logger.info("Teste alle Servos...")
        
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
