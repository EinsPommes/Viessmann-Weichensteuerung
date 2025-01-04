import tkinter as tk
from tkinter import ttk
import json
from track_layout import TrackLayout

class GUI:
    def __init__(self, servo_controller, automation_controller):
        self.servo_controller = servo_controller
        # self.hall_controller = hall_controller
        self.automation_controller = automation_controller
        
        self.root = tk.Tk()
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
        
        # Vollbildmodus für Touch-Display
        self.root.attributes('-fullscreen', True)
        
        # Stil konfigurieren für bessere Touch-Bedienung
        self.style = ttk.Style()
        self.style.configure('Title.TLabel', font=('Helvetica', 28, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Helvetica', 18))
        self.style.configure('Switch.TFrame', padding=8)
        self.style.configure('Switch.TLabel', font=('Helvetica', 14))
        self.style.configure('TButton', padding=5)  # Größere Buttons für Touch
        
        self.switches = []
        
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
        self.track_canvas = tk.Canvas(layout_frame, width=800, height=500,
                                    bg='white')
        self.track_canvas.pack(padx=10, pady=10)
        
        # Streckenlayout initialisieren
        self.track_layout = TrackLayout()
        
        # GUI-Elemente in der linken Spalte erstellen
        self._create_control_elements(control_frame)
        
        self.update_status()
        
    def _create_control_elements(self, parent):
        """Erstellt die Steuerungselemente in der linken Spalte"""
        # Titel
        title = ttk.Label(parent, text="Viessmann Weichensteuerung", 
                         style='Title.TLabel')
        title.grid(row=0, column=0, columnspan=4, pady=(0,10))
        
        subtitle = ttk.Label(parent, text="Systemstatus und Kontrolle",
                           style='Subtitle.TLabel')
        subtitle.grid(row=1, column=0, columnspan=4, pady=(0,25))
        
        # Automatik-Modus Frame
        auto_frame = ttk.LabelFrame(parent, text="Automatik-Modus", padding=15)
        auto_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=(0,25))
        
        # Modus-Auswahl mit größeren Buttons
        ttk.Label(auto_frame, text="Modus:", font=('Helvetica', 14)).grid(row=0, column=0, padx=(0,15))
        
        self.mode_var = tk.StringVar(value="sequence")
        modes = [("Sequenziell", "sequence"), ("Zufällig", "random"), ("Muster", "pattern")]
        
        for idx, (text, mode) in enumerate(modes):
            rb = ttk.Radiobutton(auto_frame, text=text, value=mode,
                               variable=self.mode_var, style='TRadiobutton')
            rb.grid(row=0, column=idx+1, padx=15)
        
        # Start/Stop Buttons
        button_frame = ttk.Frame(auto_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=(15,0))
        
        self.start_btn = ttk.Button(button_frame, text="Start Automatik",
                                  command=self._start_automation, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Automatik",
                                 command=self._stop_automation, state=tk.DISABLED, width=15)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Legende mit größerer Schrift
        legend_frame = ttk.Frame(parent)
        legend_frame.grid(row=3, column=0, columnspan=4, pady=(0,15))
        
        ttk.Label(legend_frame, text="Position korrekt", foreground='green',
                 font=('Helvetica', 12)).pack(side=tk.LEFT, padx=(0,30))
        ttk.Label(legend_frame, text="Position fehlerhaft", foreground='red',
                 font=('Helvetica', 12)).pack(side=tk.LEFT)
        
        # Weichen-Grid mit mehr Platz
        switches_frame = ttk.Frame(parent)
        switches_frame.grid(row=4, column=0, columnspan=4)
        
        # Erstelle 4x4 Grid von Weichen
        for i in range(16):
            row = i // 4
            col = i % 4
            
            switch_frame = ttk.Frame(switches_frame, style='Switch.TFrame')
            switch_frame.grid(row=row, column=col, padx=8, pady=8)
            
            # Weichennummer und Position
            header_frame = ttk.Frame(switch_frame)
            header_frame.pack(fill=tk.X)
            
            ttk.Label(header_frame, text=f"Weiche {i+1}",
                     style='Switch.TLabel').pack(side=tk.LEFT)
            
            pos_var = tk.StringVar(value="Links")
            pos_label = ttk.Label(header_frame, textvariable=pos_var,
                                style='Switch.TLabel')
            pos_label.pack(side=tk.RIGHT)
            
            # Größere Steuerungsbuttons für Touch
            btn_frame = ttk.Frame(switch_frame)
            btn_frame.pack(pady=5)
            
            left_btn = ttk.Button(btn_frame, text="◄", width=4,
                                command=lambda x=i: self.set_switch(x, "left"))
            left_btn.pack(side=tk.LEFT, padx=2)
            
            right_btn = ttk.Button(btn_frame, text="►", width=4,
                                 command=lambda x=i: self.set_switch(x, "right"))
            right_btn.pack(side=tk.LEFT, padx=2)
            
            # Größerer Test-Button
            test_btn = ttk.Button(switch_frame, text="Test", width=8,
                                command=lambda x=i: self.test_switch(x))
            test_btn.pack(pady=5)
            
            self.switches.append({
                'frame': switch_frame,
                'pos_var': pos_var,
                'pos_label': pos_label,
                'left_btn': left_btn,
                'right_btn': right_btn,
                'test_btn': test_btn
            })
        
        # Credits am unteren Rand
        credits_frame = ttk.Frame(parent)
        credits_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(25,10))
        
        # ESC zum Beenden
        exit_btn = ttk.Button(credits_frame, text="✕ Beenden", 
                            command=self.root.destroy, width=10)
        exit_btn.pack(side=tk.LEFT, padx=5)
        
        credits_text = ttk.Label(credits_frame, 
                               text="Developed by EinsPommes × chill-zone.xyz",
                               font=('Helvetica', 10),
                               foreground='gray')
        credits_text.pack(side=tk.RIGHT, padx=5)
        
        # Grid-Konfiguration
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Tastenkombination zum Beenden
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
    def _start_automation(self):
        mode = self.mode_var.get()
        self.automation_controller.start_automation(mode)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._set_switch_controls_state(tk.DISABLED)
        
    def _stop_automation(self):
        self.automation_controller.stop_automation()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._set_switch_controls_state(tk.NORMAL)
        
    def _set_switch_controls_state(self, state):
        for switch in self.switches:
            switch['left_btn'].config(state=state)
            switch['right_btn'].config(state=state)
            switch['test_btn'].config(state=state)
    
    def set_switch(self, switch_num, position):
        self.servo_controller.set_position(switch_num, position)
        self.update_status()
        
    def test_switch(self, switch_num):
        self.servo_controller.test_servo(switch_num)
        self.update_status()
        
    def update_status(self):
        """Aktualisiert den Status aller Weichen und das Streckenlayout"""
        switch_states = {}
        
        for i in range(16):
            pos = self.servo_controller.get_position(i)
            # sensor_state = self.hall_controller.get_sensor_state(i)
            
            # Position aktualisieren
            self.switches[i]['pos_var'].set("Links" if pos == "left" else "Rechts")
            
            # Farbe basierend auf Sensor-Status
            color = 'green'  # if sensor_state else 'red'
            self.switches[i]['pos_label'].configure(foreground=color)
            
            # Status für Streckenlayout speichern
            switch_states[i] = {
                'position': pos,
                'sensor_ok': True  # sensor_state
            }
        
        # Streckenlayout aktualisieren
        self.track_layout.draw(self.track_canvas, switch_states)
        
        # Nach 100ms erneut aktualisieren
        self.root.after(100, self.update_status)
        
    def run(self):
        self.root.mainloop()
