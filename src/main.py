from servo_controller import ServoController
from hall_sensor import HallSensorController
from automation_controller import AutomationController
from gui import WeichenGUI
import json
import os

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
        # Konfiguration laden
        load_config()
        
        # Servo-Controller initialisieren
        servo_controller = ServoController(
            num_servos=16,
            pca_address=CONFIG['I2C_ADDRESS']
        )
        
        # Servo-Kalibrierungswerte setzen
        servo_controller.LEFT_ANGLE = CONFIG['SERVO_CONFIG']['LEFT_ANGLE']
        servo_controller.RIGHT_ANGLE = CONFIG['SERVO_CONFIG']['RIGHT_ANGLE']
        
        # Hall-Sensor-Controller initialisieren
        hall_controller = HallSensorController(CONFIG['HALL_SENSOR_PINS'])
        
        # Automatik-Controller initialisieren
        automation_controller = AutomationController(servo_controller)
        
        # GUI starten
        gui = WeichenGUI(servo_controller, hall_controller, automation_controller)
        gui.run()
        
    except KeyboardInterrupt:
        print("\nProgramm wird beendet...")
    finally:
        # Aufräumen
        if 'automation_controller' in locals():
            automation_controller.stop_automation()
        if 'hall_controller' in locals():
            hall_controller.cleanup()
        # Konfiguration speichern
        save_config()

if __name__ == "__main__":
    main()
