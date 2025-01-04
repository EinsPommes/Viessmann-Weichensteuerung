import tkinter as tk
from tkinter import ttk
import time
from track_layout import TrackLayout

class GUI:
    def __init__(self, root, servo_controller, automation_controller):
        self.root = root
        self.servo_controller = servo_controller
        self.automation_controller = automation_controller
        
        self.root.title("Viessmann Weichensteuerung")
        
        # Bildschirmgröße ermitteln und Fenstergröße anpassen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Für 10 Zoll Display optimierte Größe (1280x800)
        window_width = min(1280, screen_width)
        window_height = min(800, screen_height)
        
        # Fenster zentrieren
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Stil konfigurieren für bessere Touch-Bedienung
        self.style = ttk.Style()
        self.style.configure('Title.TLabel', font=('Helvetica', 28, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Helvetica', 18))
        self.style.configure('Switch.TFrame', padding=8)
        self.style.configure('Switch.TLabel', font=('Helvetica', 14))
        self.style.configure('TButton', padding=5)
        
        # Hauptcontainer mit zwei Spalten
        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky="nsew")
        
        # Linke Spalte für Steuerung
        control_frame = ttk.Frame(main_container)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=(0,15))
        
        # Rechte Spalte für Streckenlayout
        layout_frame = ttk.LabelFrame(main_container, text="Streckenübersicht")
        layout_frame.grid(row=0, column=1, sticky="nsew", padx=(15,0))
        
        # Canvas für Streckenlayout
        self.canvas = tk.Canvas(layout_frame, width=800, height=500, bg='white')
        self.canvas.pack(padx=10, pady=10)
        
        # Streckenlayout initialisieren
        self.track_layout = TrackLayout(self.canvas.winfo_width(), self.canvas.winfo_height())
        
        # GUI-Elemente erstellen
        self._create_control_elements(control_frame)
        
        # Status aktualisieren
        self.update_switch_status()
        
    def _create_control_elements(self, parent):
        """Erstellt die Steuerungselemente"""
        # Titel
        title = ttk.Label(parent, text="Viessmann Weichensteuerung", 
                         style='Title.TLabel')
        title.grid(row=0, column=0, columnspan=4, pady=(0,10))
        
        # Untertitel
        subtitle = ttk.Label(parent, text="Systemstatus und Kontrolle",
                           style='Subtitle.TLabel')
        subtitle.grid(row=1, column=0, columnspan=4, pady=(0,25))
        
        # Automatik-Frame
        auto_frame = ttk.LabelFrame(parent, text="Automatik-Modus", padding=15)
        auto_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=(0,25))
        
        # Modus-Auswahl
        ttk.Label(auto_frame, text="Modus:", font=('Helvetica', 14)).grid(row=0, column=0, padx=(0,15))
        
        self.mode_var = tk.StringVar(value="sequence")
        modes = [("Sequentiell", "sequence"), 
                ("Zufällig", "random"), 
                ("Muster", "pattern")]
        
        for idx, (text, mode) in enumerate(modes):
            rb = ttk.Radiobutton(auto_frame, text=text, value=mode,
                               variable=self.mode_var)
            rb.grid(row=0, column=idx+1, padx=15)
        
        # Start/Stop Buttons
        button_frame = ttk.Frame(auto_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(15,0))
        
        ttk.Button(button_frame, text="Start", 
                  command=self.start_automation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop", 
                  command=self.stop_automation).pack(side=tk.LEFT, padx=5)
        
        # Weichen testen
        test_frame = ttk.LabelFrame(parent, text="Weichen testen", padding=15)
        test_frame.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=(0,25))
        
        ttk.Button(test_frame, text="Alle Weichen testen",
                  command=self.test_switches).pack(expand=True)
        
        # Status-Anzeige
        self.status_label = ttk.Label(parent, text="Bereit")
        self.status_label.grid(row=4, column=0, columnspan=4, pady=5)
        
        # Grid-Konfiguration
        parent.grid_columnconfigure(0, weight=1)
    
    def update_switch_status(self):
        """Aktualisiert den Status aller Weichen"""
        switch_states = {}
        for i in range(12):
            position = self.servo_controller.get_servo_position(i)
            switch_states[i+1] = {
                'position': position,
                'sensor_ok': True  # Temporär immer True
            }
        
        # Layout aktualisieren
        self.track_layout.draw(self.canvas, switch_states)
        
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
