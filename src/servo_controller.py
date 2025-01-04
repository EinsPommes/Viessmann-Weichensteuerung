import RPi.GPIO as GPIO
import time
import json
import os

class ServoController:
    def __init__(self):
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Lade Servo-Konfiguration
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
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.servo_pins = config.get('servo_pins', [])
                self.servo_left_angles = config.get('servo_left_angles', [])
                self.servo_right_angles = config.get('servo_right_angles', [])
        except (FileNotFoundError, json.JSONDecodeError):
            # Standard-Konfiguration für MG90S Servos
            self.servo_pins = [17, 18, 27, 22, 23, 24, 25, 4, 5, 6, 13, 19, 26, 16, 20, 21]  # GPIO-Pins für 16 Servos
            
            # MG90S spezifische Winkel:
            # - Duty Cycle von 5% (1ms) für 0° bis 10% (2ms) für 180°
            # - Wir nutzen ~45° für links und ~135° für rechts
            self.servo_left_angles = [6.5] * 16  # ~45° Position (links)
            self.servo_right_angles = [8.5] * 16  # ~135° Position (rechts)
            self.save_config()
    
    def save_config(self):
        """Speichere Servo-Konfiguration in config.json"""
        config = {
            'servo_pins': self.servo_pins,
            'servo_left_angles': self.servo_left_angles,
            'servo_right_angles': self.servo_right_angles
        }
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def setup_servos(self):
        """Initialisiere die GPIO-Pins für die Servos"""
        for pin in self.servo_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
    
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
            
        pin = self.servo_pins[servo_id]
        angle = self.servo_left_angles[servo_id] if position == 'left' else self.servo_right_angles[servo_id]
        
        # Setze Servo-Position
        pwm = GPIO.PWM(pin, 50)  # 50 Hz
        pwm.start(angle)
        time.sleep(0.5)
        pwm.stop()
        
        # Aktualisiere Status
        self.servo_states[servo_id]['position'] = position
    
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
        GPIO.cleanup()
