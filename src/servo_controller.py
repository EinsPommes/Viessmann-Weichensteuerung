import RPi.GPIO as GPIO
import time
import json
import os

class ServoController:
    def __init__(self):
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Standard-Konfiguration für MG90S Servos
        self.servo_pins = [17, 18, 27, 22, 23, 24, 25, 4, 5, 6, 13, 19, 26, 16, 20, 21]  # GPIO-Pins für 16 Servos
        
        # Servo-Konfiguration mit Geschwindigkeit
        self.servo_config = {}
        for i in range(16):
            self.servo_config[i] = {
                'left_angle': 2.5,    # Position A (0°)
                'right_angle': 12.5,  # Position B (180°)
                'speed': 0.5          # Geschwindigkeit (0.1 = langsam, 1.0 = schnell)
            }
        
        # Lade Servo-Konfiguration wenn vorhanden
        self.load_config()
        
        # Initialisiere Servos
        self.setup_servos()
        
        # Status-Dictionary für alle Servos
        self.servo_states = {}
        for servo_id in range(len(self.servo_pins)):
            self.servo_states[servo_id] = {
                'position': 'left',  # 'left' oder 'right'
                'sensor_ok': True    # True wenn Hall-Sensor OK
            }
    
    def load_config(self):
        """Lade Servo-Konfiguration aus config.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'servo_config' in config:
                        self.servo_config = config['servo_config']
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
    
    def save_config(self):
        """Speichere Servo-Konfiguration in config.json"""
        config = {
            'servo_config': self.servo_config
        }
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")
    
    def set_servo_config(self, servo_id, left_angle=None, right_angle=None, speed=None):
        """
        Konfiguriert einen Servo
        
        Args:
            servo_id (int): ID des Servos (0-15)
            left_angle (float): Winkel für Position A (2.5-12.5)
            right_angle (float): Winkel für Position B (2.5-12.5)
            speed (float): Geschwindigkeit (0.1-1.0)
        """
        if servo_id not in self.servo_config:
            raise ValueError(f"Ungültige Servo-ID: {servo_id}")
            
        if left_angle is not None:
            if not 2.5 <= left_angle <= 12.5:
                raise ValueError("Winkel muss zwischen 2.5 und 12.5 liegen")
            self.servo_config[servo_id]['left_angle'] = left_angle
            
        if right_angle is not None:
            if not 2.5 <= right_angle <= 12.5:
                raise ValueError("Winkel muss zwischen 2.5 und 12.5 liegen")
            self.servo_config[servo_id]['right_angle'] = right_angle
            
        if speed is not None:
            if not 0.1 <= speed <= 1.0:
                raise ValueError("Geschwindigkeit muss zwischen 0.1 und 1.0 liegen")
            self.servo_config[servo_id]['speed'] = speed
        
        # Speichere neue Konfiguration
        self.save_config()
    
    def get_servo_config(self, servo_id):
        """
        Gibt die Konfiguration eines Servos zurück
        
        Args:
            servo_id (int): ID des Servos (0-15)
            
        Returns:
            dict: Konfiguration des Servos
        """
        if servo_id not in self.servo_config:
            raise ValueError(f"Ungültige Servo-ID: {servo_id}")
        return self.servo_config[servo_id]
    
    def set_servo_position(self, servo_id, position):
        """
        Setzt die Position eines Servos
        
        Args:
            servo_id (int): ID des Servos (0-15)
            position (str): 'left' oder 'right'
        """
        if servo_id not in self.servo_config:
            raise ValueError(f"Ungültige Servo-ID: {servo_id}")
        
        if position not in ['left', 'right']:
            raise ValueError(f"Ungültige Position: {position}")
        
        try:
            pin = self.servo_pins[servo_id]
            config = self.servo_config[servo_id]
            angle = config['left_angle'] if position == 'left' else config['right_angle']
            speed = config['speed']
            
            # Setze Servo-Position
            pwm = GPIO.PWM(pin, 50)  # 50 Hz
            pwm.start(0)  # Start mit 0
            
            # Sanft zur Zielposition bewegen
            current = 0
            target = angle
            step = speed if target > current else -speed
            
            while abs(current - target) > 0.1:
                current += step
                pwm.ChangeDutyCycle(current)
                time.sleep(0.02)  # 20ms Pause zwischen Schritten
            
            # Finale Position
            pwm.ChangeDutyCycle(target)
            time.sleep(0.5)
            
            # PWM stoppen
            pwm.stop()
            
            # Aktualisiere Status
            self.servo_states[servo_id]['position'] = position
            
        except Exception as e:
            print(f"Fehler beim Setzen der Servo-Position: {e}")
            raise
    
    def get_servo_position(self, servo_id):
        """
        Gibt die aktuelle Position eines Servos zurück
        
        Args:
            servo_id (int): ID des Servos (0-15)
            
        Returns:
            str: 'left' oder 'right'
        """
        if servo_id < 0 or servo_id >= len(self.servo_pins):
            raise ValueError(f"Ungültige Servo-ID: {servo_id}")
        
        return self.servo_states[servo_id]['position']
    
    def setup_servos(self):
        """Initialisiere die GPIO-Pins für die Servos"""
        try:
            for pin in self.servo_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
        except Exception as e:
            print(f"Fehler beim Setup der GPIO-Pins: {e}")
    
    def cleanup(self):
        """Aufräumen der GPIO-Pins"""
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"Fehler beim Cleanup: {e}")