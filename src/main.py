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
        """Initialisiert die GUI"""
        super().__init__()
        
        # Logger initialisieren
        self.logger = logging.getLogger('GUI')
        self.logger.setLevel(logging.DEBUG)
        
        # Fenster-Einstellungen
        self.title("Weichensteuerung")
        self.geometry("800x600")
        
        try:
            # Servo Controller initialisieren
            self.servo_controller = ServoKitController()
            
            # Automation Controller initialisieren
            self.automation_controller = AutomationController(self.servo_controller)
            
            # Status-Variablen
            self.servo_var = tk.StringVar()
            self.servo_leds = {}  # Canvas-Objekte für LEDs
            self.position_labels = {}  # Labels für Positionen
            
            # Kalibrierungs-Variablen
            self.current_servo = None
            self.left_angle = None
            self.right_angle = None
            
            # GUI erstellen
            self.create_gui()
            
            # Status-Update Timer starten
            self.after(1000, self.update_servo_status)
            
            # Test-Bewegung durchführen
            self.logger.info("Führe Test-Bewegung durch...")
            self.servo_controller.move_servo(0, 'left')
            time.sleep(0.5)
            self.servo_controller.move_servo(0, 'right')
            time.sleep(0.5)
            self.servo_controller.move_servo(0, 'left')
            self.logger.info("Test-Bewegung erfolgreich")
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung: {e}")
            messagebox.showerror("Fehler", 
                               "Fehler bei der Initialisierung der Weichensteuerung.\n" +
                               "Bitte prüfen Sie die Verbindung zum Servo-Controller.\n\n" +
                               f"Fehler: {str(e)}")
            self.destroy()

    def create_gui(self):
        """Erstellt die GUI"""
        # Notebook für Tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Steuerungs-Tab
        control_tab = ttk.Frame(notebook)
        notebook.add(control_tab, text="Steuerung")
        self.create_control_tab(control_tab)
        
        # Gleiskarte-Tab
        track_tab = ttk.Frame(notebook)
        notebook.add(track_tab, text="Gleiskarte")
        self.create_track_tab(track_tab)
        
        # Kalibrierungs-Tab
        calibration_tab = ttk.Frame(notebook)
        notebook.add(calibration_tab, text="Kalibrierung")
        self.create_calibration_tab(calibration_tab)
        
        # Automation-Tab
        automation_tab = ttk.Frame(notebook)
        notebook.add(automation_tab, text="Automation")
        self.create_automation_tab(automation_tab)
        
        # Info-Tab
        info_tab = ttk.Frame(notebook)
        notebook.add(info_tab, text="Info")
        self.create_info_tab(info_tab)
        
        # Fenster-Schließen-Handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_control_tab(self, parent):
        """Erstellt den Steuerungs-Tab"""
        # Hauptframe mit Padding
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Servo Status Frame
        status_frame = ttk.LabelFrame(main_frame, text="Servo Status", padding="10")
        status_frame.pack(fill=tk.X, padx=5, pady=(0,10))
        
        # Grid für Servo-Status (4x4)
        for row in range(4):
            for col in range(4):
                servo_id = row * 4 + col
                frame = ttk.Frame(status_frame)
                frame.grid(row=row, column=col, padx=5, pady=2)
                
                # Status-LED
                canvas = tk.Canvas(frame, width=15, height=15)
                canvas.pack(side=tk.TOP, pady=(0,2))
                self.servo_leds[str(servo_id)] = {'canvas': canvas, 'led': canvas.create_oval(2, 2, 13, 13, fill='orange')}
                
                # Servo-Label
                ttk.Label(frame, text=f"Servo {servo_id + 1}").pack(side=tk.TOP)
                
                # Position-Label
                self.position_labels[str(servo_id)] = ttk.Label(frame, text="---")
                self.position_labels[str(servo_id)].pack(side=tk.TOP)
        
        # Servo Steuerung Frame
        control_frame = ttk.LabelFrame(main_frame, text="Servo Steuerung", padding="10")
        control_frame.pack(fill=tk.X, padx=5)
        
        # Servo-Auswahl und Steuerung in einer Reihe
        ctrl_row = ttk.Frame(control_frame)
        ctrl_row.pack(fill=tk.X)
        
        # Servo Auswahl
        select_frame = ttk.Frame(ctrl_row)
        select_frame.pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(select_frame, text="Servo:").pack(side=tk.LEFT, padx=(0,5))
        servo_select = ttk.Combobox(select_frame, 
                                  textvariable=self.servo_var,
                                  values=[f"Servo {i+1}" for i in range(16)],
                                  state="readonly",
                                  width=10)
        servo_select.pack(side=tk.LEFT)
        servo_select.set("Servo 1")  # Standardauswahl
        
        # Steuerungsbuttons
        btn_frame = ttk.Frame(ctrl_row)
        btn_frame.pack(side=tk.RIGHT)
        
        ttk.Button(btn_frame, 
                  text="Links",
                  width=10,
                  command=lambda: self.move_servo(int(self.servo_var.get().split()[1]) - 1, 'left')).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(btn_frame,
                  text="Rechts",
                  width=10,
                  command=lambda: self.move_servo(int(self.servo_var.get().split()[1]) - 1, 'right')).pack(side=tk.LEFT, padx=5)

    def update_servo_status(self):
        """Aktualisiert den Status aller Servos"""
        try:
            # Aktualisiere Status für jeden Servo
            for servo_id in range(16):  # Maximal 16 Servos pro Board
                if str(servo_id) not in self.servo_leds:
                    continue
                    
                # Hole Servo-Status
                state = self.servo_controller.servo_states.get(str(servo_id))
                if not state:
                    continue
                    
                frame_data = self.servo_leds[str(servo_id)]
                
                # Aktualisiere LED-Farbe
                if state.get('error', False):
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='red')
                elif time.time() - state.get('last_move', 0) < 0.5:  # Bewegung in den letzten 0.5 Sekunden
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='yellow')
                elif state.get('position') in ['left', 'right']:  # Position bekannt
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='green')
                else:
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='gray')
                    
                # Aktualisiere Positions-Label
                if str(servo_id) in self.position_labels:
                    position = state.get('position', '')
                    if position in ['left', 'right']:
                        self.position_labels[str(servo_id)].config(text=position.capitalize())
                    else:
                        self.position_labels[str(servo_id)].config(text='?')
                        
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Servo-Status: {e}")
            
        # Plane nächstes Update
        self.after(500, self.update_servo_status)

    def adjust_left(self, delta):
        """Passt den linken Winkel an"""
        try:
            self.logger.debug(f"Passe linken Winkel an: aktuell={self.left_angle}, delta={delta}")
            
            # Berechne neuen Winkel
            new_angle = float(self.left_angle) + delta
            
            # Prüfe Grenzen
            if new_angle < 0 or new_angle > 180:
                self.logger.debug(f"Neuer Winkel {new_angle}° außerhalb der Grenzen")
                return
                
            # Aktualisiere Winkel
            self.left_angle = float(new_angle)  # Explizit als float speichern
            self.logger.debug(f"Neuer linker Winkel: {self.left_angle}°")
            
            # Aktualisiere Label
            if hasattr(self, 'left_angle_label'):
                self.left_angle_label['text'] = f"{int(self.left_angle)}°"
            
            # Bewege Servo
            if self.current_servo < 8:
                self.servo_controller.kit1.servo[self.current_servo].angle = self.left_angle
            else:
                self.servo_controller.kit2.servo[self.current_servo-8].angle = self.left_angle
                
        except Exception as e:
            self.logger.error(f"Fehler beim Anpassen des linken Winkels: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def adjust_right(self, delta):
        """Passt den rechten Winkel an"""
        try:
            self.logger.debug(f"Passe rechten Winkel an: aktuell={self.right_angle}, delta={delta}")
            
            # Berechne neuen Winkel
            new_angle = float(self.right_angle) + delta
            
            # Prüfe Grenzen
            if new_angle < 0 or new_angle > 180:
                self.logger.debug(f"Neuer Winkel {new_angle}° außerhalb der Grenzen")
                return
                
            # Aktualisiere Winkel
            self.right_angle = float(new_angle)  # Explizit als float speichern
            self.logger.debug(f"Neuer rechter Winkel: {self.right_angle}°")
            
            # Aktualisiere Label
            if hasattr(self, 'right_angle_label'):
                self.right_angle_label['text'] = f"{int(self.right_angle)}°"
            
            # Bewege Servo
            if self.current_servo < 8:
                self.servo_controller.kit1.servo[self.current_servo].angle = self.right_angle
            else:
                self.servo_controller.kit2.servo[self.current_servo-8].angle = self.right_angle
                
        except Exception as e:
            self.logger.error(f"Fehler beim Anpassen des rechten Winkels: {e}")
            messagebox.showerror("Fehler", str(e))
            
    def save_calibration(self):
        """Speichert die Kalibrierung"""
        try:
            self.logger.debug(f"Starte Speicherung der Kalibrierung für Servo {self.current_servo}")
            
            # Prüfe ob die Winkel gültig sind
            if not hasattr(self, 'left_angle') or not hasattr(self, 'right_angle'):
                raise ValueError("Keine Winkel zum Speichern vorhanden")
                
            # Prüfe ob die Winkel numerisch sind
            try:
                left = float(self.left_angle)
                right = float(self.right_angle)
            except (ValueError, TypeError):
                raise ValueError("Ungültige Winkel-Werte")
                
            # Prüfe Grenzen
            if left < 0 or left > 180 or right < 0 or right > 180:
                raise ValueError("Winkel müssen zwischen 0° und 180° liegen")
                
            # Erstelle Konfiguration
            servo_config = {
                'left_angle': left,
                'right_angle': right,
                'speed': 0.5  # Fester Wert
            }
            
            self.logger.debug(f"Neue Konfiguration: {servo_config}")
            
            # Aktualisiere Konfiguration im Controller
            self.servo_controller.config[str(self.current_servo)] = servo_config
            
            # Speichere in Datei
            self.logger.debug("Speichere Konfiguration in Datei...")
            self.servo_controller.save_config()
            self.logger.debug("Konfiguration erfolgreich gespeichert")
            
            # Schließe Fenster
            if hasattr(self, 'cal_window'):
                self.cal_window.destroy()
            
            # Bestätige Speicherung
            messagebox.showinfo("Erfolg", 
                f"Kalibrierung für Servo {self.current_servo + 1} gespeichert:\n" +
                f"Linker Anschlag: {int(left)}°\n" +
                f"Rechter Anschlag: {int(right)}°")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Kalibrierung: {e}")
            self.logger.error(f"Debug Info - Attribute: left_angle={hasattr(self, 'left_angle')}, " +
                          f"right_angle={hasattr(self, 'right_angle')}, " +
                          f"current_servo={hasattr(self, 'current_servo')}")
            messagebox.showerror("Fehler", str(e))
            
    def create_map_tab(self, parent):
        # Gleiskarte erstellen
        self.track_map = TrackMap(parent)
        
    def create_calibration_tab(self, parent):
        """Erstellt den Kalibrierungs-Tab"""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Servo-Auswahl
        select_frame = ttk.Frame(frame)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_frame, text="Servo auswählen:").pack(side=tk.LEFT, padx=5)
        servo_select = ttk.Combobox(select_frame, 
                                  textvariable=self.servo_var,
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
            servo_str = self.servo_var.get()
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
            
    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            # Prüfe Parameter
            if not isinstance(servo_id, int):
                raise ValueError(f"Ungültige Servo-ID: {servo_id}")
                
            if direction not in ['left', 'right']:
                raise ValueError(f"Ungültige Richtung: {direction}")
                
            # Bewege Servo
            self.servo_controller.move_servo(servo_id, direction)
            
            # Aktualisiere GUI-Status
            if str(servo_id) in self.position_labels:
                self.position_labels[str(servo_id)].config(text=direction.capitalize())
                
            # Aktualisiere LED-Status
            if str(servo_id) in self.servo_leds:
                frame_data = self.servo_leds[str(servo_id)]
                frame_data['canvas'].itemconfig(frame_data['led'], fill='green')
                
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {e}")
            
            # Aktualisiere LED-Status auf Fehler
            if str(servo_id) in self.servo_leds:
                frame_data = self.servo_leds[str(servo_id)]
                frame_data['canvas'].itemconfig(frame_data['led'], fill='red')
                
            # Zeige Fehlermeldung nur bei echten Fehlern
            if not isinstance(e, ValueError):
                messagebox.showerror("Fehler", f"Fehler beim Bewegen von Servo {servo_id}:\n{str(e)}")
                
    def create_automation_tab(self, parent):
        """Erstellt den Automation-Tab"""
        frame = ttk.Frame(parent, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Muster-Auswahl
        pattern_frame = ttk.LabelFrame(frame, text="Automatik-Muster", padding="5")
        pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Muster definieren
        self.patterns = {
            "Links → Rechts": "left_to_right",
            "Rechts → Links": "right_to_left",
            "Abwechselnd": "alternate",
            "Zufällig": "random"
        }
        
        self.pattern_var = tk.StringVar(value="Links → Rechts")
        pattern_menu = ttk.Combobox(pattern_frame, 
                                  textvariable=self.pattern_var,
                                  values=list(self.patterns.keys()),
                                  state="readonly")
        pattern_menu.pack(fill=tk.X, padx=5, pady=5)
        
        # Geschwindigkeits-Slider
        speed_frame = ttk.LabelFrame(frame, text="Geschwindigkeit", padding="5")
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, 
                              from_=0.1, 
                              to=2.0,
                              variable=self.speed_var,
                              orient=tk.HORIZONTAL)
        speed_scale.pack(fill=tk.X, padx=5, pady=5)
        
        # Start/Stop Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(button_frame, 
                                     text="Start",
                                     command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame,
                                    text="Stop",
                                    command=self.stop_automation,
                                    state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
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
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten der Automation: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Starten der Automation: {str(e)}")
            
    def stop_automation(self):
        """Stoppt die Automation"""
        try:
            self.automation_controller.stop_automation()
            
            # Buttons aktualisieren
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
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
            self.update_servo_status()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen des Servos: {e}")
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