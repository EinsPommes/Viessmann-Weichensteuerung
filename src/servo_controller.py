import RPi.GPIO as GPIO
import time
import json
import os

class ServoController:
    def __init__(self, config_file=None):
        # GPIO initialisieren
        GPIO.setmode(GPIO.BCM)
        
        # Servo-Pins (BCM-Nummern)
        self.servo_pins = [15, 18, 27, 22, 23, 24, 25, 4, 5, 6, 13, 19, 26, 16, 20, 21]
        
        # GPIO-Pins als Ausgang konfigurieren
        for pin in self.servo_pins:
            GPIO.setup(pin, GPIO.OUT)
        
        # PWM für jeden Servo initialisieren
        self.pwm = {}
        for pin in self.servo_pins:
            self.pwm[pin] = GPIO.PWM(pin, 50)  # 50 Hz
            self.pwm[pin].start(0)
        
        # Servo-Konfiguration
        self.servo_config = []
        for i in range(16):  # 16 Servos
            servo = {
                'left_angle': 2.5,
                'right_angle': 12.5,
                'speed': 0.2  # Langsamere Standardgeschwindigkeit
            }
            self.servo_config.append(servo)
        
        # Lade Servo-Konfiguration wenn vorhanden
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()
        
        # Status für jeden Servo
        self.servo_states = {}
        for i in range(16):
            self.servo_states[i] = {
                'position': None,  # 'left' oder 'right'
                'current_duty': 0
            }

    def load_config(self):
        """Lädt die Konfiguration aus der config.json"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Initialisiere Servo-Konfiguration
            self.servo_config = []
            for i in range(16):  # 16 Servos
                servo = {
                    'left_angle': 2.5,
                    'right_angle': 12.5,
                    'speed': 0.2  # Langsamere Standardgeschwindigkeit
                }
                self.servo_config.append(servo)
                
            # Lade gespeicherte Konfiguration wenn vorhanden
            if 'SERVOS' in config:
                for servo in config['SERVOS']:
                    if 'id' in servo and 0 <= servo['id'] < 16:
                        self.servo_config[servo['id']].update({
                            'left_angle': float(servo.get('left_angle', 2.5)),
                            'right_angle': float(servo.get('right_angle', 12.5)),
                            'speed': float(servo.get('speed', 0.2))  # Langsamere Standardgeschwindigkeit
                        })
                        
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            # Standardwerte verwenden
            self.servo_config = [
                {'left_angle': 2.5, 'right_angle': 12.5, 'speed': 0.2}  # Langsamere Standardgeschwindigkeit
                for _ in range(16)
            ]

    def save_config(self):
        """Speichert die Konfiguration in config.json"""
        try:
            # Aktuelle Konfiguration lesen
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Servo-Konfiguration aktualisieren
            servos = []
            for i, servo in enumerate(self.servo_config):
                servos.append({
                    'id': i,
                    'gpio': self.servo_pins[i],
                    'left_angle': float(servo['left_angle']),
                    'right_angle': float(servo['right_angle']),
                    'speed': float(servo['speed'])
                })
            
            config['SERVOS'] = servos
            
            # Konfiguration speichern
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            print("Konfiguration erfolgreich gespeichert")
            return True
            
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")
            return False

    def get_servo_config(self, servo_id):
        """Gibt die Konfiguration eines Servos zurück"""
        if servo_id < 0 or servo_id >= len(self.servo_config):
            return {
                'left_angle': 2.5,
                'right_angle': 12.5,
                'speed': 0.2  # Langsamere Standardgeschwindigkeit
            }
        return self.servo_config[servo_id]

    def set_servo_config(self, servo_id, **kwargs):
        """Aktualisiert die Konfiguration eines Servos"""
        if servo_id < 0 or servo_id >= len(self.servo_config):
            return False
            
        # Aktualisiere nur gültige Werte
        if 'left_angle' in kwargs:
            self.servo_config[servo_id]['left_angle'] = float(kwargs['left_angle'])
        if 'right_angle' in kwargs:
            self.servo_config[servo_id]['right_angle'] = float(kwargs['right_angle'])
        if 'speed' in kwargs:
            self.servo_config[servo_id]['speed'] = float(kwargs['speed'])
            
        return True

    def angle_to_duty_cycle(self, angle):
        """
        Konvertiert einen Winkel (0-180 Grad) in einen Duty-Cycle (2.5-12.5)
        
        Args:
            angle (float): Winkel in Grad (0-180)
            
        Returns:
            float: Duty-Cycle (2.5-12.5)
        """
        # Begrenzen des Winkels auf 0-180 Grad
        angle = max(0, min(180, angle))
        
        # Lineare Umrechnung von Grad (0-180) zu Duty-Cycle (2.5-12.5)
        duty_cycle = 2.5 + (angle / 180.0) * 10.0
        return duty_cycle
    
    def duty_to_percent(self, duty):
        """
        Konvertiert einen Duty-Cycle (2.5-12.5) in einen Prozentwert (0-100)
        """
        # Begrenze den Duty-Cycle auf den gültigen Bereich
        duty = max(2.5, min(12.5, duty))
        # Konvertiere zu Prozent
        return duty * 100.0 / 20.0  # 2.5 -> 12.5%, 12.5 -> 62.5%

    def set_servo_position(self, servo_id, position):
        """
        Setzt die Position eines Servos
        
        Args:
            servo_id (int): ID des Servos (0-15)
            position (str): 'left' oder 'right'
        """
        if servo_id >= len(self.servo_pins):
            raise ValueError(f"Ungültige Servo-ID: {servo_id}")
            
        if position not in ['left', 'right']:
            raise ValueError(f"Ungültige Position: {position}")
        
        try:
            pin = self.servo_pins[servo_id]
            config = self.servo_config[servo_id]
            
            # Ziel-Duty-Cycle berechnen
            target_duty = config['left_angle'] if position == 'left' else config['right_angle']
            current_duty = self.servo_states[servo_id]['current_duty']
            
            # Wenn der Servo bereits in der richtigen Position ist, nichts tun
            if self.servo_states[servo_id]['position'] == position:
                return
                
            # Geschwindigkeit in Grad pro Sekunde
            speed = config['speed']
            
            # Berechne die Anzahl der Schritte basierend auf der Geschwindigkeit
            total_steps = 50  # Anzahl der Schritte für die Bewegung
            step_size = (target_duty - current_duty) / total_steps
            step_delay = (1.0 / total_steps) * (1.0 / speed)  # Verzögerung zwischen den Schritten
            
            # Sanft zur Zielposition bewegen
            for step in range(total_steps + 1):
                duty = current_duty + (step * step_size)
                self.pwm[pin].ChangeDutyCycle(duty)
                time.sleep(step_delay)
            
            # Speichere die neue Position
            self.servo_states[servo_id]['position'] = position
            self.servo_states[servo_id]['current_duty'] = target_duty
            
            # Stoppe PWM nach der Bewegung
            self.pwm[pin].ChangeDutyCycle(0)
            
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
        if servo_id >= len(self.servo_pins):
            raise ValueError(f"Ungültige Servo-ID: {servo_id}")
        
        return self.servo_states[servo_id]['position']

    def cleanup(self):
        """Aufräumen beim Beenden"""
        try:
            # Servos auf 0 setzen
            for pin in self.servo_pins:
                if pin in self.pwm:
                    self.pwm[pin].ChangeDutyCycle(0)
                    self.pwm[pin].stop()
            
            # GPIO aufräumen
            GPIO.cleanup()
            
        except Exception as e:
            print(f"Fehler beim Aufräumen: {e}")