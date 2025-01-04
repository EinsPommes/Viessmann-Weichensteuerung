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
        
        # MG90S Servo Kalibrierung:
        # 2.5 = 0° / 7.5 = 90° / 12.5 = 180°
        self.servo_left_angles = [2.5] * 16   # 0° Position (links)
        self.servo_right_angles = [12.5] * 16  # 180° Position (rechts)
        
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
                    # Nur gültige Konfigurationen übernehmen
                    if len(config.get('servo_pins', [])) == 16:
                        self.servo_pins = config['servo_pins']
                    if len(config.get('servo_left_angles', [])) == 16:
                        self.servo_left_angles = config['servo_left_angles']
                    if len(config.get('servo_right_angles', [])) == 16:
                        self.servo_right_angles = config['servo_right_angles']
        except (FileNotFoundError, json.JSONDecodeError):
            # Bei Fehler Standard-Konfiguration behalten
            pass
        
        # Konfiguration speichern
        self.save_config()
    
    def save_config(self):
        """Speichere Servo-Konfiguration in config.json"""
        config = {
            'servo_pins': self.servo_pins,
            'servo_left_angles': self.servo_left_angles,
            'servo_right_angles': self.servo_right_angles
        }
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")
    
    def setup_servos(self):
        """Initialisiere die GPIO-Pins für die Servos"""
        try:
            for pin in self.servo_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
        except Exception as e:
            print(f"Fehler beim Setup der GPIO-Pins: {e}")
    
    def set_servo_position(self, servo_id, position):
        """
        Setzt die Position eines Servos
        
        Args:
            servo_id (int): ID des Servos (0-15)
            position (str): 'left' oder 'right'
        """
        if servo_id < 0 or servo_id >= len(self.servo_pins):
            raise ValueError(f"Ungültige Servo-ID: {servo_id}")
        
        if position not in ['left', 'right']:
            raise ValueError(f"Ungültige Position: {position}")
        
        try:
            pin = self.servo_pins[servo_id]
            angle = self.servo_left_angles[servo_id] if position == 'left' else self.servo_right_angles[servo_id]
            
            # Setze Servo-Position
            pwm = GPIO.PWM(pin, 50)  # 50 Hz
            pwm.start(0)  # Start mit 0
            
            # Sanft zur Zielposition bewegen
            current = 0
            target = angle
            step = 0.5 if target > current else -0.5
            
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
    
    def cleanup(self):
        """Aufräumen der GPIO-Pins"""
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"Fehler beim Cleanup: {e}")
