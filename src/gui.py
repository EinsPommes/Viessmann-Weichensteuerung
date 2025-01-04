import tkinter as tk
from tkinter import ttk
import time
from track_layout import TrackLayout

class GUI:
    def __init__(self, root, servo_controller, automation_controller):
        self.root = root
        self.servo_controller = servo_controller
        self.automation_controller = automation_controller
        
        self.root.title("Weichensteuerung")
        
        # Canvas für Streckenlayout
        self.canvas = tk.Canvas(root, width=800, height=500, bg='white')
        self.canvas.pack(pady=10)
        
        # Streckenlayout
        self.track_layout = TrackLayout(self.canvas)
        
        # Steuerungsbuttons
        self.control_frame = ttk.Frame(root)
        self.control_frame.pack(pady=10)
        
        ttk.Button(self.control_frame, text="Test Weichen", 
                  command=self.test_switches).pack(side=tk.LEFT, padx=5)
        
        # Automatik-Steuerung
        self.auto_frame = ttk.LabelFrame(root, text="Automatik")
        self.auto_frame.pack(pady=10)
        
        # Modus-Auswahl
        self.mode_var = tk.StringVar(value="sequence")
        modes = [("Sequentiell", "sequence"), 
                ("Zufällig", "random"), 
                ("Muster", "pattern")]
        
        for text, mode in modes:
            ttk.Radiobutton(self.auto_frame, text=text, value=mode, 
                          variable=self.mode_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.auto_frame, text="Start", 
                  command=self.start_automation).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.auto_frame, text="Stop", 
                  command=self.stop_automation).pack(side=tk.LEFT, padx=5)
        
        # Status-Anzeige
        self.status_label = ttk.Label(root, text="Bereit")
        self.status_label.pack(pady=5)
        
        # Weichenstatus aktualisieren
        self.update_switch_status()
    
    def update_switch_status(self):
        """Aktualisiert den Status aller Weichen"""
        for i in range(12):
            position = self.servo_controller.get_servo_position(i)
            
            # Status für Streckenlayout
            switch_status = {
                'position': position,
                'sensor_ok': True  # Temporär immer True
            }
            
            # Layout aktualisieren
            self.track_layout.update_switch(i, switch_status)
        
        # Alle 100ms aktualisieren
        self.root.after(100, self.update_switch_status)
    
    def test_switches(self):
        """Testet alle Weichen"""
        self.status_label.config(text="Teste Weichen...")
        for i in range(12):
            self.servo_controller.set_servo_position(i, 'right')
            time.sleep(0.5)
            self.servo_controller.set_servo_position(i, 'left')
            time.sleep(0.5)
        self.status_label.config(text="Test abgeschlossen")
    
    def start_automation(self):
        """Startet den Automatik-Modus"""
        mode = self.mode_var.get()
        self.automation_controller.start_automation(mode)
        self.status_label.config(text=f"Automatik aktiv ({mode})")
    
    def stop_automation(self):
        """Stoppt den Automatik-Modus"""
        self.automation_controller.stop_automation()
        self.status_label.config(text="Automatik gestoppt")
