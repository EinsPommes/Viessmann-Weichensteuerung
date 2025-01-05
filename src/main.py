from servo_controller import ServoController
from hall_sensor import HallSensor
from automation_controller import AutomationController
from gui import GUI
import json
import os
import tkinter as tk
import sys

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

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from servo_controller import ServoController
from automation_controller import AutomationController
from hall_sensor import HallSensor

class WeichensteuerungGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Weichensteuerung")
        
        # Controller initialisieren
        try:
            self.servo_controller = ServoController()
            self.automation_controller = AutomationController(self.servo_controller)
            self.hall_sensor = HallSensor()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Starten: {str(e)}")
            raise
        
        # Hauptframe
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status-Dictionary für Servos
        self.servo_labels = {}
        
        # Tabs erstellen
        self.tab_control = ttk.Notebook(main_frame)
        self.tab_control.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Steuerungs-Tab
        control_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(control_tab, text="Steuerung")
        self.create_control_tab(control_tab)
        
        # Kalibrierungs-Tab
        config_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(config_tab, text="Kalibrierung")
        self.create_config_tab(config_tab)
        
        # Automation-Tab
        automation_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(automation_tab, text="Automation")
        self.create_automation_tab(automation_tab)
    
    def create_control_tab(self, parent):
        # Grid für Servo-Steuerung
        for i in range(16):
            row = i // 4
            col = i % 4
            
            # Frame für jeden Servo
            servo_frame = ttk.LabelFrame(parent, text=f"Servo {i+1}", padding="5")
            servo_frame.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Status-Label
            status_label = ttk.Label(servo_frame, text="Position: Links")
            status_label.grid(row=0, column=0, columnspan=2)
            
            # Speichere Label für Updates
            self.servo_labels[i] = status_label
            
            # Buttons
            ttk.Button(servo_frame, text="Links", 
                      command=lambda x=i: self.set_servo_position(x, 'left')).grid(row=1, column=0)
            ttk.Button(servo_frame, text="Rechts", 
                      command=lambda x=i: self.set_servo_position(x, 'right')).grid(row=1, column=1)
    
    def create_config_tab(self, parent):
        # Servo-Auswahl
        ttk.Label(parent, text="Servo auswählen:").grid(row=0, column=0, padx=5, pady=5)
        self.selected_servo = tk.StringVar()
        servo_select = ttk.Combobox(parent, textvariable=self.selected_servo)
        servo_select['values'] = [f"Servo {i+1}" for i in range(16)]
        servo_select.grid(row=0, column=1, padx=5, pady=5)
        servo_select.bind('<<ComboboxSelected>>', self.on_servo_selected)
        
        # Konfigurationsframe
        config_frame = ttk.LabelFrame(parent, text="Servo-Konfiguration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Position A (Links)
        ttk.Label(config_frame, text="Position A (Links):").grid(row=0, column=0, padx=5, pady=5)
        self.left_angle = tk.StringVar()
        self.left_scale = ttk.Scale(config_frame, from_=2.5, to=12.5, orient=tk.HORIZONTAL, 
                                  variable=self.left_angle, command=self.update_left_angle)
        self.left_scale.grid(row=0, column=1, padx=5, pady=5)
        
        # Position B (Rechts)
        ttk.Label(config_frame, text="Position B (Rechts):").grid(row=1, column=0, padx=5, pady=5)
        self.right_angle = tk.StringVar()
        self.right_scale = ttk.Scale(config_frame, from_=2.5, to=12.5, orient=tk.HORIZONTAL, 
                                   variable=self.right_angle, command=self.update_right_angle)
        self.right_scale.grid(row=1, column=1, padx=5, pady=5)
        
        # Geschwindigkeit
        ttk.Label(config_frame, text="Geschwindigkeit:").grid(row=2, column=0, padx=5, pady=5)
        self.speed = tk.StringVar()
        self.speed_scale = ttk.Scale(config_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL, 
                                   variable=self.speed, command=self.update_speed)
        self.speed_scale.grid(row=2, column=1, padx=5, pady=5)
        
        # Test-Buttons
        test_frame = ttk.LabelFrame(parent, text="Test", padding="10")
        test_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(test_frame, text="Test Position A", 
                  command=lambda: self.test_position('left')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(test_frame, text="Test Position B", 
                  command=lambda: self.test_position('right')).grid(row=0, column=1, padx=5, pady=5)
    
    def create_automation_tab(self, parent):
        # Pattern-Auswahl
        pattern_frame = ttk.LabelFrame(parent, text="Automatik-Muster", padding="10")
        pattern_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Muster-Liste
        patterns = [
            "Muster 1: Links → Rechts",
            "Muster 2: Rechts → Links",
            "Muster 3: Alternierend",
            "Muster 4: Zufällig",
            "Muster 5: Welle",
            "Muster 6: Kreuz"
        ]
        
        self.selected_pattern = tk.StringVar()
        pattern_list = ttk.Combobox(pattern_frame, textvariable=self.selected_pattern)
        pattern_list['values'] = patterns
        pattern_list.set(patterns[0])
        pattern_list.grid(row=0, column=0, padx=5, pady=5)
        
        # Geschwindigkeit
        speed_frame = ttk.LabelFrame(pattern_frame, text="Geschwindigkeit", padding="5")
        speed_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.automation_speed = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL,
                              variable=self.automation_speed)
        speed_scale.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Start/Stop Buttons
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(control_frame, text="Start", 
                  command=self.start_automation).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="Stop", 
                  command=self.stop_automation).grid(row=0, column=1, padx=5, pady=5)
    
    def on_servo_selected(self, event):
        if not self.selected_servo.get():
            return
            
        servo_id = int(self.selected_servo.get().split()[1]) - 1
        config = self.servo_controller.get_servo_config(servo_id)
        
        self.left_scale.set(config['left_angle'])
        self.right_scale.set(config['right_angle'])
        self.speed_scale.set(config['speed'])
    
    def update_left_angle(self, value):
        if not self.selected_servo.get():
            return
            
        servo_id = int(self.selected_servo.get().split()[1]) - 1
        self.servo_controller.set_servo_config(servo_id, left_angle=float(value))
    
    def update_right_angle(self, value):
        if not self.selected_servo.get():
            return
            
        servo_id = int(self.selected_servo.get().split()[1]) - 1
        self.servo_controller.set_servo_config(servo_id, right_angle=float(value))
    
    def update_speed(self, value):
        if not self.selected_servo.get():
            return
            
        servo_id = int(self.selected_servo.get().split()[1]) - 1
        self.servo_controller.set_servo_config(servo_id, speed=float(value))
    
    def test_position(self, position):
        if not self.selected_servo.get():
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst einen Servo aus.")
            return
            
        servo_id = int(self.selected_servo.get().split()[1]) - 1
        try:
            self.servo_controller.set_servo_position(servo_id, position)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Testen: {str(e)}")
    
    def set_servo_position(self, servo_id, position):
        try:
            self.servo_controller.set_servo_position(servo_id, position)
            # Aktualisiere Status-Label
            if servo_id in self.servo_labels:
                self.servo_labels[servo_id].configure(text=f"Position: {'Links' if position == 'left' else 'Rechts'}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Setzen der Position: {str(e)}")
    
    def start_automation(self):
        try:
            pattern = self.selected_pattern.get().split(':')[0].strip()
            speed = self.automation_speed.get()
            self.automation_controller.set_pattern(pattern)
            self.automation_controller.set_speed(speed)
            self.automation_controller.start()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Starten der Automation: {str(e)}")
    
    def stop_automation(self):
        try:
            self.automation_controller.stop()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Stoppen der Automation: {str(e)}")

def main():
    try:
        root = tk.Tk()
        app = WeichensteuerungGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Starten: {str(e)}")
        raise

if __name__ == "__main__":
    main()
