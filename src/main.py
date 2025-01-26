import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import logging
import os
import socket
from servokit_controller import ServoKitController
from web_server import run_server

class WeichensteuerungGUI(tk.Tk):
    def __init__(self):
        """Initialisiert die GUI"""
        try:
            # Logger initialisieren
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("GUI Initialisierung gestartet")
            
            # Hauptfenster erstellen
            super().__init__()
            
            # Vollbild für 10-Zoll-Display
            self.attributes('-fullscreen', True)
            
            # Escape zum Beenden
            self.bind('<Escape>', lambda e: self.destroy())
            
            # Style konfigurieren
            self.style = ttk.Style()
            self.style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
            self.style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))
            self.style.configure('Normal.TLabel', font=('Helvetica', 14))
            self.style.configure('Big.TButton', padding=5)
            
            # Fenstertitel
            self.title("Car Motion System")
            
            # Fenster mittig positionieren
            window_width = 800
            window_height = 600
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            center_x = int(screen_width/2 - window_width/2)
            center_y = int(screen_height/2 - window_height/2)
            self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
            
            # Kalibrierungs-Variablen
            self.cal_servo_var = tk.StringVar(value="Servo 1")
            self.left_angle_var = tk.StringVar(value="30.0")
            self.right_angle_var = tk.StringVar(value="150.0")
            self.current_servo = 0
            
            # Initialisiere ServoController
            try:
                self.servo_controller = ServoKitController()
                self.logger.debug("ServoController erfolgreich initialisiert")
            except Exception as e:
                self.logger.error(f"Fehler bei der Initialisierung des ServoControllers: {e}")
                messagebox.showerror("Fehler", f"ServoController konnte nicht initialisiert werden: {e}")
                raise
                
            # Initialisiere Dictionaries für LED Canvas und Position Labels
            self.led_canvas = {}
            self.position_labels = {}
            
            # Notebook für Tabs
            self.notebook = ttk.Notebook(self)
            self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
            
            # Control-Tab erstellen
            self.create_control_tab()
            
            # Kalibrierungs-Tab erstellen
            self.create_calibration_tab()
            
            # Status-Tab erstellen
            self.create_status_tab()
            
            # Gleiskarten-Tab erstellen
            self.create_track_tab()
            
            # Settings-Tab erstellen
            self.create_settings_tab()
            
            # Setze initialen Status
            self.logger.debug("Setze initialen Status")
            
            # Starte Status-Update Timer
            self.logger.debug("Starte Status-Update Timer")
            self.after(1000, self.update_servo_status)
            
            self.logger.debug("GUI Initialisierung abgeschlossen")
            
        except Exception as e:
            self.logger.error(f"Fehler bei der GUI Initialisierung: {e}")
            messagebox.showerror("Fehler", f"GUI konnte nicht initialisiert werden: {e}")
            raise
            
    def create_control_tab(self):
        """Erstellt den Control-Tab mit LED-Anzeigen und Buttons für jeden Servo"""
        self.logger.debug("Erstelle Control-Tab")
        
        # Frame für Control-Tab
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text='Steuerung')
        
        # Grid für Servo-Steuerung (4x4)
        for row in range(4):
            for col in range(4):
                i = row * 4 + col  # Servo-ID
                
                # Frame für jeden Servo
                servo_frame = ttk.LabelFrame(control_frame, text=f"Servo {i+1}", padding="5")
                servo_frame.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E))
                
                # Status-Frame
                status_frame = ttk.Frame(servo_frame)
                status_frame.pack(fill=tk.X, pady=2)
                
                # LED-Canvas
                canvas = tk.Canvas(status_frame, width=20, height=20, bg=self.cget('bg'), highlightthickness=0)
                canvas.pack(side=tk.LEFT)
                
                # LED (Kreis) zeichnen
                led = canvas.create_oval(5, 5, 15, 15, fill='gray')
                self.led_canvas[i] = (canvas, led)
                self.logger.debug(f"LED Canvas für Servo {i+1} erstellt")
                
                # Label für Servo-Nummer
                ttk.Label(servo_frame, text=f"Servo {i+1}", style='Normal.TLabel').pack()
                
                # Label für Position
                pos_label = ttk.Label(servo_frame, text="---", style='Normal.TLabel')
                pos_label.pack()
                self.position_labels[i] = pos_label
                self.logger.debug(f"Position Label für Servo {i+1} erstellt")
                
                # Button-Frame
                btn_frame = ttk.Frame(servo_frame)
                btn_frame.pack(pady=2)
                
                # Links-Button
                ttk.Button(btn_frame, 
                          text="←", 
                          width=3,
                          style='Big.TButton',
                          command=lambda s=i: self.move_left(s)).pack(side=tk.LEFT, padx=1)
                
                # Rechts-Button
                ttk.Button(btn_frame, 
                          text="→", 
                          width=3,
                          style='Big.TButton',
                          command=lambda s=i: self.move_right(s)).pack(side=tk.LEFT, padx=1)
                
        # Grid-Konfiguration
        for i in range(4):
            control_frame.grid_columnconfigure(i, weight=1)
            control_frame.grid_rowconfigure(i, weight=1)
            
        self.logger.debug(f"Control-Tab erstellt mit {len(self.led_canvas)} LED Canvas und {len(self.position_labels)} Position Labels")

    def move_left(self, servo_id):
        """Bewegt den Servo nach links"""
        try:
            self.logger.debug(f"Bewege Servo {servo_id+1} nach links")
            
            # Setze Status auf 'moving'
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                canvas.itemconfig(led, fill='yellow')
            
            # Bewege den Servo
            self.servo_controller.move_servo(servo_id, 'left')
            
            # Aktualisiere den Status
            self.update_led_status(servo_id)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id+1} nach links: {e}")
            messagebox.showerror("Fehler", f"Servo {servo_id+1} konnte nicht nach links bewegt werden: {e}")
            
            # Setze Status auf 'error'
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                canvas.itemconfig(led, fill='red')
                
    def move_right(self, servo_id):
        """Bewegt den Servo nach rechts"""
        try:
            self.logger.debug(f"Bewege Servo {servo_id+1} nach rechts")
            
            # Setze Status auf 'moving'
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                canvas.itemconfig(led, fill='yellow')
            
            # Bewege den Servo
            self.servo_controller.move_servo(servo_id, 'right')
            
            # Aktualisiere den Status
            self.update_led_status(servo_id)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id+1} nach rechts: {e}")
            messagebox.showerror("Fehler", f"Servo {servo_id+1} konnte nicht nach rechts bewegt werden: {e}")
            
            # Setze Status auf 'error'
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                canvas.itemconfig(led, fill='red')
                
    def update_led_status(self, servo_id):
        """Aktualisiert den LED-Status für einen einzelnen Servo"""
        try:
            state = self.servo_controller.servo_states.get(str(servo_id), {})
            status = state.get('status', 'unknown')
            position = state.get('position', None)
            
            self.logger.debug(f"Update LED Status für Servo {servo_id+1}: Status={status}, Position={position}")
            
            # Aktualisiere LED
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                color = {
                    'initialized': 'green',
                    'moving': 'yellow',
                    'error': 'red',
                    'unknown': 'gray'
                }.get(status, 'gray')
                canvas.itemconfig(led, fill=color)
                self.logger.debug(f"LED für Servo {servo_id+1} auf {color} gesetzt")
            
            # Aktualisiere Position Label
            if servo_id in self.position_labels:
                if status == 'error':
                    text = "Error"
                elif position == 'left':
                    text = "Links"
                elif position == 'right':
                    text = "Rechts"
                else:
                    text = "---"
                self.position_labels[servo_id].config(text=text)
                self.logger.debug(f"Position Label für Servo {servo_id+1} auf {text} gesetzt")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des LED-Status für Servo {servo_id+1}: {e}")
            
    def update_servo_status(self):
        """Aktualisiert die Status-LEDs und Position Labels aller Servos"""
        try:
            self.logger.debug("Starte Status-Update für alle Servos")
            for i in range(16):
                self.update_led_status(i)
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Status-LEDs: {e}")
        
        # Plane nächste Aktualisierung in 1 Sekunde
        self.after(1000, self.update_servo_status)
        
    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            self.logger.debug(f"Bewege Servo {servo_id+1} nach {direction}")
            
            # Setze Status auf 'moving'
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                canvas.itemconfig(led, fill='yellow')
                self.logger.debug(f"LED für Servo {servo_id+1} auf gelb gesetzt (moving)")
            
            # Bewege den Servo
            if direction == "left":
                self.move_left(servo_id)
            else:
                self.move_right(servo_id)
                
            # Aktualisiere den Status
            self.update_led_status(servo_id)
            self.logger.debug(f"Servo {servo_id+1} erfolgreich bewegt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id+1}: {e}")
            messagebox.showerror("Fehler", f"Servo {servo_id+1} konnte nicht bewegt werden: {e}")
            
            # Setze Status auf 'error'
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                canvas.itemconfig(led, fill='red')
                self.logger.debug(f"LED für Servo {servo_id+1} auf rot gesetzt (error)")
                
            if servo_id in self.position_labels:
                self.position_labels[servo_id].config(text="Error")
                self.logger.debug(f"Position Label für Servo {servo_id+1} auf 'Error' gesetzt")
                
    def create_calibration_tab(self):
        """Erstellt den Kalibrierungs-Tab"""
        self.logger.debug("Erstelle Kalibrierungs-Tab")
        
        # Frame für Kalibrierungs-Tab
        calibration_frame = ttk.Frame(self.notebook)
        self.notebook.add(calibration_frame, text='Kalibrierung')
        
        # Servo-Auswahl
        select_frame = ttk.Frame(calibration_frame)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_frame, text="Servo auswählen:", style='Normal.TLabel').pack(side=tk.LEFT, padx=5)
        servo_select = ttk.Combobox(select_frame, 
                                  textvariable=self.cal_servo_var,
                                  values=[f"Servo {i+1}" for i in range(16)],
                                  width=15,
                                  state="readonly")
        servo_select.pack(side=tk.LEFT, padx=5)
        
        # Start-Button
        ttk.Button(calibration_frame, 
                  text="Kalibrierung starten",
                  style='Big.TButton',
                  command=self.show_calibration_dialog).pack(pady=10)
        
        self.logger.debug("Kalibrierungs-Tab erstellt")
        
    def show_calibration_dialog(self):
        """Zeigt den Kalibrierungsdialog"""
        try:
            # Hole Servo-Nummer
            servo_str = self.cal_servo_var.get()
            if not servo_str:
                messagebox.showwarning("Warnung", "Bitte wählen Sie einen Servo aus")
                return
                
            self.current_servo = int(servo_str.split()[1]) - 1  # "Servo 1" -> 0
            
            # Prüfe ob Servo verfügbar
            if self.current_servo >= 8 and not self.servo_controller.dual_board:
                raise Exception(f"Servo {self.current_servo + 1} nicht verfügbar (kein zweites Board)")
            
            # Hole aktuelle Konfiguration oder setze Standardwerte
            config = self.servo_controller.config.get(str(self.current_servo), {})
            self.left_angle_var.set(str(config.get('left_angle', 30.0)))   # Standardwert 30.0° für links
            self.right_angle_var.set(str(config.get('right_angle', 150.0)))  # Standardwert 150.0° für rechts
            
            self.logger.info(f"Kalibrierung für Servo {self.current_servo + 1}: Links={self.left_angle_var.get()}°, Rechts={self.right_angle_var.get()}°")
            
            # Erstelle Kalibrierungsfenster
            self.cal_window = tk.Toplevel(self)
            self.cal_window.title(f"Kalibrierung Servo {self.current_servo + 1}")
            self.cal_window.geometry("400x400")  # Größeres Fenster
            self.cal_window.resizable(False, False)
            
            # Hauptframe mit Padding
            main_frame = ttk.Frame(self.cal_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Info-Label
            ttk.Label(main_frame, 
                     text="Stellen Sie die Positionen mit den Pfeiltasten ein",
                     wraplength=350,
                     justify=tk.CENTER,
                     style='Normal.TLabel').pack(pady=(0,20))
            
            # Linke Position
            left_frame = ttk.LabelFrame(main_frame, text="Linke Position", padding="10")
            left_frame.pack(fill=tk.X, pady=(0,10))
            
            # Winkel-Anzeige und Steuerung in einer Reihe
            left_ctrl = ttk.Frame(left_frame)
            left_ctrl.pack(fill=tk.X)
            ttk.Label(left_ctrl, text="Winkel:", width=8, style='Normal.TLabel').pack(side=tk.LEFT)
            
            # Label für linken Winkel
            self.left_angle_label = ttk.Label(left_ctrl, text=f"{self.left_angle_var.get()}°", width=5, style='Normal.TLabel')
            self.left_angle_label.pack(side=tk.LEFT)
            
            # Buttons rechtsbündig
            left_btn_frame = ttk.Frame(left_ctrl)
            left_btn_frame.pack(side=tk.RIGHT)
            ttk.Button(left_btn_frame, text="◄◄", width=3, style='Big.TButton', command=lambda: self.adjust_angle('left', -10)).pack(side=tk.LEFT, padx=1)
            ttk.Button(left_btn_frame, text="◄", width=3, style='Big.TButton', command=lambda: self.adjust_angle('left', -1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(left_btn_frame, text="►", width=3, style='Big.TButton', command=lambda: self.adjust_angle('left', 1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(left_btn_frame, text="►►", width=3, style='Big.TButton', command=lambda: self.adjust_angle('left', 10)).pack(side=tk.LEFT, padx=1)
            
            # Rechte Position
            right_frame = ttk.LabelFrame(main_frame, text="Rechte Position", padding="10")
            right_frame.pack(fill=tk.X, pady=(0,10))
            
            # Winkel-Anzeige und Steuerung in einer Reihe
            right_ctrl = ttk.Frame(right_frame)
            right_ctrl.pack(fill=tk.X)
            ttk.Label(right_ctrl, text="Winkel:", width=8, style='Normal.TLabel').pack(side=tk.LEFT)
            
            # Label für rechten Winkel
            self.right_angle_label = ttk.Label(right_ctrl, text=f"{self.right_angle_var.get()}°", width=5, style='Normal.TLabel')
            self.right_angle_label.pack(side=tk.LEFT)
            
            # Buttons rechtsbündig
            right_btn_frame = ttk.Frame(right_ctrl)
            right_btn_frame.pack(side=tk.RIGHT)
            ttk.Button(right_btn_frame, text="◄◄", width=3, style='Big.TButton', command=lambda: self.adjust_angle('right', -10)).pack(side=tk.LEFT, padx=1)
            ttk.Button(right_btn_frame, text="◄", width=3, style='Big.TButton', command=lambda: self.adjust_angle('right', -1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(right_btn_frame, text="►", width=3, style='Big.TButton', command=lambda: self.adjust_angle('right', 1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(right_btn_frame, text="►►", width=3, style='Big.TButton', command=lambda: self.adjust_angle('right', 10)).pack(side=tk.LEFT, padx=1)
            
            # Test-Buttons
            test_frame = ttk.Frame(main_frame)
            test_frame.pack(fill=tk.X, pady=10)
            ttk.Button(test_frame, text="Test Links", style='Big.TButton', command=lambda: self.test_position('left')).pack(side=tk.LEFT, expand=True, padx=5)
            ttk.Button(test_frame, text="Test Mitte", style='Big.TButton', command=lambda: self.test_position('center')).pack(side=tk.LEFT, expand=True, padx=5)
            ttk.Button(test_frame, text="Test Rechts", style='Big.TButton', command=lambda: self.test_position('right')).pack(side=tk.LEFT, expand=True, padx=5)
            
            # Speichern und Abbrechen Buttons
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(btn_frame, 
                      text="Speichern",
                      style='Big.TButton',
                      command=self.save_calibration).pack(side=tk.LEFT, expand=True, padx=5)
                      
            ttk.Button(btn_frame,
                      text="Abbrechen",
                      style='Big.TButton',
                      command=self.cal_window.destroy).pack(side=tk.LEFT, expand=True, padx=5)
            
            # Mache Fenster modal
            self.cal_window.transient(self)
            self.cal_window.grab_set()
            
            # Setze Servo auf Mittelposition
            self.test_position('center')
            
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Kalibrierungsdialogs: {e}")
            messagebox.showerror("Fehler", str(e))
            if hasattr(self, 'cal_window'):
                self.cal_window.destroy()
                
    def adjust_angle(self, position, delta):
        """Passt den Winkel für eine Position an"""
        try:
            # Hole aktuelle Werte
            if position == 'left':
                current = float(self.left_angle_var.get())
                new_value = current + delta
                if 0 <= new_value <= 90:
                    self.left_angle_var.set(f"{new_value:.1f}")
                    self.left_angle_label.config(text=f"{new_value:.1f}°")
                    # Bewege Servo
                    self.test_position('left')
            else:  # right
                current = float(self.right_angle_var.get())
                new_value = current + delta
                if 90 <= new_value <= 180:
                    self.right_angle_var.set(f"{new_value:.1f}")
                    self.right_angle_label.config(text=f"{new_value:.1f}°")
                    # Bewege Servo
                    self.test_position('right')
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Anpassen des Winkels: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def test_position(self, position):
        """Testet eine Position während der Kalibrierung"""
        try:
            if position == 'left':
                angle = float(self.left_angle_var.get())
            elif position == 'right':
                angle = float(self.right_angle_var.get())
            else:  # center
                # Setze direkt auf 90 Grad für die Mittelposition
                angle = 90.0
                
            # Setze Winkel
            if self.current_servo < 8:
                self.servo_controller.kit1.servo[self.current_servo].angle = angle
            else:
                if not self.servo_controller.dual_board:
                    raise Exception("Zweites Board nicht verfügbar")
                self.servo_controller.kit2.servo[self.current_servo-8].angle = angle
                
            self.logger.info(f"Test: Servo {self.current_servo + 1} auf {angle}° gesetzt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Testen der Position: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def create_track_tab(self):
        """Erstellt den Gleiskarten-Tab"""
        self.logger.debug("Erstelle Gleiskarten-Tab")
        
        # Frame für Gleiskarten-Tab
        track_frame = ttk.Frame(self.notebook)
        self.notebook.add(track_frame, text='Gleiskarte')
        
        # TODO: Implementiere Gleiskarte
        ttk.Label(track_frame, text="Gleiskarte wird noch implementiert", style='Normal.TLabel').pack(pady=20)
        
        self.logger.debug("Gleiskarten-Tab erstellt")

    def create_status_tab(self):
        """Erstellt den Status-Tab"""
        self.logger.debug("Erstelle Status-Tab")
        
        # Frame für Status-Tab
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text='Status')
        
        # Status-Informationen
        ttk.Label(status_frame, text="Servo-Controller Status:", style='Header.TLabel').pack(pady=(20,5))
        
        # Status-Text
        status_text = tk.Text(status_frame, height=10, width=50)
        status_text.pack(padx=20, pady=5)
        
        # Füge Status-Informationen hinzu
        status_info = [
            f"ServoKit 1 (0x40): {'Verbunden' if self.servo_controller.kit1 else 'Nicht verbunden'}",
            f"ServoKit 2 (0x41): {'Verbunden' if self.servo_controller.dual_board else 'Nicht verbunden'}",
            f"Aktive Servos: {len([s for s in range(16) if self.servo_controller.get_servo_status(s)['initialized']])}/16",
            f"Software-Version: 1.0.0"
        ]
        
        for info in status_info:
            status_text.insert(tk.END, info + "\n")
        
        status_text.config(state='disabled')
        
        # Aktualisieren-Button
        ttk.Button(status_frame, 
                  text="Aktualisieren",
                  style='Big.TButton',
                  command=self.update_status).pack(pady=10)
        
        self.logger.debug("Status-Tab erstellt")

    def create_settings_tab(self):
        """Erstellt den Settings-Tab"""
        self.logger.debug("Erstelle Settings-Tab")
        
        # Frame für Settings-Tab
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text='Info & Einstellungen')
        
        # Info Frame
        info_frame = ttk.LabelFrame(settings_frame, text="Programm-Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Version und Copyright
        ttk.Label(info_frame, text="Car Motion System", style='Title.TLabel').pack(pady=5)
        ttk.Label(info_frame, text="Version 1.0", style='Normal.TLabel').pack()
        ttk.Label(info_frame, text=" 2024 EinsPommes", style='Normal.TLabel').pack(pady=5)
        
        # Beschreibung
        desc_text = """
        Diese Software ermöglicht die Steuerung von bis zu 16 Servomotoren für Ihr Fahrzeug.
        Die Servos können einzeln kalibriert und gesteuert werden,
        um präzise Bewegungen zu ermöglichen.
        Die Steuerung erfolgt wahlweise über die grafische
        Oberfläche oder über das Webinterface."""
        ttk.Label(info_frame, text=desc_text, wraplength=400, justify=tk.CENTER, style='Normal.TLabel').pack(pady=10)
        
        # IP-Adresse
        ip_frame = ttk.Frame(settings_frame)
        ip_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.ip_label = ttk.Label(ip_frame, text="IP-Adresse: ...", style='Normal.TLabel')
        self.ip_label.pack()
        
        # Aktualisiere IP-Adresse
        self.update_ip()
        
        # I2C Einstellungen
        i2c_frame = ttk.LabelFrame(settings_frame, text="I2C Einstellungen", padding="10")
        i2c_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status der I2C Boards
        board1_frame = ttk.Frame(i2c_frame)
        board1_frame.pack(fill=tk.X, pady=2)
        ttk.Label(board1_frame, text="Board 1 (0x40):", style='Normal.TLabel').pack(side=tk.LEFT, padx=5)
        self.board1_status = ttk.Label(board1_frame, text="Verbunden" if self.servo_controller.kit1 else "Nicht verbunden", style='Normal.TLabel')
        self.board1_status.pack(side=tk.LEFT)
        
        board2_frame = ttk.Frame(i2c_frame)
        board2_frame.pack(fill=tk.X, pady=2)
        ttk.Label(board2_frame, text="Board 2 (0x41):", style='Normal.TLabel').pack(side=tk.LEFT, padx=5)
        self.board2_status = ttk.Label(board2_frame, text="Verbunden" if self.servo_controller.dual_board else "Nicht verbunden", style='Normal.TLabel')
        self.board2_status.pack(side=tk.LEFT)
        
        # Konfiguration
        config_frame = ttk.LabelFrame(settings_frame, text="Konfiguration", padding="10")
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Konfigurationsdatei
        config_file_frame = ttk.Frame(config_frame)
        config_file_frame.pack(fill=tk.X, pady=2)
        ttk.Label(config_file_frame, text="Konfigurationsdatei:", style='Normal.TLabel').pack(side=tk.LEFT, padx=5)
        ttk.Label(config_file_frame, text=self.servo_controller.config_file, style='Normal.TLabel').pack(side=tk.LEFT)
        
        # Buttons für Konfiguration
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, 
                  text="Konfiguration neu laden",
                  style='Big.TButton',
                  command=self.reload_config).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(btn_frame,
                  text="Konfiguration zurücksetzen",
                  style='Big.TButton',
                  command=self.reset_config).pack(side=tk.LEFT, padx=5)
        
        # Programm-Steuerung
        control_frame = ttk.LabelFrame(settings_frame, text="Programm-Steuerung", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        control_btn_frame = ttk.Frame(control_frame)
        control_btn_frame.pack(fill=tk.X, pady=5)
        
        # Update-Button
        update_btn = ttk.Button(control_btn_frame,
                              text="Nach Updates suchen",
                              style='Big.TButton',
                              command=self.check_for_updates)
        update_btn.pack(side=tk.LEFT, padx=5)
        
        # Beenden-Button
        exit_btn = ttk.Button(control_btn_frame,
                            text="Programm beenden",
                            style='Big.TButton',
                            command=self.quit_program)
        exit_btn.pack(side=tk.RIGHT, padx=5)
                  
        # GitHub Link
        link_frame = ttk.Frame(settings_frame)
        link_frame.pack(fill=tk.X, padx=10, pady=10)
        
        link_label = ttk.Label(link_frame, 
                             text="GitHub Repository", 
                             foreground="blue", 
                             cursor="hand2",
                             style='Normal.TLabel')
        link_label.pack()
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/EinsPommes"))
        
        self.logger.debug("Settings-Tab erstellt")
        
    def check_for_updates(self):
        """Prüft auf Updates"""
        try:
            # Hier könnte später die Update-Logik implementiert werden
            messagebox.showinfo("Updates", "Keine neuen Updates verfügbar.")
        except Exception as e:
            self.logger.error(f"Fehler bei der Update-Prüfung: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def quit_program(self):
        """Beendet das Programm"""
        try:
            if messagebox.askyesno("Beenden", "Möchten Sie das Programm wirklich beenden?"):
                self.logger.info("Programm wird beendet")
                self.destroy()
        except Exception as e:
            self.logger.error(f"Fehler beim Beenden: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def reload_config(self):
        """Lädt die Konfiguration neu"""
        try:
            if self.servo_controller.load_config():
                messagebox.showinfo("Erfolg", "Konfiguration erfolgreich neu geladen")
            else:
                raise Exception("Fehler beim Laden der Konfiguration")
        except Exception as e:
            self.logger.error(f"Fehler beim Neuladen der Konfiguration: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def reset_config(self):
        """Setzt die Konfiguration zurück"""
        try:
            if messagebox.askyesno("Bestätigung", 
                                 "Möchten Sie wirklich alle Kalibrierungseinstellungen zurücksetzen?"):
                self.servo_controller.config = {}
                if self.servo_controller.save_config():
                    messagebox.showinfo("Erfolg", "Konfiguration erfolgreich zurückgesetzt")
                else:
                    raise Exception("Fehler beim Speichern der Konfiguration")
        except Exception as e:
            self.logger.error(f"Fehler beim Zurücksetzen der Konfiguration: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def update_status(self):
        """Aktualisiert den Status aller Servos"""
        try:
            # Aktualisiere Status-LEDs
            for servo_id in range(16):  # 16 Servos
                frame_data = self.servo_frames[servo_id]
                if not frame_data:
                    continue
                    
                # Hole Servo-Status
                state = self.servo_controller.servo_states[servo_id]
                
                # Hole Position vom Controller falls nicht angegeben
                position = state.get('position')
                
                # Aktualisiere Positions-Label
                if position in ['left', 'right']:
                    frame_data['pos_label'].config(text=position.capitalize())
                else:
                    frame_data['pos_label'].config(text='?')
                
                # Aktualisiere LED-Farbe
                if state['error']:
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='red')
                elif time.time() - state['last_move'] < 0.5:  # Bewegung in den letzten 0.5 Sekunden
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='yellow')
                elif position in ['left', 'right']:  # Position bekannt
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='green')
                else:
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='gray')
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Status: {e}")
            
        # Plane nächste Aktualisierung
        self.after(500, self.update_status)
        
    def init_servo_controller(self):
        """Initialisiert den Servo-Controller"""
        try:
            self.logger.info("Initialisiere Servo-Controller...")
            self.servo_controller = ServoKitController()
            self.logger.info("Servo-Controller erfolgreich initialisiert")
            
            # Test-Bewegung durchführen
            self.logger.info("Führe Test-Bewegung durch...")
            success = self.servo_controller.move_servo(0, 'left')
            if success:
                self.logger.info("Test-Bewegung erfolgreich")
            else:
                self.logger.error("Test-Bewegung fehlgeschlagen")
            
        except Exception as e:
            self.logger.error(f"Fehler bei Controller-Initialisierung: {str(e)}")
            messagebox.showerror("Fehler", f"Konnte Servo-Controller nicht initialisieren: {str(e)}")
            raise
            
    def on_closing(self):
        """Handler für das Schließen des Fensters"""
        try:
            self._closing = True  # Flag setzen um Update-Loop zu stoppen
            
            # Servo-Controller herunterfahren
            if hasattr(self, 'servo_controller'):
                self.servo_controller.cleanup()
            
            # Fenster zerstören
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Schließen: {e}")
            self.destroy()  # Trotzdem versuchen zu schließen

    def update_servo_list(self):
        """Aktualisiert die Servo-Liste"""
        try:
            # Hole aktuelle Auswahl
            current = self.servo_var.get()
            
            # Liste leeren
            self.servo_list['menu'].delete(0, 'end')
            
            # Neue Einträge hinzufügen
            for i in range(16):
                # Prüfe ob Servo verfügbar
                if i >= 8 and not self.servo_controller.dual_board:
                    continue
                    
                # Bestimme Textfarbe basierend auf Servo-Status
                state = self.servo_controller.servo_states[i]
                
                # Bestimme Farbe basierend auf Servo-Status
                if state['error']:
                    fg = 'red'  # Rot für Fehler
                elif not state['initialized']:
                    fg = 'orange'  # Orange für nicht initialisiert
                else:
                    fg = 'black'  # Schwarz für normal
                    
                # Füge Eintrag hinzu
                self.servo_list['menu'].add_command(
                    label=f'Servo {i+1}',
                    command=lambda x=f'Servo {i+1}': self.servo_var.set(x),
                    foreground=fg
                )
            
            # Setze Auswahl zurück wenn möglich
            if current in [f'Servo {i+1}' for i in range(16)]:
                self.servo_var.set(current)
            else:
                self.servo_var.set('Servo 1')
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Servo-Liste: {e}")
            messagebox.showerror("Fehler", str(e))

    def toggle_servo_active(self):
        """Aktiviert oder deaktiviert den ausgewählten Servo"""
        try:
            # Hole ausgewählten Servo
            servo_id = int(self.servo_var.get().split()[1])
            
            # Hole aktuelle Konfiguration
            config = self.servo_controller.config
            
            # Prüfe ob Servo aktiv ist
            if servo_id in config['active_servos']:
                # Deaktiviere Servo
                config['active_servos'].remove(servo_id)
                self.logger.info(f"Servo {servo_id} deaktiviert")
            else:
                # Aktiviere Servo
                config['active_servos'].append(servo_id)
                self.logger.info(f"Servo {servo_id} aktiviert")
            
            # Speichere Konfiguration
            with open(self.servo_controller.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Aktualisiere GUI
            self.update_servo_list()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktivieren/Deaktivieren des Servos: {e}")
            messagebox.showerror("Fehler", str(e))

    def test_servo(self, direction):
        """Testet einen Servo mit den aktuellen Einstellungen"""
        try:
            # Hole Servo-ID
            servo_str = self.servo_var.get()
            servo_id = int(servo_str.split()[1]) - 1  # "Servo 1" -> 0
            
            # Hole Winkel
            if direction == 'left':
                angle = float(self.left_angle_var.get())
            else:
                angle = float(self.right_angle_var.get())
                
            # Setze Winkel direkt
            if servo_id < 8:
                self.servo_controller.kit1.servo[servo_id].angle = angle
            elif self.servo_controller.dual_board:
                self.servo_controller.kit2.servo[servo_id-8].angle = angle
            else:
                raise Exception("Zweites Board nicht verfügbar")
                
            # Aktualisiere Status
            self.servo_controller.servo_states[servo_id].update({
                'position': direction,
                'current_angle': angle,
                'last_move': time.time(),
                'error': False,
                'initialized': True
            })
            
            self.logger.info(f"Test: Servo {servo_id+1} auf {angle}° ({direction}) gesetzt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Testen: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Testen: {str(e)}")
            
    def create_servo_frame(self, parent, servo_id):
        """Erstellt einen Frame für einen Servo mit Steuerung und Status"""
        servo_frame = ttk.LabelFrame(parent, text=f"Servo {servo_id + 1}")
        
        # Status-Anzeige
        status_frame = ttk.Frame(servo_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # LED
        canvas = tk.Canvas(status_frame, width=20, height=20)
        canvas.pack(side=tk.LEFT, padx=2)
        
        # LED (Kreis) zeichnen
        led = canvas.create_oval(5, 5, 15, 15, fill='gray')
        self.servo_leds[servo_id] = (canvas, led)
        self.logger.debug(f"LED Canvas für Servo {servo_id+1} erstellt")
        
        # Label für Servo-Nummer
        ttk.Label(servo_frame, text=f"Servo {servo_id + 1}", style='Normal.TLabel').pack()
        
        # Label für Position
        pos_label = ttk.Label(servo_frame, text="---", style='Normal.TLabel')
        pos_label.pack()
        self.position_labels[servo_id] = pos_label
        self.logger.debug(f"Position Label für Servo {servo_id+1} erstellt")
        
        # Button-Frame
        btn_frame = ttk.Frame(servo_frame)
        btn_frame.pack(pady=2)
        
        # Links-Button
        ttk.Button(btn_frame, 
                  text="←", 
                  width=3,
                  style='Big.TButton',
                  command=lambda s=servo_id: self.move_servo(s, 'left')).pack(side=tk.LEFT, padx=1)
        
        # Rechts-Button
        ttk.Button(btn_frame, 
                  text="→", 
                  width=3,
                  style='Big.TButton',
                  command=lambda s=servo_id: self.move_servo(s, 'right')).pack(side=tk.LEFT, padx=1)
        
        return servo_frame, canvas, led, pos_label

    def update_servo_status(self, servo_id=None, position=None):
        """Aktualisiert die Statusanzeige für einen Servo"""
        try:
            if not hasattr(self, 'status_labels'):
                return
                
            if servo_id is None:
                for i in range(16):
                    self.update_servo_status(i)
                return
                
            if servo_id not in self.status_labels:
                return
                
            label = self.status_labels[servo_id]
            
            # Hole Position vom Controller falls nicht angegeben
            if position is None:
                position = self.servo_controller.servo_states[servo_id-1]['position']
            
            # Setze Text und Farbe
            if position == "left":
                label.config(text="Links", fg="green")
            elif position == "right":
                label.config(text="Rechts", fg="blue")
            else:
                label.config(text="Fehler", fg="red")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Servo-Status: {e}")
            if servo_id in self.status_labels:
                self.status_labels[servo_id].config(text="Fehler", fg="red")
                
    def set_servo_position(self, servo_id, position):
        try:
            # Position setzen (synchron)
            self.servo_controller.set_servo_position_sync(servo_id, position)
            
            # GUI aktualisieren
            self.update_servo_status(servo_id)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Setzen der Position: {str(e)}")
            
    def check_for_updates(self):
        """Prüft auf Updates und installiert sie bei Bedarf"""
        try:
            # Wechsle in das Projektverzeichnis
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Prüfe auf lokale Änderungen
            status = subprocess.run(['git', 'status', '--porcelain'],
                                 cwd=project_dir,
                                 capture_output=True,
                                 text=True)
            
            if status.stdout.strip():
                # Es gibt lokale Änderungen
                if messagebox.askyesno("Lokale Änderungen", 
                    "Es gibt lokale Änderungen. Möchten Sie diese erst speichern?\n" +
                    "- Ja: Änderungen werden committet\n" +
                    "- Nein: Änderungen werden verworfen"):
                    # Commit lokale Änderungen
                    subprocess.run(['git', 'add', '.'], cwd=project_dir)
                    subprocess.run(['git', 'commit', '-m', "Automatisches Backup vor Update"], 
                                cwd=project_dir)
                else:
                    # Verwerfe lokale Änderungen
                    subprocess.run(['git', 'reset', '--hard'], cwd=project_dir)
            
            # Führe git fetch origin main aus
            result = subprocess.run(['git', 'fetch', 'origin', 'main'], 
                                 cwd=project_dir,
                                 capture_output=True,
                                 text=True)
            
            if result.returncode == 0:
                # Prüfe ob Updates verfügbar sind
                diff = subprocess.run(['git', 'diff', 'HEAD', 'origin/main', '--stat'],
                                   cwd=project_dir,
                                   capture_output=True,
                                   text=True)
                
                if diff.stdout.strip():
                    # Es gibt Updates
                    if messagebox.askyesno("Updates verfügbar", 
                                         "Es sind Updates verfügbar. Möchten Sie diese jetzt installieren?\n" +
                                         "Das Programm wird danach neu gestartet."):
                        # Führe git pull aus
                        pull_result = subprocess.run(['git', 'pull', 'origin', 'main'],
                                                   cwd=project_dir,
                                                   capture_output=True,
                                                   text=True)
                        
                        if pull_result.returncode == 0:
                            messagebox.showinfo("Update erfolgreich", 
                                             "Updates wurden installiert. Das Programm wird neu gestartet.")
                            # Programm neu starten
                            python = sys.executable
                            os.execl(python, python, *sys.argv)
                        else:
                            messagebox.showerror("Fehler", 
                                               f"Installation fehlgeschlagen: {pull_result.stderr}")
                else:
                    messagebox.showinfo("Kein Update", "Es sind keine Updates verfügbar.")
            else:
                messagebox.showerror("Fehler", f"Update-Prüfung fehlgeschlagen: {result.stderr}")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Update: {str(e)}")
            
    def quit_application(self):
        """Beendet die Anwendung"""
        if messagebox.askokcancel("Beenden", "Möchten Sie die Anwendung wirklich beenden?"):
            self.servo_controller.cleanup()
            self.destroy()
            
    def update_software(self):
        """Software über Git aktualisieren"""
        import subprocess
        import sys
        import os

        try:
            # Aktuelles Verzeichnis speichern
            current_dir = os.getcwd()
            
            # In das Projektverzeichnis wechseln
            os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Git-Befehle ausführen
            subprocess.check_call(['git', 'fetch', 'origin'])
            subprocess.check_call(['git', 'reset', '--hard', 'origin/main'])
            
            # Zurück zum ursprünglichen Verzeichnis
            os.chdir(current_dir)
            
            # Erfolgsmeldung
            messagebox.showinfo("Update", "Update erfolgreich! Bitte starten Sie das Programm neu.")
            
            # Programm beenden
            self.quit_application()
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Fehler", f"Update fehlgeschlagen: {str(e)}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Unerwarteter Fehler: {str(e)}")
            
    def save_calibration(self):
        """Speichert die Kalibrierungseinstellungen"""
        try:
            # Hole aktuelle Werte
            left = float(self.left_angle_var.get())
            right = float(self.right_angle_var.get())
            
            # Validiere Werte
            if not (0 <= left <= 90):
                raise ValueError(f"Ungültiger linker Winkel: {left}")
            if not (90 <= right <= 180):
                raise ValueError(f"Ungültiger rechter Winkel: {right}")
                
            # Speichere in Konfiguration
            self.servo_controller.config[str(self.current_servo)] = {
                'left_angle': left,
                'right_angle': right,
                'speed': 0.5  # Standard-Geschwindigkeit
            }
            
            # Speichere Konfiguration
            self.servo_controller.save_config()
            messagebox.showinfo("Erfolg", "Kalibrierung erfolgreich gespeichert")
            self.cal_window.destroy()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Kalibrierung: {e}")
            messagebox.showerror("Fehler", str(e))

    def get_ip_address(self):
        """Ermittelt die IP-Adresse"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def update_ip(self):
        """Aktualisiert die IP-Adresse in der GUI"""
        ip = self.get_ip_address()
        self.ip_label.config(text=f"IP-Adresse: {ip}:5000")
        self.after(5000, self.update_ip)  # Erneut in 5 Sekunden

def main():
    try:
        root = WeichensteuerungGUI()
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Starten: {str(e)}")
        raise

if __name__ == "__main__":
    main()