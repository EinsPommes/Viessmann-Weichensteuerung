import logging
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import time
from servokit_controller import ServoKitController
from pigpio_servo_controller import PiGPIOServoController
from hall_sensor import HallSensor
from automation_controller import AutomationController
from gui import GUI
from track_map import TrackMap

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from servokit_controller import ServoKitController
from hall_sensor import HallSensor
from automation_controller import AutomationController
from gui import GUI
from track_map import TrackMap
import json
import os
import sys
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import time
import pigpio
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from logging.handlers import RotatingFileHandler
import os
import json
import time
import pigpio
import subprocess
import threading
from datetime import datetime
from pigpio_servo_controller import PiGPIOServoController, PCA9685ServoController
from automation_controller import AutomationController
from hall_sensor import HallSensor

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
import sys
import subprocess
import logging
from servokit_controller import ServoKitController

class WeichensteuerungGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # Fenster-Einstellungen für 10 Zoll Display
        self.title("Weichensteuerung")
        self.geometry("800x480")  # Typische 10 Zoll Auflösung
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Variablen initialisieren
        self.servo_var = tk.StringVar(value="Servo 1")
        self.cal_servo_var = tk.StringVar(value="Servo 1")
        self.pattern_var = tk.StringVar()
        self.speed_var = tk.DoubleVar(value=1.0)
        
        # Status-Variablen
        self.servo_leds = {}  # Canvas-Objekte für LEDs
        self.position_labels = {}  # Labels für Positionen
        self.automation_running = False
        self.automation_task = None
        
        # Kalibrierungs-Variablen
        self.left_angle = 30.0
        self.right_angle = 150.0
        self.current_servo = 0
        
        # Servo Controller initialisieren
        try:
            self.servo_controller = ServoKitController()
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren des Servo Controllers: {e}")
            messagebox.showerror("Fehler", str(e))
            self.destroy()
            return
            
        # Style konfigurieren für bessere Lesbarkeit auf kleinem Display
        style = ttk.Style()
        style.configure('TButton', padding=5, font=('Helvetica', 10))
        style.configure('TLabel', font=('Helvetica', 10))
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        
        # Notebook (Tabs) erstellen
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        
        # Tabs erstellen
        self.control_tab = ttk.Frame(self.notebook)
        self.automation_tab = ttk.Frame(self.notebook)
        self.calibration_tab = ttk.Frame(self.notebook)
        self.track_tab = ttk.Frame(self.notebook)
        self.info_tab = ttk.Frame(self.notebook)
        
        # Tabs zum Notebook hinzufügen
        self.notebook.add(self.control_tab, text="Steuerung")
        self.notebook.add(self.automation_tab, text="Automation")
        self.notebook.add(self.calibration_tab, text="Kalibrierung")
        self.notebook.add(self.track_tab, text="Gleiskarte")
        self.notebook.add(self.info_tab, text="Info")
        
        # Tab-Inhalte erstellen
        self.create_control_tab(self.control_tab)
        self.create_automation_tab(self.automation_tab)
        self.create_calibration_tab(self.calibration_tab)
        self.create_track_tab(self.track_tab)
        self.create_info_tab(self.info_tab)
        
        # Status-Update Timer
        self.after(1000, self.update_servo_status)
        
        # Fenster-Close Handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_control_tab(self, parent):
        """Erstellt den Control-Tab"""
        # Frame für Servo-Steuerung
        servos_frame = ttk.LabelFrame(parent, text="Servo-Steuerung")
        servos_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Dictionary für Position Labels
        self.position_labels = {}
        
        # Erstelle Steuerelemente für jeden Servo
        for i in range(16):
            # Frame für diesen Servo
            servo_frame = ttk.Frame(servos_frame)
            servo_frame.grid(row=i//4, column=i%4, padx=5, pady=5, sticky='nsew')
            
            # Servo-Nummer und LED
            header_frame = ttk.Frame(servo_frame)
            header_frame.pack(side='top')
            
            ttk.Label(header_frame, text=f"Servo {i+1}").pack(side='left', padx=(0,5))
            
            led_canvas = tk.Canvas(header_frame, width=10, height=10)
            led_canvas.pack(side='left')
            led_canvas.create_oval(1, 1, 9, 9, fill='gray', tags=f'led_{i}')
            
            # Position Label
            pos_label = ttk.Label(servo_frame, text="---")
            pos_label.pack(side='top', pady=2)
            self.position_labels[str(i)] = pos_label
            
            # Button Frame
            btn_frame = ttk.Frame(servo_frame)
            btn_frame.pack(side='top', pady=2)
            
            # Links-Button
            ttk.Button(btn_frame, 
                      text="←", 
                      width=2,
                      command=lambda s=i: self.move_servo(s, 'left')).pack(side='left', padx=1)
            
            # Rechts-Button
            ttk.Button(btn_frame, 
                      text="→", 
                      width=2,
                      command=lambda s=i: self.move_servo(s, 'right')).pack(side='left', padx=1)
            
        # Grid-Konfiguration
        for i in range(4):
            servos_frame.grid_rowconfigure(i, weight=1)
            servos_frame.grid_columnconfigure(i, weight=1)
            
    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            # Bewege Servo
            self.servo_controller.move_servo(servo_id, direction)
            
            # Aktualisiere LED-Status auf "moving" (gelb)
            led_tag = f'led_{servo_id}'
            led_items = self.winfo_children()[0].winfo_children()[0].winfo_children()[2].find_withtag(led_tag)
            if led_items:
                self.winfo_children()[0].winfo_children()[0].winfo_children()[2].itemconfig(led_items[0], fill='yellow')
            
            # Aktualisiere Position Label
            if str(servo_id) in self.position_labels:
                text = "Links" if direction == 'left' else "Rechts"
                self.position_labels[str(servo_id)].config(text=text)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {e}")
            # Setze LED auf rot bei Fehler
            led_tag = f'led_{servo_id}'
            led_items = self.winfo_children()[0].winfo_children()[0].winfo_children()[2].find_withtag(led_tag)
            if led_items:
                self.winfo_children()[0].winfo_children()[0].winfo_children()[2].itemconfig(led_items[0], fill='red')
            # Setze Position Label auf Error
            if str(servo_id) in self.position_labels:
                self.position_labels[str(servo_id)].config(text="Error")
            messagebox.showerror("Fehler", str(e))
            
    def update_servo_status(self):
        """Aktualisiert die Status-LEDs und Position Labels aller Servos"""
        try:
            for i in range(16):  # Für alle 16 Servos
                # Hole Servo-Status
                state = self.servo_controller.servo_states.get(str(i), {})
                status = state.get('status', 'unknown')
                position = state.get('position', None)
                
                # Aktualisiere LED
                led_tag = f'led_{i}'
                led_items = self.winfo_children()[0].winfo_children()[0].winfo_children()[2].find_withtag(led_tag)
                if led_items:
                    led = led_items[0]
                    # Bestimme LED-Farbe basierend auf Status
                    color = {
                        'initialized': 'green',  # Servo ist initialisiert
                        'moving': 'yellow',      # Servo bewegt sich gerade
                        'error': 'red',          # Fehler aufgetreten
                        'unknown': 'gray'        # Status unbekannt
                    }.get(status, 'gray')
                    self.winfo_children()[0].winfo_children()[0].winfo_children()[2].itemconfig(led, fill=color)
                
                # Aktualisiere Position Label
                if str(i) in self.position_labels:
                    if status == 'error':
                        text = "Error"
                    elif position == 'left':
                        text = "Links"
                    elif position == 'right':
                        text = "Rechts"
                    else:
                        text = "---"
                    self.position_labels[str(i)].config(text=text)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Status-LEDs: {e}")
            
        # Plane nächste Aktualisierung in 1 Sekunde
        self.after(1000, self.update_servo_status)
        
    def create_calibration_tab(self, parent):
        """Erstellt den Kalibrierungs-Tab"""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Servo-Auswahl
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_frame, text="Servo auswählen:").pack(side=tk.LEFT, padx=5)
        servo_select = ttk.Combobox(select_frame, 
                                  textvariable=self.cal_servo_var,
                                  values=[f"Servo {i+1}" for i in range(16)],
                                  width=15,
                                  state="readonly")
        servo_select.pack(side=tk.LEFT, padx=5)
        
        # Start-Button
        ttk.Button(frame, text="Kalibrierung starten",
                  command=self.show_calibration_dialog).pack(pady=10)
                  
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
                raise Exception(f"Servo {self.current_servo} nicht verfügbar (kein zweites Board)")
            
            # Hole aktuelle Konfiguration oder setze Standardwerte
            config = self.servo_controller.config.get(str(self.current_servo), {})
            self.left_angle = float(config.get('left_angle', 30.0))   # Standardwert 30.0° für links
            self.right_angle = float(config.get('right_angle', 150.0))  # Standardwert 150.0° für rechts
            
            self.logger.info(f"Kalibrierung für Servo {self.current_servo + 1}: Links={self.left_angle}°, Rechts={self.right_angle}°")
            
            # Erstelle Kalibrierungsfenster
            self.cal_window = tk.Toplevel(self)
            self.cal_window.title(f"Kalibrierung Servo {self.current_servo + 1}")
            self.cal_window.geometry("400x300")  # Größeres Fenster
            self.cal_window.resizable(False, False)
            
            # Hauptframe mit Padding
            main_frame = ttk.Frame(self.cal_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Info-Label
            ttk.Label(main_frame, 
                     text="Stellen Sie die Positionen mit den Pfeiltasten ein",
                     wraplength=350,
                     justify=tk.CENTER).pack(pady=(0,20))
            
            # Linke Position
            left_frame = ttk.LabelFrame(main_frame, text="Linke Position", padding="10")
            left_frame.pack(fill=tk.X, pady=(0,10))
            
            # Winkel-Anzeige und Steuerung in einer Reihe
            left_ctrl = ttk.Frame(left_frame)
            left_ctrl.pack(fill=tk.X)
            ttk.Label(left_ctrl, text="Winkel:", width=8).pack(side=tk.LEFT)
            
            # Label für linken Winkel
            self.left_angle_label = ttk.Label(left_ctrl, text=f"{int(self.left_angle)}°", width=5)
            self.left_angle_label.pack(side=tk.LEFT)
            
            # Buttons rechtsbündig
            left_btn_frame = ttk.Frame(left_ctrl)
            left_btn_frame.pack(side=tk.RIGHT)
            ttk.Button(left_btn_frame, text="◄◄", width=3, command=lambda: self.adjust_left(-10)).pack(side=tk.LEFT, padx=1)
            ttk.Button(left_btn_frame, text="◄", width=3, command=lambda: self.adjust_left(-1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(left_btn_frame, text="►", width=3, command=lambda: self.adjust_left(1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(left_btn_frame, text="►►", width=3, command=lambda: self.adjust_left(10)).pack(side=tk.LEFT, padx=1)
            
            # Rechte Position
            right_frame = ttk.LabelFrame(main_frame, text="Rechte Position", padding="10")
            right_frame.pack(fill=tk.X, pady=(0,10))
            
            # Winkel-Anzeige und Steuerung in einer Reihe
            right_ctrl = ttk.Frame(right_frame)
            right_ctrl.pack(fill=tk.X)
            ttk.Label(right_ctrl, text="Winkel:", width=8).pack(side=tk.LEFT)
            
            # Label für rechten Winkel
            self.right_angle_label = ttk.Label(right_ctrl, text=f"{int(self.right_angle)}°", width=5)
            self.right_angle_label.pack(side=tk.LEFT)
            
            # Buttons rechtsbündig
            right_btn_frame = ttk.Frame(right_ctrl)
            right_btn_frame.pack(side=tk.RIGHT)
            ttk.Button(right_btn_frame, text="◄◄", width=3, command=lambda: self.adjust_right(-10)).pack(side=tk.LEFT, padx=1)
            ttk.Button(right_btn_frame, text="◄", width=3, command=lambda: self.adjust_right(-1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(right_btn_frame, text="►", width=3, command=lambda: self.adjust_right(1)).pack(side=tk.LEFT, padx=1)
            ttk.Button(right_btn_frame, text="►►", width=3, command=lambda: self.adjust_right(10)).pack(side=tk.LEFT, padx=1)
            
            # Speichern Button
            save_frame = ttk.Frame(main_frame)
            save_frame.pack(fill=tk.X, pady=10)
            ttk.Button(save_frame, 
                      text="Einstellungen speichern",
                      command=self.save_calibration).pack(expand=True)
            
            # Setze Servo auf Mittelposition
            middle_angle = (self.left_angle + self.right_angle) / 2
            self.logger.info(f"Setze Servo {self.current_servo} auf Mittelposition ({middle_angle}°)")
            if self.current_servo < 8:
                self.servo_controller.kit1.servo[self.current_servo].angle = middle_angle
            else:
                self.servo_controller.kit2.servo[self.current_servo-8].angle = middle_angle
            
            # Mache Fenster modal
            self.cal_window.transient(self)
            self.cal_window.grab_set()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen des Kalibrierungsdialogs: {e}")
            messagebox.showerror("Fehler", str(e))
            if hasattr(self, 'cal_window'):
                self.cal_window.destroy()
                
    def create_track_tab(self, parent):
        """Erstellt den Gleiskarten-Tab"""
        # Hauptframe
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Platzhalter-Label
        ttk.Label(main_frame, text="Gleiskarte wird in zukünftiger Version implementiert").pack(pady=20)

    def create_info_tab(self, parent): 
        """Erstellt den Info & Settings Tab"""
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = """Entwickelt von: EinsPommes
Website: Chill-zone.xyz
Version: 1.2
 2025 EinsPommes

Weboberfläche:
http://raspberrypi:5000

Steuerung der Servos:
- Links/Rechts Buttons zum Steuern
- Status wird farblich angezeigt
- Kalibrierung über Settings möglich

Weboberfläche:
- Zugriff über Browser mit obiger URL
- Gleiche Funktionen wie GUI
- Automatische Aktualisierung"""
        
        ttk.Label(content_frame, text=info_text, justify=tk.LEFT).pack(side='left', anchor='nw')
        
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(side='right', anchor='ne')
        
        update_button = ttk.Button(button_frame, text="Update", command=self.check_for_updates)
        update_button.pack(pady=2)
        
        quit_button = ttk.Button(button_frame, text="Beenden", command=self.quit_application)
        quit_button.pack(pady=2)
    
    def on_servo_selected(self, event):
        if not self.servo_var.get():
            return
            
        servo_id = int(self.servo_var.get().split()[1]) - 1
        config = self.servo_controller.get_servo_config(servo_id)
        
        self.left_value.set(f"{config['left_angle']:.1f}")
        self.right_value.set(f"{config['right_angle']:.1f}")
        self.speed_value.set(f"{config['speed']:.1f}")
    
    def update_left_angle(self, *args):
        """Aktualisiert den linken Winkel in der Konfiguration"""
        if not self.servo_var.get():
            return
        try:
            value = self.left_value.get()
            if value and value != ".":
                angle = float(value)
                if 2.5 <= angle <= 12.5:
                    servo_id = int(self.servo_var.get().split()[1]) - 1
                    # Nur Konfiguration aktualisieren, keine Bewegung
                    self.servo_controller.servo_config[servo_id]['left_angle'] = angle
        except ValueError:
            pass

    def update_right_angle(self, *args):
        """Aktualisiert den rechten Winkel in der Konfiguration"""
        if not self.servo_var.get():
            return
        try:
            value = self.right_value.get()
            if value and value != ".":
                angle = float(value)
                if 2.5 <= angle <= 12.5:
                    servo_id = int(self.servo_var.get().split()[1]) - 1
                    # Nur Konfiguration aktualisieren, keine Bewegung
                    self.servo_controller.servo_config[servo_id]['right_angle'] = angle
        except ValueError:
            pass

    def update_speed(self, *args):
        """Aktualisiert die Geschwindigkeit in der Konfiguration"""
        if not self.servo_var.get():
            return
        try:
            value = self.speed_value.get()
            if value and value != ".":
                speed = float(value)
                if 0.1 <= speed <= 1.0:
                    servo_id = int(self.servo_var.get().split()[1]) - 1
                    # Nur Konfiguration aktualisieren, keine Bewegung
                    self.servo_controller.servo_config[servo_id]['speed'] = speed
        except ValueError:
            pass

    def validate_input(self, value):
        """Validiert die Eingabe der Zahlenfelder"""
        if value == "" or value == ".":
            return True
        try:
            float_val = float(value)
            # Für Winkel (Duty-Cycle)
            if len(value) <= 4 and float_val >= 2.5 and float_val <= 12.5:
                return True
            # Für Geschwindigkeit
            elif len(value) <= 3 and float_val >= 0.1 and float_val <= 1.0:
                return True
            return False
        except ValueError:
            return False

    def validate_and_save_config(self):
        """Validiert und speichert die Servo-Konfiguration"""
        try:
            # Aktuelle Werte aus den Eingabefeldern holen
            servo_id = self.servo_var.get()
            if not servo_id:
                return
                
            servo_id = int(servo_id.split()[1]) - 1  # "Servo X" -> X-1
            
            try:
                left = float(self.left_value.get())
                right = float(self.right_value.get())
                speed = float(self.speed_value.get())
                
                # Validiere die Werte
                if not (2.5 <= left <= 12.5):
                    messagebox.showerror("Fehler", f"Ungültiger Winkel für Position A (2.5-12.5): {left}")
                    return False
                    
                if not (2.5 <= right <= 12.5):
                    messagebox.showerror("Fehler", f"Ungültiger Winkel für Position B (2.5-12.5): {right}")
                    return False
                    
                if not (0.1 <= speed <= 1.0):
                    messagebox.showerror("Fehler", f"Ungültige Geschwindigkeit (0.1-1.0): {speed}")
                    return False
                
                # Speichere die Konfiguration
                self.servo_controller.set_servo_config(
                    servo_id,
                    left_angle=left,
                    right_angle=right,
                    speed=speed
                )
                return True
                
            except ValueError:
                messagebox.showerror("Fehler", "Bitte geben Sie gültige Zahlen ein")
                return False
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern der Konfiguration: {str(e)}")
            return False

    def test_position(self, position):
        """Testet eine Servo-Position"""
        try:
            # Erst Konfiguration speichern
            if not self.validate_and_save_config():
                return
                
            # Servo-ID ermitteln
            servo_id = int(self.servo_var.get().split()[1]) - 1
            
            # Position setzen (synchron)
            self.servo_controller.set_servo_position_sync(servo_id, position)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Testen der Position: {str(e)}")

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
        """Speichert die aktuelle Konfiguration"""
        if not self.validate_and_save_config():
            return
            
        if self.servo_controller.save_config():
            messagebox.showinfo("Erfolg", "Konfiguration erfolgreich gespeichert")
        else:
            messagebox.showerror("Fehler", "Fehler beim Speichern der Konfiguration")
            
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
                
    def create_servo_frame(self, parent, servo_id):
        """Erstellt einen Frame für einen Servo mit Steuerung und Status"""
        servo_frame = ttk.LabelFrame(parent, text=f"Servo {servo_id + 1}")
        
        # Status-Anzeige
        status_frame = ttk.Frame(servo_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # LED
        canvas = tk.Canvas(status_frame, width=20, height=20)
        canvas.pack(side=tk.LEFT, padx=2)
        led = canvas.create_oval(5, 5, 15, 15, fill='gray')
        
        # Positions-Label
        pos_label = ttk.Label(status_frame, text="--")
        pos_label.pack(side=tk.LEFT, padx=5)
        
        # Steuerungsbuttons
        button_frame = ttk.Frame(servo_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Links-Button
        left_btn = ttk.Button(button_frame, text="←", width=3,
                            command=lambda: self.move_servo(servo_id, 'left'))
        left_btn.pack(side=tk.LEFT, padx=2)
        
        # Rechts-Button
        right_btn = ttk.Button(button_frame, text="→", width=3,
                            command=lambda: self.move_servo(servo_id, 'right'))
        right_btn.pack(side=tk.LEFT, padx=2)
        
        return servo_frame, canvas, led, pos_label

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
                
                # Hole Position vom Controller
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
                    label=f'Servo {i}',
                    command=lambda x=f'Servo {i}': self.servo_var.set(x),
                    foreground=fg
                )
            
            # Setze Auswahl zurück wenn möglich
            if current in [f'Servo {i}' for i in range(16)]:
                self.servo_var.set(current)
            else:
                self.servo_var.set('Servo 0')
                
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
            
            self.logger.info(f"Test: Servo {servo_id} auf {angle}° ({direction}) gesetzt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Testen: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Testen: {str(e)}")
            
    def create_automation_tab(self, parent):
        """Erstellt den Automation-Tab"""
        # Hauptframe
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Muster Frame
        pattern_frame = ttk.LabelFrame(main_frame, text="Automatik-Muster", padding="10")
        pattern_frame.pack(fill='x', expand=True, padx=10, pady=10)
        
        # Muster Auswahl
        patterns = ["Links → Rechts", "Rechts → Links", "Links ↔ Rechts", "Zufällig"]
        self.pattern_var.set(patterns[0])
        ttk.Combobox(pattern_frame, 
                    textvariable=self.pattern_var,
                    values=patterns,
                    state='readonly',
                    width=20).pack(fill='x', pady=5)
        
        # Geschwindigkeit Frame
        speed_frame = ttk.LabelFrame(main_frame, text="Geschwindigkeit", padding="10")
        speed_frame.pack(fill='x', expand=True, padx=10, pady=10)
        
        # Geschwindigkeits-Slider
        ttk.Scale(speed_frame,
                 from_=0.1,
                 to=2.0,
                 variable=self.speed_var,
                 orient=tk.HORIZONTAL).pack(fill='x', pady=5)
        
        # Button Frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', expand=True, padx=10, pady=10)
        
        # Start/Stop Buttons
        self.start_btn = ttk.Button(btn_frame, 
                                  text="Start",
                                  width=15,
                                  command=self.start_automation)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame,
                                 text="Stop",
                                 width=15,
                                 command=self.stop_automation,
                                 state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Automation Status
        self.automation_running = False
        self.automation_task = None
        
    def start_automation(self):
        """Startet die Automation"""
        try:
            # Pattern-Name aus der Auswahl ermitteln
            pattern_display = self.pattern_var.get()
            pattern = self.patterns.get(pattern_display)
            
            if not pattern:
                raise ValueError(f"Ungültiges Muster: {pattern_display}")
            
            # Automation starten
            self.automation_controller.start_automation(pattern)
            
            # Buttons aktualisieren
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten der Automation: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Starten der Automation: {str(e)}")
            
    def stop_automation(self):
        """Stoppt die Automation"""
        try:
            self.automation_controller.stop_automation()
            
            # Buttons aktualisieren
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen der Automation: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Stoppen der Automation: {str(e)}")

    def move_selected_servo(self, direction):
        """Bewegt den ausgewählten Servo"""
        try:
            # Hole Servo-ID
            servo_str = self.servo_var.get()
            if not servo_str:
                messagebox.showwarning("Warnung", "Bitte wählen Sie einen Servo aus")
                return
                
            servo_id = int(servo_str.split()[1]) - 1  # "Servo 1" -> 0
            
            # Bewege Servo
            success = self.servo_controller.move_servo(servo_id, direction)
            if not success:
                self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}")
                
            # Sofort aktualisieren
            self.update_all_status()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen des Servos: {e}")
            messagebox.showerror("Fehler", str(e))

    def adjust_left(self, delta):
        """Passt den linken Winkel an"""
        try:
            # Berechne neuen Winkel
            new_angle = self.left_angle + delta
            
            # Prüfe Grenzen
            if not (0 <= new_angle <= 180):
                return
                
            # Aktualisiere Winkel
            self.left_angle = new_angle
            
            # Aktualisiere Label
            if hasattr(self, 'left_angle_label'):
                self.left_angle_label.config(text=f"{int(new_angle)}°")
            
            # Bewege Servo zur Vorschau
            servo_str = self.cal_servo_var.get()
            if servo_str:
                servo_id = int(servo_str.split()[1]) - 1
                self.servo_controller.set_servo_angle(servo_id, new_angle)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Anpassen des linken Winkels: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def adjust_right(self, delta):
        """Passt den rechten Winkel an"""
        try:
            # Berechne neuen Winkel
            new_angle = self.right_angle + delta
            
            # Prüfe Grenzen
            if not (0 <= new_angle <= 180):
                return
                
            # Aktualisiere Winkel
            self.right_angle = new_angle
            
            # Aktualisiere Label
            if hasattr(self, 'right_angle_label'):
                self.right_angle_label.config(text=f"{int(new_angle)}°")
            
            # Bewege Servo zur Vorschau
            servo_str = self.cal_servo_var.get()
            if servo_str:
                servo_id = int(servo_str.split()[1]) - 1
                self.servo_controller.set_servo_angle(servo_id, new_angle)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Anpassen des rechten Winkels: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def save_calibration(self):
        """Speichert die Kalibrierung"""
        try:
            # Hole Servo-Nummer
            servo_str = self.cal_servo_var.get()
            if not servo_str:
                messagebox.showwarning("Warnung", "Bitte wählen Sie einen Servo aus")
                return
                
            servo_id = int(servo_str.split()[1]) - 1
            
            # Validiere Winkel
            if not (0 <= self.left_angle <= 180 and 0 <= self.right_angle <= 180):
                raise ValueError("Winkel müssen zwischen 0° und 180° liegen")
                
            if abs(self.right_angle - self.left_angle) < 10:
                raise ValueError("Differenz zwischen rechtem und linkem Winkel muss mindestens 10° betragen")
                
            # Speichere Konfiguration
            self.servo_controller.config[str(servo_id)] = {
                'left_angle': self.left_angle,
                'right_angle': self.right_angle
            }
            self.servo_controller.save_config()
            
            self.logger.info(f"Kalibrierung für Servo {servo_id + 1} gespeichert: Links={self.left_angle}°, Rechts={self.right_angle}°")
            messagebox.showinfo("Erfolg", "Kalibrierung erfolgreich gespeichert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Kalibrierung: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def test_calibration(self, direction):
        """Testet die Kalibrierung für eine Richtung"""
        try:
            servo_str = self.cal_servo_var.get()
            if not servo_str:
                return
                
            servo_id = int(servo_str.split()[1]) - 1
            self.servo_controller.move_servo(servo_id, direction)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Testen der Kalibrierung: {e}")
            messagebox.showerror("Fehler", str(e))

    def create_servo_controls(self):
        """Erstellt die Servo-Steuerungselemente"""
        servos_frame = ttk.LabelFrame(self.control_tab, text="Servo-Steuerung")
        servos_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Dictionary für LED- und Label-Referenzen
        self.servo_leds = {}
        self.position_labels = {}
        
        # Erstelle Steuerelemente für jeden Servo
        for i in range(16):
            # Frame für diesen Servo
            servo_frame = ttk.Frame(servos_frame)
            servo_frame.grid(row=i//4, column=i%4, padx=5, pady=5, sticky='nsew')
            
            # Servo-Nummer und LED in einem Frame
            header_frame = ttk.Frame(servo_frame)
            header_frame.pack(side='top')
            
            # Servo-Nummer
            ttk.Label(header_frame, text=f"Servo {i+1}").pack(side='left', padx=(0,5))
            
            # Status-LED
            led_canvas = tk.Canvas(header_frame, width=10, height=10)
            led_canvas.pack(side='left')
            led = led_canvas.create_oval(1, 1, 9, 9, fill='gray')
            self.servo_leds[str(i)] = {
                'canvas': led_canvas,
                'led': led
            }
            
            # Position Label mit Rahmen
            pos_frame = ttk.Frame(servo_frame, relief='groove', borderwidth=1)
            pos_frame.pack(side='top', pady=2, fill='x')
            pos_label = ttk.Label(pos_frame, text="---", width=10, anchor='center')
            pos_label.pack(pady=1)
            self.position_labels[str(i)] = pos_label
            
            # Button-Frame
            btn_frame = ttk.Frame(servo_frame)
            btn_frame.pack(side='top', pady=2)
            
            # Links-Button
            ttk.Button(btn_frame, 
                      text="←", 
                      width=2,
                      command=lambda s=i: self.move_servo(s, 'left')).pack(side='left', padx=1)
            
            # Rechts-Button
            ttk.Button(btn_frame, 
                      text="→", 
                      width=2,
                      command=lambda s=i: self.move_servo(s, 'right')).pack(side='left', padx=1)
            
        # Grid-Konfiguration
        for i in range(4):
            servos_frame.grid_rowconfigure(i, weight=1)
            servos_frame.grid_columnconfigure(i, weight=1)

    def update_position_labels(self):
        """Aktualisiert alle Positions-Labels"""
        for servo_id in range(16):
            if str(servo_id) in self.position_labels:
                try:
                    status = self.servo_controller.get_servo_status(servo_id)
                    if status['error']:
                        text = "Fehler"
                    elif not status['initialized']:
                        text = "---"
                    else:
                        position = status['position']
                        if position == 'left':
                            text = "Links"
                        elif position == 'right':
                            text = "Rechts"
                        else:
                            text = "---"
                    self.position_labels[str(servo_id)].config(text=text)
                except Exception as e:
                    self.logger.error(f"Fehler beim Aktualisieren des Labels für Servo {servo_id}: {e}")

    def move_servo(self, servo_id, direction):
        """Bewegt einen bestimmten Servo"""
        try:
            # Bewege Servo
            self.servo_controller.move_servo(servo_id, direction)
            
            # Aktualisiere LED und Label
            servo_status = self.servo_controller.get_servo_status(servo_id)
            
            # LED-Farbe basierend auf Status setzen
            if str(servo_id) in self.servo_leds:
                canvas = self.servo_leds[str(servo_id)]['canvas']
                led = self.servo_leds[str(servo_id)]['led']
                
                if servo_status['error']:
                    color = 'red'
                elif servo_status['initialized']:
                    if direction == 'right':
                        color = 'yellow'
                    else:
                        color = 'green'
                else:
                    color = 'gray'
                    
                canvas.itemconfig(led, fill=color)
                
            # Position Label aktualisieren
            if str(servo_id) in self.position_labels:
                text = "Rechts" if direction == 'right' else "Links"
                self.position_labels[str(servo_id)].config(text=text)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {e}")
            # LED auf Rot bei Fehler
            if str(servo_id) in self.servo_leds:
                canvas = self.servo_leds[str(servo_id)]['canvas']
                led = self.servo_leds[str(servo_id)]['led']
                canvas.itemconfig(led, fill='red')
            messagebox.showerror("Fehler", str(e))

def main():
    try:
        root = WeichensteuerungGUI()
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Starten: {str(e)}")
        raise

if __name__ == "__main__":
    main()