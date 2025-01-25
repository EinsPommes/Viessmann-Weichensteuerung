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
        'left_angle': 30.0,   # Standardwinkel für linke Position
        'right_angle': 150.0, # Standardwinkel für rechte Position
        'speed': 0.5         # Standard-Geschwindigkeit
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
            self.logger.info("ServoKit 1 (0x40) erfolgreich initialisiert")
            
            # Versuche zweites Board zu initialisieren
            try:
                self.kit2 = ServoKit(channels=16, i2c=self.i2c, address=0x41)
                self.dual_board = True
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
                        'left_angle': 0,
                        'right_angle': 180,
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
            
            # Teste alle Servos
            self.logger.info("Teste alle Servos...")
            
            for i in range(16):
                if i >= 8 and not self.dual_board:
                    continue
                    
                try:
                    # Versuche den Servo zu bewegen
                    if i < 8:
                        self.kit1.servo[i].angle = 90
                        time.sleep(0.1)
                        self.kit1.servo[i].angle = self.config[str(i)]['left_angle']
                        time.sleep(0.1)
                        
                        # Wenn kein Fehler aufgetreten ist, markiere als initialisiert
                        self.servo_states[str(i)].update({
                            'error': False,
                            'initialized': True,
                            'position': 'left',
                            'current_angle': self.config[str(i)]['left_angle'],
                            'status': 'initialized'
                        })
                        self.logger.info(f"Servo {i} gefunden und initialisiert")
                    elif self.dual_board:
                        self.kit2.servo[i-8].angle = 90
                        time.sleep(0.1)
                        self.kit2.servo[i-8].angle = self.config[str(i)]['left_angle']
                        time.sleep(0.1)
                        
                        # Wenn kein Fehler aufgetreten ist, markiere als initialisiert
                        self.servo_states[str(i)].update({
                            'error': False,
                            'initialized': True,
                            'position': 'left',
                            'current_angle': self.config[str(i)]['left_angle'],
                            'status': 'initialized'
                        })
                        self.logger.info(f"Servo {i} gefunden und initialisiert")
                        
                except Exception as e:
                    self.logger.warning(f"Servo {i} nicht gefunden: {e}")
                    self.servo_states[str(i)].update({
                        'error': True,
                        'initialized': False,
                        'position': None,
                        'current_angle': None,
                        'status': 'error'
                    })
            
            # Debug-Ausgabe der Servo-Status
            for i in range(16):
                self.logger.debug(f"Servo {i} Status nach Initialisierung: {self.servo_states.get(str(i))}")
            
            # Speichere aktualisierte Konfiguration
            self.save_config()
            self.logger.info("Servo-Initialisierung abgeschlossen")
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung: {e}")
            raise
            
    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            # Prüfe ob Servo initialisiert
            if not self.servo_states[str(servo_id)]['initialized']:
                raise Exception("Servo nicht initialisiert")
                
            # Setze Status auf "moving"
            self.servo_states[str(servo_id)]['status'] = 'moving'
            
            # Hole Zielwinkel aus Konfiguration
            target_angle = self.config[str(servo_id)][f'{direction}_angle']
            
            # Bewege Servo
            if servo_id < 8:
                self.kit1.servo[servo_id].angle = target_angle
            else:
                if not self.dual_board:
                    raise Exception("Zweites Board nicht verfügbar")
                self.kit2.servo[servo_id-8].angle = target_angle
                
            # Aktualisiere Status
            self.servo_states[str(servo_id)].update({
                'position': direction,
                'current_angle': target_angle,
                'last_move': time.time(),
                'error': False,
                'initialized': True,
                'status': 'initialized'
            })
            
            # Speichere Konfiguration
            self.save_config()
            self.logger.info(f"Servo {servo_id} erfolgreich bewegt zu {direction} (Winkel: {target_angle})")
            
        except Exception as e:
            self.servo_states[str(servo_id)]['status'] = 'error'
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {e}")
            raise
            
    def create_default_config(self):
        """Erstellt eine Standard-Konfiguration"""
        try:
            # Erstelle leeres Konfigurations-Dictionary
            config = {}
            
            # Füge Standard-Konfiguration für jedes Board hinzu
            for i in range(16):  # Erstes Board
                config[str(i)] = {
                    'left_angle': 0,
                    'right_angle': 180,
                    'speed': 0.5
                }
                
            if self.dual_board:
                for i in range(16):  # Zweites Board
                    config[str(i+16)] = {
                        'left_angle': 0,
                        'right_angle': 180,
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
                        'left_angle': 0,
                        'right_angle': 180,
                        'speed': 0.5
                    }
                    
            if self.dual_board:
                for i in range(16):  # Zweites Board
                    if str(i+16) not in config:
                        self.logger.warning(f"Servo {i+16} nicht in Konfiguration gefunden, füge Standard-Konfiguration hinzu")
                        config[str(i+16)] = {
                            'left_angle': 0,
                            'right_angle': 180,
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
            
    def set_servo_angle(self, servo_id, angle):
        """Setzt den Winkel eines Servos direkt"""
        try:
            # Prüfe Parameter
            if not isinstance(servo_id, int):
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")
                
            try:
                angle = float(angle)
            except (ValueError, TypeError):
                raise ValueError(f"Ungültiger Winkel: {angle}")
                
            if angle < 0 or angle > 180:
                raise ValueError(f"Winkel {angle}° außerhalb der Grenzen (0-180)")
                
            self.logger.debug(f"Setze Servo {servo_id} auf {angle}°")
            
            # Bewege Servo
            if servo_id < 8:
                self.kit1.servo[servo_id].angle = angle
            else:
                if not self.dual_board:
                    raise Exception(f"Servo {servo_id} nicht verfügbar (kein zweites Board)")
                self.kit2.servo[servo_id-8].angle = angle
                
            # Aktualisiere Status
            self.servo_states[servo_id].update({
                'current_angle': angle,
                'last_move': time.time(),
                'error': False,
                'initialized': True
            })
            
            # Bestimme Position basierend auf Konfiguration
            config = self.config.get(str(servo_id))
            if config:
                left_angle = float(config['left_angle'])
                right_angle = float(config['right_angle'])
                
                # Toleranz von 5 Grad
                if abs(angle - left_angle) <= 5:
                    self.servo_states[servo_id]['position'] = 'left'
                elif abs(angle - right_angle) <= 5:
                    self.servo_states[servo_id]['position'] = 'right'
                else:
                    self.servo_states[servo_id]['position'] = None
            
            self.logger.debug(f"Servo {servo_id} Status: {self.servo_states[servo_id]}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen des Winkels für Servo {servo_id}: {e}")
            if str(servo_id) in self.servo_states:
                self.servo_states[servo_id]['error'] = True
            raise
            
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
            if str(servo_id) not in self.config:
                return None
                
            if servo_id < 8:
                current_angle = self.kit1.servo[servo_id].angle
            else:
                if not self.dual_board:
                    raise Exception(f"Servo {servo_id} nicht verfügbar (kein zweites Board)")
                current_angle = self.kit2.servo[servo_id-8].angle
                
            left_angle = self.config[str(servo_id)]['left_angle']
            right_angle = self.config[str(servo_id)]['right_angle']
            
            # Toleranz von 5 Grad
            if abs(current_angle - left_angle) <= 5:
                return 'left'
            elif abs(current_angle - right_angle) <= 5:
                return 'right'
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Fehler beim Ermitteln der Servo-Position {servo_id}: {e}")
            return None
            
    def cleanup(self):
        """Räumt auf und gibt Ressourcen frei"""
        try:
            # Alle Servos auf 0
            if self.kit1:
                for i in range(16):
                    try:
                        self.kit1.servo[i].angle = None
                    except:
                        pass
                        
            if self.kit2:
                for i in range(16):
                    try:
                        self.kit2.servo[i].angle = None
                    except:
                        pass
        except Exception as e:
            self.logger.error(f"Fehler beim Aufräumen: {e}")
