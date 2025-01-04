import RPi.GPIO as GPIO
import time
import json

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
            with open('src/config.json', 'r') as f:
                config = json.load(f)
                self.servo_pins = config.get('servo_pins', [])
                self.servo_left_angles = config.get('servo_left_angles', [])
                self.servo_right_angles = config.get('servo_right_angles', [])
        except FileNotFoundError:
            # Standard-Konfiguration für MG90S Servos
            self.servo_pins = [17, 18, 27, 22, 23, 24, 25, 4, 5, 6, 13, 19]  # GPIO-Pins für 12 Servos
            
            # MG90S spezifische Winkel:
            # - Duty Cycle von 5% (1ms) für 0° bis 10% (2ms) für 180°
            # - Wir nutzen ~45° für links und ~135° für rechts
            self.servo_left_angles = [6.5] * 12  # ~45° Position (links)
            self.servo_right_angles = [8.5] * 12  # ~135° Position (rechts)
            self.save_config()
    
    def save_config(self):
        """Speichere Servo-Konfiguration in config.json"""
        config = {
            'servo_pins': self.servo_pins,
            'servo_left_angles': self.servo_left_angles,
            'servo_right_angles': self.servo_right_angles
        }
        with open('src/config.json', 'w') as f:
            json.dump(config, f, indent=4)
    
    def setup_servos(self):
        """Initialisiere alle Servo-Pins"""
        self.servos = []
        for pin in self.servo_pins:
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, 50)  # 50Hz Frequenz
            pwm.start(0)
            self.servos.append(pwm)
    
    def set_servo_position(self, servo_id, position):
        """Setze Position eines Servos"""
        if 0 <= servo_id < len(self.servos):
            # MG90S benötigt eine sanfte Bewegung
            angle = self.servo_left_angles[servo_id] if position == 'left' else self.servo_right_angles[servo_id]
            
            # Aktiviere PWM
            self.servos[servo_id].ChangeDutyCycle(angle)
            
            # Warte bis Servo Position erreicht hat (MG90S braucht ~0.1s/60°)
            time.sleep(0.3)
            
            # Stoppe PWM um Zittern zu vermeiden
            self.servos[servo_id].ChangeDutyCycle(0)
            
            # Aktualisiere Status
            self.servo_states[servo_id]['position'] = position
    
    def get_servo_position(self, servo_id):
        """Gibt die aktuelle Position eines Servos zurück"""
        if 0 <= servo_id < len(self.servos):
            return self.servo_states[servo_id]['position']
        return None
    
    def get_servo_states(self):
        """Gibt den Status aller Servos zurück"""
        return self.servo_states
    
    def set_sensor_status(self, servo_id, status):
        """Setze den Status des Hall-Sensors für einen Servo"""
        if 0 <= servo_id < len(self.servos):
            self.servo_states[servo_id]['sensor_ok'] = status
    
    def cleanup(self):
        """Aufräumen beim Beenden"""
        for servo in self.servos:
            servo.stop()
        GPIO.cleanup()
