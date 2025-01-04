from servo_controller import ServoController
from hall_sensor import HallSensor
from automation_controller import AutomationController
from gui import GUI
import json
import os
import tkinter as tk

# Konfigurationswerte
CONFIG = {
    # GPIO-Pins für die Hall-Sensoren (BCM-Nummerierung)
    'HALL_SENSOR_PINS': [17, 18, 27, 22, 23, 24, 25, 4,
                        5, 6, 12, 13, 16, 19, 20, 21],
    
    # Servo-Kalibrierungswerte
    'SERVO_CONFIG': {
        'LEFT_ANGLE': 0,    # Minimaler Winkel
        'RIGHT_ANGLE': 180, # Maximaler Winkel
        'MIN_PULSE': 500,   # Minimale Pulsweite (µs)
        'MAX_PULSE': 2500   # Maximale Pulsweite (µs)
    },
    
    # I2C-Konfiguration
    'I2C_ADDRESS': 0x40,    # Standard-Adresse des PCA9685
}

def load_config():
    """Lädt die Konfiguration aus config.json wenn vorhanden"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
            CONFIG.update(loaded_config)

def save_config():
    """Speichert die aktuelle Konfiguration"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'w') as f:
        json.dump(CONFIG, f, indent=4)

def main():
    try:
        # Initialisiere Servo-Controller
        servo_controller = ServoController()
        
        # Initialisiere Hall-Sensor-Controller
        hall_sensor = HallSensor()
        
        # Initialisiere Automatik-Controller
        automation = AutomationController(servo_controller)
        
        # Starte GUI
        root = tk.Tk()
        app = GUI(root, servo_controller, hall_sensor, automation)
        root.protocol("WM_DELETE_WINDOW", lambda: cleanup(root, servo_controller))
        root.mainloop()
    except Exception as e:
        print(f"Fehler beim Starten: {e}")
        
def cleanup(root, servo_controller):
    """Aufräumen beim Beenden"""
    print("Beende Programm...")
    servo_controller.cleanup()
    root.destroy()

if __name__ == "__main__":
    main()
