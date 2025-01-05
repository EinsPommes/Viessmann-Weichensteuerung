from servo_controller import ServoController
from hall_sensor import HallSensor
from automation_controller import AutomationController
from gui import GUI
from track_map import TrackMap
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
        
        # Fenstergröße für 10 Zoll Monitor (1024x600 typische Auflösung)
        self.root.geometry("1024x600")
        
        # Skalierung für hochauflösende Displays
        self.root.tk.call('tk', 'scaling', 1.5)
        
        # Controller initialisieren
        try:
            self.servo_controller = ServoController()
            self.automation_controller = AutomationController(self.servo_controller)
            self.hall_sensor = HallSensor()
            self.system_status = "Ready"
        except Exception as e:
            self.system_status = f"Error: {str(e)}"
            messagebox.showerror("Fehler", f"Fehler beim Starten: {str(e)}")
            raise
        
        # Hauptframe mit Padding für bessere Lesbarkeit
        main_frame = ttk.Frame(root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grid-Konfiguration für bessere Skalierung
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # Status-Dictionary für Servos
        self.servo_status = {}
        for i in range(16):
            self.servo_status[i] = {
                'frame': None,
                'label': None,
                'position': 'links'
            }
        
        # Tabs erstellen
        self.tab_control = ttk.Notebook(main_frame)
        self.tab_control.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Steuerungs-Tab
        control_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(control_tab, text="Steuerung")
        self.create_control_tab(control_tab)
        
        # Gleiskarte-Tab
        map_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(map_tab, text="Gleiskarte")
        self.create_map_tab(map_tab)
        
        # Kalibrierungs-Tab
        config_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(config_tab, text="Kalibrierung")
        self.create_config_tab(config_tab)
        
        # Automation-Tab
        automation_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(automation_tab, text="Automation")
        self.create_automation_tab(automation_tab)
        
        # Info-Tab
        info_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(info_tab, text="Info & Settings")
        self.create_info_tab(info_tab)
    
    def create_control_tab(self, parent):
        # Frame für Servo-Grid
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grid für Servo-Steuerung (4x4 Grid)
        for i in range(16):
            row = i // 4
            col = i % 4
            
            # Frame für jeden Servo mit angepasster Größe
            servo_frame = ttk.LabelFrame(control_frame, text=f"Servo {i+1}", padding="3")
            servo_frame.grid(row=row, column=col, padx=3, pady=3, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Grid-Konfiguration für gleichmäßige Größe
            control_frame.grid_rowconfigure(row, weight=1)
            control_frame.grid_columnconfigure(col, weight=1)
            
            # Status-Label mit größerer Schrift
            status_label = ttk.Label(servo_frame, text="Position: Links", font=('TkDefaultFont', 9))
            status_label.grid(row=0, column=0, columnspan=2, pady=2)
            
            # Buttons mit angepasster Größe
            btn_left = ttk.Button(servo_frame, text="Links", width=8,
                                command=lambda x=i: self.set_servo_position(x, 'left'))
            btn_left.grid(row=1, column=0, padx=2, pady=2)
            
            btn_right = ttk.Button(servo_frame, text="Rechts", width=8,
                                 command=lambda x=i: self.set_servo_position(x, 'right'))
            btn_right.grid(row=1, column=1, padx=2, pady=2)
            
            # Speichere Frame und Label
            self.servo_status[i]['frame'] = servo_frame
            self.servo_status[i]['label'] = status_label
    
    def create_map_tab(self, parent):
        # Gleiskarte erstellen
        self.track_map = TrackMap(parent)
        
    def create_config_tab(self, parent):
        # Hauptframe mit Padding
        config_main = ttk.Frame(parent, padding="5")
        config_main.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Servo-Auswahl mit größerer Schrift
        ttk.Label(config_main, text="Servo auswählen:", font=('TkDefaultFont', 10)).grid(row=0, column=0, padx=5, pady=5)
        self.selected_servo = tk.StringVar()
        servo_select = ttk.Combobox(config_main, textvariable=self.selected_servo, font=('TkDefaultFont', 10), width=15)
        servo_select['values'] = [f"Servo {i+1}" for i in range(16)]
        servo_select.grid(row=0, column=1, padx=5, pady=5)
        servo_select.bind('<<ComboboxSelected>>', self.on_servo_selected)
        
        # Konfigurationsframe
        config_frame = ttk.LabelFrame(config_main, text="Servo-Konfiguration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Position A (Links)
        ttk.Label(config_frame, text="Position A (Links):", font=('TkDefaultFont', 10)).grid(row=0, column=0, padx=5, pady=5)
        self.left_angle = tk.StringVar()
        self.left_scale = ttk.Scale(config_frame, from_=2.5, to=12.5, orient=tk.HORIZONTAL,
                                  variable=self.left_angle, command=self.update_left_angle, length=200)
        self.left_scale.grid(row=0, column=1, padx=5, pady=5)
        
        # Position B (Rechts)
        ttk.Label(config_frame, text="Position B (Rechts):", font=('TkDefaultFont', 10)).grid(row=1, column=0, padx=5, pady=5)
        self.right_angle = tk.StringVar()
        self.right_scale = ttk.Scale(config_frame, from_=2.5, to=12.5, orient=tk.HORIZONTAL,
                                   variable=self.right_angle, command=self.update_right_angle, length=200)
        self.right_scale.grid(row=1, column=1, padx=5, pady=5)
        
        # Geschwindigkeit
        ttk.Label(config_frame, text="Geschwindigkeit:", font=('TkDefaultFont', 10)).grid(row=2, column=0, padx=5, pady=5)
        self.speed = tk.StringVar()
        self.speed_scale = ttk.Scale(config_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL,
                                   variable=self.speed, command=self.update_speed, length=200)
        self.speed_scale.grid(row=2, column=1, padx=5, pady=5)
        
        # Test-Buttons
        test_frame = ttk.LabelFrame(config_main, text="Test", padding="5")
        test_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(test_frame, text="Test Position A", width=15,
                  command=lambda: self.test_position('left')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(test_frame, text="Test Position B", width=15,
                  command=lambda: self.test_position('right')).grid(row=0, column=1, padx=5, pady=5)
    
    def create_automation_tab(self, parent):
        # Hauptframe mit Padding
        auto_main = ttk.Frame(parent, padding="5")
        auto_main.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Pattern-Auswahl
        pattern_frame = ttk.LabelFrame(auto_main, text="Automatik-Muster", padding="10")
        pattern_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Muster-Liste mit größerer Schrift
        patterns = [
            "Muster 1: Links → Rechts",
            "Muster 2: Rechts → Links",
            "Muster 3: Alternierend",
            "Muster 4: Zufällig",
            "Muster 5: Welle",
            "Muster 6: Kreuz"
        ]
        
        self.selected_pattern = tk.StringVar()
        pattern_list = ttk.Combobox(pattern_frame, textvariable=self.selected_pattern,
                                  font=('TkDefaultFont', 10), width=30)
        pattern_list['values'] = patterns
        pattern_list.set(patterns[0])
        pattern_list.grid(row=0, column=0, padx=5, pady=5)
        
        # Geschwindigkeit
        speed_frame = ttk.LabelFrame(pattern_frame, text="Geschwindigkeit", padding="5")
        speed_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.automation_speed = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL,
                              variable=self.automation_speed, length=300)
        speed_scale.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Start/Stop Buttons mit größerer Breite
        control_frame = ttk.Frame(auto_main)
        control_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(control_frame, text="Start", width=20,
                  command=self.start_automation).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="Stop", width=20,
                  command=self.stop_automation).grid(row=0, column=1, padx=5, pady=5)
    
    def create_info_tab(self, parent):
        # Info Frame
        info_frame = ttk.LabelFrame(parent, text="System Information", padding="10")
        info_frame.grid(row=0, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        # System Status
        status_frame = ttk.Frame(info_frame)
        status_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(status_frame, text="System Status:", 
                 font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, padx=5)
        
        status_label = ttk.Label(status_frame, 
                               text=self.system_status,
                               font=('TkDefaultFont', 10))
        status_label.grid(row=0, column=1, padx=5)
        
        # Credits
        credits_frame = ttk.LabelFrame(parent, text="Credits", padding="10")
        credits_frame.grid(row=1, column=0, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(credits_frame, 
                 text="Entwickelt von EinsPommesx\nWebsite: Chill-zone.xyz",
                 font=('TkDefaultFont', 10)).grid(row=0, column=0, padx=5, pady=5)
        
        # Beenden Button
        ttk.Button(parent, text="Beenden", 
                  command=self.quit_application,
                  width=20).grid(row=2, column=0, pady=20)
    
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
            label = self.servo_status[servo_id]['label']
            if label:
                label.configure(text=f"Position: {'Links' if position == 'left' else 'Rechts'}")
            self.servo_status[servo_id]['position'] = position
            
            # Aktualisiere Gleiskarte
            self.track_map.update_switch(servo_id + 1, position)
            
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
            
    def quit_application(self):
        """Beendet die Anwendung sauber"""
        try:
            self.servo_controller.cleanup()
        except:
            pass
        self.root.quit()
        
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
