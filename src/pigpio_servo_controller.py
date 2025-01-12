import pigpio
import time
import json
import os
import logging
import asyncio
import shutil
from datetime import datetime
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor
import glob

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
                for sid in range(16):
                    self.locked_servos.add(sid)
                    self.last_movement[sid] = time.time() + self.config['GLOBAL_LOCK_DURATION']

class PiGPIOServoController:
    def __init__(self, pi, servo_pins, led_pins=None, config_file=None):
        """Initialisiert den Servo-Controller"""
        self.pi = pi
        self.servo_pins = servo_pins
        self.led_pins = led_pins if led_pins else [None] * len(servo_pins)
        self.config_file = config_file if config_file else 'config.json'
        
        # Logger initialisieren
        self.logger = logging.getLogger('ServoController')
        
        # Initialisiere Servos
        for pin in self.servo_pins:
            if pin is not None:
                self.pi.set_mode(pin, pigpio.OUTPUT)
                # Setze PWM-Frequenz auf 50Hz (Standard für Servos)
                self.pi.set_PWM_frequency(pin, 50)
                # Kein PWM-Signal am Start
                self.pi.set_servo_pulsewidth(pin, 0)
        
        # Initialisiere LEDs
        for pin in self.led_pins:
            if pin is not None:
                self.pi.set_mode(pin, pigpio.OUTPUT)
                self.pi.write(pin, 0)  # LED aus
                
        # Lade Konfiguration
        self.load_config()
        
        # Initialisiere Servo-Zustände
        self.servo_states = {}
        for i in range(len(servo_pins)):
            self.servo_states[i] = {
                'position': None,  # 'left', 'right' oder None
                'current_angle': None,  # Aktueller Winkel
                'last_move': 0,
                'move_count': 0,
                'error': False
            }

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
        :param servo_id: ID des Servos (0-15)
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
        :param servo_id: ID des Servos (0-15)
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
                self.servo_states[servo_id]['move_count'] += 1
                self.servo_states[servo_id]['error'] = False
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
