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
        self.root.configure(bg='#f0f0f0')  # Hellgrauer Hintergrund
        
        # Vollbildmodus für 10 Zoll Display
        self.root.attributes('-fullscreen', True)
        
        # Moderne Styles definieren
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('Card.TFrame', background='white', relief='solid', borderwidth=1)
        self.style.configure('TButton', padding=10, font=('Segoe UI', 10))
        self.style.configure('Action.TButton', padding=10, font=('Segoe UI', 10, 'bold'))
        self.style.configure('Switch.TButton', padding=(15, 8), font=('Segoe UI', 12, 'bold'))
        self.style.configure('TRadiobutton', padding=8, font=('Segoe UI', 10))
        self.style.configure('TLabel', font=('Segoe UI', 10), background='#f0f0f0')
        self.style.configure('Header.TLabel', font=('Segoe UI', 24, 'bold'), background='#f0f0f0')
        self.style.configure('Subheader.TLabel', font=('Segoe UI', 14), background='#f0f0f0')
        self.style.configure('Card.TLabel', background='white')
        
        # Hauptcontainer
        main_container = ttk.Frame(self.root, style='TFrame')
        main_container.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Linke Spalte
        left_frame = ttk.Frame(main_container, style='TFrame')
        left_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(0, 10))
        
        # Titel mit modernem Design
        title = ttk.Label(left_frame, text="Weichensteuerung",
                         style='Header.TLabel')
        title.pack(anchor='w', pady=(0, 5))
        
        subtitle = ttk.Label(left_frame, text="Systemstatus und Kontrolle",
                           style='Subheader.TLabel')
        subtitle.pack(anchor='w', pady=(0, 20))
        
        # Automatik-Modus Frame mit Kartendesign
        auto_frame = ttk.LabelFrame(left_frame, text="Automatik-Modus", style='Card.TFrame')
        auto_frame.pack(fill='x', pady=(0, 20))
        
        # Modus-Auswahl mit besserem Spacing
        mode_frame = ttk.Frame(auto_frame, style='Card.TFrame')
        mode_frame.pack(padx=15, pady=10)
        
        ttk.Label(mode_frame, text="Betriebsmodus:", 
                 style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="sequence")
        ttk.Radiobutton(mode_frame, text="Sequentiell", value="sequence",
                       variable=self.mode_var).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Zufällig", value="random",
                       variable=self.mode_var).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Muster", value="pattern",
                       variable=self.mode_var).pack(side=tk.LEFT, padx=5)
        
        # Start/Stop Buttons mit Action-Style
        button_frame = ttk.Frame(auto_frame, style='Card.TFrame')
        button_frame.pack(padx=15, pady=(0, 10))
        
        ttk.Button(button_frame, text="▶ Start Automatik",
                  command=self.start_automation,
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⬛ Stop Automatik",
                  command=self.stop_automation,
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        
        # Status-Legende mit Icons
        legend_frame = ttk.Frame(left_frame, style='TFrame')
        legend_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(legend_frame, text="✓ Position korrekt",
                 foreground='#2ecc71', style='TLabel').pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(legend_frame, text="⚠ Position fehlerhaft",
                 foreground='#e74c3c', style='TLabel').pack(side=tk.LEFT)
        
        # Weichen-Grid mit Karten-Design
        switches_frame = ttk.Frame(left_frame, style='TFrame')
        switches_frame.pack(fill='both', expand=True)
        
        # Grid-Konfiguration
        for i in range(4):
            switches_frame.columnconfigure(i, weight=1)
        for i in range(4):
            switches_frame.rowconfigure(i, weight=1)
        
        self.switches = []
        for i in range(16):
            row = i // 4
            col = i % 4
            
            # Weichen-Karte
            switch_frame = ttk.Frame(switches_frame, style='Card.TFrame')
            switch_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # Weichennummer und Status
            header_frame = ttk.Frame(switch_frame, style='Card.TFrame')
            header_frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(header_frame, text=f"Weiche {i+1}",
                     style='Card.TLabel').pack(side=tk.LEFT)
            status_var = tk.StringVar(value="Rechts")
            status_label = ttk.Label(header_frame, textvariable=status_var,
                                   foreground='#2ecc71', style='Card.TLabel')
            status_label.pack(side=tk.RIGHT)
            
            # Steuerungsbuttons mit Icons
            btn_frame = ttk.Frame(switch_frame, style='Card.TFrame')
            btn_frame.pack(pady=5)
            
            left_btn = ttk.Button(btn_frame, text="◀",
                                command=lambda x=i: self.set_switch(x, 'left'),
                                style='Switch.TButton')
            left_btn.pack(side=tk.LEFT, padx=2)
            
            right_btn = ttk.Button(btn_frame, text="▶",
                                 command=lambda x=i: self.set_switch(x, 'right'),
                                 style='Switch.TButton')
            right_btn.pack(side=tk.LEFT, padx=2)
            
            # Test-Button
            test_btn = ttk.Button(switch_frame, text="▷ Test",
                                command=lambda x=i: self.test_switch(x),
                                style='TButton')
            test_btn.pack(pady=5)
            
            self.switches.append({
                'status_var': status_var,
                'status_label': status_label,
                'left_btn': left_btn,
                'right_btn': right_btn,
                'test_btn': test_btn
            })
        
        # Rechte Spalte - Streckenlayout
        right_frame = ttk.LabelFrame(main_container, text="Streckenübersicht",
                                   style='Card.TFrame')
        right_frame.pack(side=tk.LEFT, fill='both', expand=True, padx=(10, 0))
        
        # Canvas für Streckenlayout
        self.canvas = tk.Canvas(right_frame, width=600, height=400,
                              bg='white', highlightthickness=0)
        self.canvas.pack(padx=10, pady=10, expand=True, fill='both')
        
        # Streckenlayout
        self.track_layout = TrackLayout(self.canvas.winfo_width(),
                                      self.canvas.winfo_height())
        
        # Footer mit modernem Design
        footer_frame = ttk.Frame(self.root, style='TFrame')
        footer_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(footer_frame, text="✕ Beenden",
                  command=self.root.destroy,
                  style='Action.TButton').pack(side=tk.LEFT)
        
        ttk.Label(footer_frame,
                 text="Developed by EinsPommes × chill-zone.xyz",
                 foreground='#95a5a6',
                 style='TLabel').pack(side=tk.RIGHT)
        
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
                foreground='#2ecc71' if self.servo_controller.servo_states[i]['sensor_ok'] else '#e74c3c'
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
