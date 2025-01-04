import RPi.GPIO as GPIO
import time

class HallSensor:
    def __init__(self):
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Standard-Pins für Hall-Sensoren
        self.sensor_pins = [26, 16, 20, 21]  # Beispiel-Pins, anpassen nach Bedarf
        self.setup_sensors()
        
        # Status-Dictionary für alle Sensoren
        self.sensor_states = {}
        for pin in self.sensor_pins:
            self.sensor_states[pin] = False
    
    def setup_sensors(self):
        """Initialisiere alle Hall-Sensor-Pins"""
        for pin in self.sensor_pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    def read_sensor(self, pin):
        """Lese den Status eines einzelnen Sensors"""
        if pin in self.sensor_pins:
            # Hall-Sensor gibt LOW wenn Magnet erkannt wird
            state = not GPIO.input(pin)
            self.sensor_states[pin] = state
            return state
        return False
    
    def read_all_sensors(self):
        """Lese den Status aller Sensoren"""
        for pin in self.sensor_pins:
            self.read_sensor(pin)
        return self.sensor_states
    
    def get_sensor_state(self, pin):
        """Gibt den letzten bekannten Status eines Sensors zurück"""
        return self.sensor_states.get(pin, False)
    
    def get_all_states(self):
        """Gibt den Status aller Sensoren zurück"""
        return self.sensor_states
    
    def cleanup(self):
        """Aufräumen beim Beenden"""
        # GPIO.cleanup() wird nicht hier aufgerufen, da es die Servo-Pins beeinflussen würde
        pass
