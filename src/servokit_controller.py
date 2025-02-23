import time
import json
import os
import logging
from adafruit_servokit import ServoKit
import board
import busio

class ServoKitController:
    """Klasse zur Steuerung der Servos über den ServoKit"""
    
    def __init__(self):
        """Initialisiert den ServoKit Controller"""
        try:
            # Logger initialisieren
            self.logger = logging.getLogger('servo_controller')
            self.logger.setLevel(logging.DEBUG)
            
            # Config-Datei Pfad bestimmen (absoluter Pfad)
            self.config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.json"))
            self.logger.info(f"Config-Datei Pfad: {self.config_file}")
            
            # Lade Konfiguration
            self.config = self.load_config()
            
            # Erstelle ServoKit für 16 Servos
            self.kit1 = ServoKit(channels=16)
            
            # Initialisiere Servo-Status
            self.servo_states = {}
            for i in range(16):
                self.servo_states[str(i)] = {
                    'position': None,
                    'current_angle': None,
                    'last_move': time.time(),
                    'error': False,
                    'initialized': True,
                    'status': 'initialized'
                }
                
            self.logger.info("ServoKit Controller erfolgreich initialisiert")
            
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

            # Lade aktuelle Konfiguration neu
            self.config = self.load_config()
            self.logger.debug(f"Geladene Konfiguration: {json.dumps(self.config, indent=2)}")

            # Hole Konfiguration für den Servo
            servo_config = self.config.get('SERVO_CONFIG', {})
            servos = servo_config.get('SERVOS', [])
            servo_data = next((s for s in servos if s['id'] == servo_id), None)
            
            if not servo_data:
                self.logger.warning(f"Keine Konfiguration für Servo {servo_id} gefunden")
                # Erstelle Standard-Konfiguration für diesen Servo
                servo_data = {
                    'id': servo_id,
                    'gpio': servo_id,
                    'left_angle': 45.0,
                    'right_angle': 135.0,
                    'min_pulse': 500,
                    'max_pulse': 2500
                }
            
            # Setze Zielwinkel basierend auf Richtung
            target_angle = servo_data['left_angle'] if direction == 'left' else servo_data['right_angle']
            
            # Setze Pulslängen
            min_pulse = servo_data.get('min_pulse', 500)
            max_pulse = servo_data.get('max_pulse', 2500)
            self.kit1.servo[servo_id].set_pulse_width_range(min_pulse, max_pulse)
            
            # Bewege Servo
            self.logger.info(f"Bewege Servo {servo_id} nach {direction} (Winkel: {target_angle}°)")
            self.kit1.servo[servo_id].angle = target_angle
            
            # Aktualisiere Status
            self.servo_states[str(servo_id)].update({
                'position': direction,
                'current_angle': target_angle,
                'last_move': time.time(),
                'error': False,
                'status': 'ok'
            })
            
            return {
                'status': 'success',
                'position': direction,
                'angle': target_angle
            }
            
        except Exception as e:
            error_msg = f"Fehler beim Bewegen von Servo {servo_id}: {str(e)}"
            self.logger.error(error_msg)
            
            # Aktualisiere Fehlerstatus
            if str(servo_id) in self.servo_states:
                self.servo_states[str(servo_id)].update({
                    'error': True,
                    'status': 'error',
                    'message': str(e)
                })
            
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def load_config(self):
        """Lädt die Konfiguration aus der Datei"""
        try:
            self.logger.info(f"Versuche Config-Datei zu laden von: {self.config_file}")
            
            # Prüfe ob Datei existiert
            if not os.path.exists(self.config_file):
                self.logger.error(f"Config-Datei nicht gefunden: {self.config_file}")
                raise FileNotFoundError(f"Config-Datei nicht gefunden: {self.config_file}")
                
            # Lade Konfiguration
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.logger.info(f"Config-Datei erfolgreich geladen: {json.dumps(config, indent=2)}")
                return config
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
            raise
            
    def save_config(self):
        """Speichert die Konfiguration in der JSON-Datei"""
        try:
            self.logger.info(f"Speichere Konfiguration in: {self.config_file}")
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info("Konfiguration erfolgreich gespeichert")
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Konfiguration: {str(e)}")
            raise
            
    def set_angle(self, servo_num: int, angle: float, steps=10) -> None:
        """Setzt einen Servo auf einen bestimmten Winkel"""
        try:
            # Validiere Servo-Nummer
            if not 0 <= servo_num < 16:
                raise ValueError(f"Ungültige Servo-Nummer: {servo_num}")
            
            # Validiere Winkel
            if not 0 <= angle <= 180:
                raise ValueError(f"Winkel muss zwischen 0° und 180° liegen (war: {angle})")
            
            # Hole Servo-Konfiguration
            servo_config = self.config.get('SERVO_CONFIG', {})
            servos = servo_config.get('SERVOS', [])
            servo_data = next((s for s in servos if s['id'] == servo_num), None)
            
            # Hole aktuellen Winkel, falls vorhanden, sonst setze auf 90°
            current_angle = self.servo_states[str(servo_num)].get('current_angle')
            if current_angle is None:
                current_angle = 90.0  # Standardwinkel
                
            # Berechne Schrittgröße
            angle_diff = angle - current_angle
            step_size = angle_diff / steps
            
            # Bewege Servo schrittweise
            for step in range(steps):
                current = current_angle + (step_size * (step + 1))
                
                if servo_data:
                    # Berechne duty cycle basierend auf min_duty und max_duty
                    min_duty = float(servo_data.get('min_duty', 2.5))
                    max_duty = float(servo_data.get('max_duty', 12.5))
                    duty_range = max_duty - min_duty
                    duty = min_duty + (current / 180.0) * duty_range
                    self.kit1._pca.channels[servo_num].duty_cycle = int(duty * 65535 / 100)
                else:
                    # Standard-Verhalten wenn keine spezifische Konfiguration
                    self.kit1.servo[servo_num].angle = current
                    
                time.sleep(0.02)  # Kleine Pause zwischen den Schritten
            
            # Setze finalen Winkel
            if servo_data:
                min_duty = float(servo_data.get('min_duty', 2.5))
                max_duty = float(servo_data.get('max_duty', 12.5))
                duty_range = max_duty - min_duty
                duty = min_duty + (angle / 180.0) * duty_range
                self.kit1._pca.channels[servo_num].duty_cycle = int(duty * 65535 / 100)
            else:
                self.kit1.servo[servo_num].angle = angle
            
            # Aktualisiere Status
            self.servo_states[str(servo_num)].update({
                'current_angle': angle,
                'last_move': time.time(),
                'error': False,
                'status': 'initialized'
            })
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen des Winkels für Servo {servo_num}: {e}")
            if str(servo_num) in self.servo_states:
                self.servo_states[str(servo_num)].update({
                    'error': True,
                    'status': 'error',
                    'message': str(e)
                })
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
            self.config['SERVO_CONFIG']['SERVOS'][servo_id]['left_angle'] = left_angle
            self.config['SERVO_CONFIG']['SERVOS'][servo_id]['right_angle'] = right_angle
            
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
            # Deaktiviere alle Servos
            for i in range(16):
                # Setze PWM auf 0 um den Servo stromlos zu machen
                self.kit1._pca.channels[i].duty_cycle = 0
            
            self.logger.info("Alle Servos deaktiviert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aufräumen: {e}")
            
    def __del__(self):
        """Destruktor - wird beim Löschen des Objekts aufgerufen"""
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
        
        # Lade die Servo-Konfigurationen
        servo_configs = self.config.get('SERVO_CONFIG', {}).get('SERVOS', [])
        if not servo_configs:
            self.logger.error("Keine Servo-Konfigurationen gefunden!")
            return
        
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
                    servo = self.kit1.servo[i]
                    
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

    def update_servo_config(self, servo_id, config_data):
        """Aktualisiert die Konfiguration eines Servos"""
        try:
            # Prüfe ob Servo-ID gültig ist
            if servo_id >= 16:
                raise Exception("Ungültige Servo-ID")

            # Validiere die Winkel
            if 'left_angle' in config_data:
                left_angle = float(config_data['left_angle'])
                if not 0 <= left_angle <= 180:
                    raise ValueError(f"Ungültiger linker Winkel: {left_angle}. Muss zwischen 0 und 180 sein.")
                config_data['left_angle'] = left_angle

            if 'right_angle' in config_data:
                right_angle = float(config_data['right_angle'])
                if not 0 <= right_angle <= 180:
                    raise ValueError(f"Ungültiger rechter Winkel: {right_angle}. Muss zwischen 0 und 180 sein.")
                config_data['right_angle'] = right_angle

            # Hole aktuelle Konfiguration
            if 'SERVO_CONFIG' not in self.config:
                self.config['SERVO_CONFIG'] = {}
            if 'SERVOS' not in self.config['SERVO_CONFIG']:
                self.config['SERVO_CONFIG']['SERVOS'] = []
            
            servos = self.config['SERVO_CONFIG']['SERVOS']
            
            # Finde den Servo in der Konfiguration
            servo_index = next((i for i, s in enumerate(servos) if s['id'] == servo_id), None)
            
            if servo_index is not None:
                # Aktualisiere existierenden Servo
                current_config = servos[servo_index]
                current_config.update(config_data)
                # Stelle sicher, dass die ID nicht überschrieben wird
                current_config['id'] = servo_id
            else:
                # Erstelle neue Servo-Konfiguration
                new_config = {
                    'id': servo_id,
                    'gpio': servo_id,
                    'left_angle': 45,
                    'right_angle': 135,
                    'min_pulse': 500,
                    'max_pulse': 2500
                }
                new_config.update(config_data)
                servos.append(new_config)
            
            # Speichere die aktualisierte Konfiguration
            self.save_config()
            
            self.logger.info(f"Konfiguration für Servo {servo_id} aktualisiert: {json.dumps(config_data, indent=2)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Servo-Konfiguration: {str(e)}")
            raise
