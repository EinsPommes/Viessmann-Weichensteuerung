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
        
        # Vollbildmodus für 10 Zoll Display
        self.root.attributes('-fullscreen', True)
        
        # Stil für Touch-Display optimieren
        self.style = ttk.Style()
        self.style.configure('TButton', padding=5)  # Größere Buttons
        self.style.configure('TRadiobutton', padding=5)  # Größere Radiobuttons
        
        # Hauptcontainer
        main_container = ttk.Frame(self.root)
        main_container.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Linke Spalte
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 5))
        
        # Titel
        title = ttk.Label(left_frame, text="Viessmann Weichensteuerung",
                         font=('Helvetica', 20, 'bold'))
        title.pack(anchor='w', pady=(0, 2))
        
        subtitle = ttk.Label(left_frame, text="Systemstatus und Kontrolle",
                           font=('Helvetica', 12))
        subtitle.pack(anchor='w', pady=(0, 10))
        
        # Automatik-Modus Frame
        auto_frame = ttk.LabelFrame(left_frame, text="Automatik-Modus")
        auto_frame.pack(fill='x', pady=(0, 10))
        
        # Modus-Auswahl
        mode_frame = ttk.Frame(auto_frame)
        mode_frame.pack(padx=5, pady=2)
        
        ttk.Label(mode_frame, text="Modus:", 
                 font=('Helvetica', 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.mode_var = tk.StringVar(value="sequence")
        ttk.Radiobutton(mode_frame, text="Sequentiell", value="sequence",
                       variable=self.mode_var).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Zufällig", value="random",
                       variable=self.mode_var).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="Muster", value="pattern",
                       variable=self.mode_var).pack(side=tk.LEFT)
        
        # Start/Stop Buttons
        button_frame = ttk.Frame(auto_frame)
        button_frame.pack(padx=5, pady=2)
        
        ttk.Button(button_frame, text="Start Automatik",
                  command=self.start_automation).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Stop Automatik",
                  command=self.stop_automation).pack(side=tk.LEFT, padx=2)
        
        # Legende
        legend_frame = ttk.Frame(left_frame)
        legend_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(legend_frame, text="Position korrekt",
                 foreground='green').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(legend_frame, text="Position fehlerhaft",
                 foreground='red').pack(side=tk.LEFT)
        
        # Weichen-Grid
        switches_frame = ttk.Frame(left_frame)
        switches_frame.pack(fill='both', expand=True)
        
        # Grid-Konfiguration für gleichmäßige Verteilung
        for i in range(4):
            switches_frame.columnconfigure(i, weight=1)
        for i in range(4):
            switches_frame.rowconfigure(i, weight=1)
        
        self.switches = []
        for i in range(16):
            row = i // 4
            col = i % 4
            
            # Weichen-Frame
            switch_frame = ttk.Frame(switches_frame)
            switch_frame.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
            
            # Weichennummer und Status
            header_frame = ttk.Frame(switch_frame)
            header_frame.pack(fill='x')
            
            ttk.Label(header_frame, text=f"Weiche {i+1}",
                     font=('Helvetica', 10)).pack(side=tk.LEFT)
            status_var = tk.StringVar(value="Rechts")
            status_label = ttk.Label(header_frame, textvariable=status_var,
                                   foreground='green', font=('Helvetica', 10))
            status_label.pack(side=tk.RIGHT)
            
            # Steuerungsbuttons
            btn_frame = ttk.Frame(switch_frame)
            btn_frame.pack(pady=1)
            
            left_btn = ttk.Button(btn_frame, text="←", width=2,
                                command=lambda x=i: self.set_switch(x, 'left'))
            left_btn.pack(side=tk.LEFT, padx=1)
            
            right_btn = ttk.Button(btn_frame, text="→", width=2,
                                 command=lambda x=i: self.set_switch(x, 'right'))
            right_btn.pack(side=tk.LEFT, padx=1)
            
            # Test-Button
            test_btn = ttk.Button(switch_frame, text="Test", width=6,
                                command=lambda x=i: self.test_switch(x))
            test_btn.pack(pady=1)
            
            self.switches.append({
                'status_var': status_var,
                'status_label': status_label,
                'left_btn': left_btn,
                'right_btn': right_btn,
                'test_btn': test_btn
            })
        
        # Rechte Spalte - Streckenlayout
        right_frame = ttk.LabelFrame(main_container, text="Streckenübersicht")
        right_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(5, 0))
        
        # Canvas für Streckenlayout
        self.canvas = tk.Canvas(right_frame, width=600, height=400, bg='white')
        self.canvas.pack(padx=5, pady=5, expand=True, fill='both')
        
        # Streckenlayout
        self.track_layout = TrackLayout(self.canvas.winfo_width(), self.canvas.winfo_height())
        
        # Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill='x', padx=10, pady=2)
        
        ttk.Button(footer_frame, text="✕ Beenden",
                  command=self.root.destroy).pack(side=tk.LEFT)
        
        ttk.Label(footer_frame, text="Developed by EinsPommes × chill-zone.xyz",
                 foreground='gray', font=('Helvetica', 8)).pack(side=tk.RIGHT)
        
        # ESC zum Beenden
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
        # Status aktualisieren
        self.update_switch_status()
    
    def set_switch(self, switch_num, position):
        """Setzt die Position einer Weiche"""
        self.servo_controller.set_servo_position(switch_num, position)
        self.update_switch_status()
    
    def test_switch(self, switch_num):
        """Testet eine einzelne Weiche"""
        self.set_switch(switch_num, 'right')
        time.sleep(0.5)
        self.set_switch(switch_num, 'left')
    
    def update_switch_status(self):
        """Aktualisiert den Status aller Weichen"""
        switch_states = {}
        for i in range(16):
            position = self.servo_controller.get_servo_position(i)
            
            # GUI aktualisieren
            switch = self.switches[i]
            status_text = "Rechts" if position == 'right' else "Links"
            switch['status_var'].set(status_text)
            switch['status_label'].config(
                foreground='green' if self.servo_controller.servo_states[i]['sensor_ok'] else 'red'
            )
            
            # Status für Streckenlayout
            switch_states[i+1] = {
                'position': position,
                'sensor_ok': self.servo_controller.servo_states[i]['sensor_ok']
            }
        
        # Layout aktualisieren
        self.track_layout.draw(self.canvas, switch_states)
        
        # Alle 100ms aktualisieren
        self.root.after(100, self.update_switch_status)
    
    def test_switches(self):
        """Testet alle Weichen"""
        for i in range(16):
            self.test_switch(i)
    
    def start_automation(self):
        """Startet den Automatik-Modus"""
        mode = self.mode_var.get()
        self.automation_controller.start_automation(mode)
        
        # Buttons deaktivieren
        for switch in self.switches:
            switch['left_btn'].config(state=tk.DISABLED)
            switch['right_btn'].config(state=tk.DISABLED)
            switch['test_btn'].config(state=tk.DISABLED)
    
    def stop_automation(self):
        """Stoppt den Automatik-Modus"""
        self.automation_controller.stop_automation()
        
        # Buttons wieder aktivieren
        for switch in self.switches:
            switch['left_btn'].config(state=tk.NORMAL)
            switch['right_btn'].config(state=tk.NORMAL)
            switch['test_btn'].config(state=tk.NORMAL)
