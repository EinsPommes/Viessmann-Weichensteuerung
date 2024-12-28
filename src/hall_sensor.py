# import RPi.GPIO as GPIO
import time
from threading import Thread, Lock

class HallSensorController:
    def __init__(self, sensor_pins):
        """
        Initialisiert den Hall-Sensor-Controller
        
        Args:
            sensor_pins (list): Liste der GPIO-Pins für die Hall-Sensoren
        """
        self.sensor_pins = sensor_pins
        self.sensor_states = [False] * len(sensor_pins)
        self.state_lock = Lock()
        # self._setup_gpio()
        self._start_monitoring()
        
    def _setup_gpio(self):
        """Konfiguriert die GPIO-Pins für die Hall-Sensoren"""
        # GPIO.setmode(GPIO.BCM)
        # for pin in self.sensor_pins:
        #     GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pass
            
    def _monitor_sensors(self):
        """Überwacht kontinuierlich die Hall-Sensoren"""
        while True:
            for i, pin in enumerate(self.sensor_pins):
                # state = not GPIO.input(pin)  # Invertiert, da Hall-Sensor LOW bei Magnet
                # Simuliere zufällige Sensorwerte für Test
                state = True  # Alle Sensoren zeigen "korrekte Position"
                with self.state_lock:
                    self.sensor_states[i] = state
            time.sleep(0.1)  # Kleine Pause zwischen den Messungen
            
    def _start_monitoring(self):
        """Startet den Überwachungs-Thread"""
        self.monitor_thread = Thread(target=self._monitor_sensors, daemon=True)
        self.monitor_thread.start()
        
    def get_sensor_state(self, sensor_num):
        """
        Gibt den Status eines bestimmten Sensors zurück
        
        Args:
            sensor_num (int): Nummer des Sensors (0-15)
            
        Returns:
            bool: True wenn Magnet erkannt, False wenn nicht
        """
        if sensor_num < 0 or sensor_num >= len(self.sensor_pins):
            raise ValueError(f"Ungültige Sensor-Nummer: {sensor_num}")
            
        with self.state_lock:
            return self.sensor_states[sensor_num]
            
    def get_all_states(self):
        """
        Gibt den Status aller Sensoren zurück
        
        Returns:
            list: Liste der Sensor-Zustände
        """
        with self.state_lock:
            return self.sensor_states.copy()
            
    def cleanup(self):
        """Aufräumen der GPIO-Ressourcen"""
        # GPIO.cleanup()
        pass
