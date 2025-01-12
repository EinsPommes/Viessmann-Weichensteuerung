from pigpio_servo_controller import PiGPIOServoController
from hall_sensor import HallSensor
from automation_controller import AutomationController
from gui import GUI
from track_map import TrackMap
import json
import os
import tkinter as tk
import sys
import subprocess
import logging
from pigpio_servo_controller import PiGPIOServoController
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
from pigpio_servo_controller import PiGPIOServoController
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
from pigpio_servo_controller import PiGPIOServoController

class ServoStatusFrame(ttk.LabelFrame):
    """Frame für detaillierte Servo-Status-Anzeige"""
    def __init__(self, parent, servo_id, controller):
        super().__init__(parent, text=f"Servo {servo_id + 1}")
        self.servo_id = servo_id
        self.controller = controller
        
        # Status-Anzeige
        self.status_indicator = tk.Canvas(self, width=20, height=20)
        self.status_indicator.grid(row=0, column=0, padx=5, pady=5)
        self.status_light = self.status_indicator.create_oval(2, 2, 18, 18, fill='gray')
        
        # Position und Status
        status_frame = ttk.Frame(self)
        status_frame.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        self.position_label = ttk.Label(status_frame, text="Position: --")
        self.position_label.pack(anchor='w')
        
        self.status_label = ttk.Label(status_frame, text="Status: Bereit")
        self.status_label.pack(anchor='w')
        
        # Fehleranzeige
        self.error_label = ttk.Label(self, text="", foreground='red')
        self.error_label.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky='w')
        
    def update_status(self, state):
        """Aktualisiert die Status-Anzeige"""
        # Position
        position = state.get('position', None)
        if position:
            self.position_label.config(text=f"Position: {'Links' if position == 'left' else 'Rechts'}")
        else:
            self.position_label.config(text="Position: --")
        
        # Status und Farbe
        if state.get('is_moving', False):
            self.status_indicator.itemconfig(self.status_light, fill='yellow')
            self.status_label.config(text="Status: In Bewegung")
        elif state.get('last_error'):
            self.status_indicator.itemconfig(self.status_light, fill='red')
            self.status_label.config(text="Status: Fehler")
            self.error_label.config(text=state['last_error'])
        else:
            self.status_indicator.itemconfig(self.status_light, fill='green')
            self.status_label.config(text="Status: Bereit")
            self.error_label.config(text="")

class WeichensteuerungGUI(tk.Tk):
    def __init__(self):
        """Initialisiert die GUI"""
        super().__init__()
        self.title("Weichensteuerung")
        
        # Logger initialisieren
        self.logger = logging.getLogger('GUI')
        
        # Servo-Controller initialisieren
        self.init_servo_controller()
        
        # Servo-Auswahl für Kalibrierung
        self.servo_var = tk.StringVar(value="Servo 1")
        
        # Erstelle Tab-Control
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=True, fill=tk.BOTH)
        
        # Steuerungs-Tab
        control_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(control_tab, text="Steuerung")
        self.create_control_tab(control_tab)
        
        # Gleiskarten-Tab
        map_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(map_tab, text="Gleiskarte")
        self.create_map_tab(map_tab)
        
        # Kalibrierungs-Tab
        config_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(config_tab, text="Kalibrierung")
        self.create_calibration_tab(config_tab)
        
        # Automation-Tab
        automation_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(automation_tab, text="Automation")
        self.create_automation_tab(automation_tab)
        
        # Info-Tab
        info_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(info_tab, text="Info")
        self.create_info_tab(info_tab)
        
        # Status-Update starten
        self.update_status()

    def create_control_tab(self, parent):
        """Erstellt den Steuerungs-Tab"""
        # Hauptframe mit Padding
        control_frame = ttk.Frame(parent, padding="5")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Erstelle 4x4 Grid für Servos
        self.servo_frames = {}  # Speichere Frame-Daten für Updates
        for i in range(16):
            row = i // 4
            col = i % 4
            
            # Servo-Frame
            servo_frame = ttk.LabelFrame(control_frame, text=f"Servo {i+1}")
            servo_frame.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Status-LED
            canvas = tk.Canvas(servo_frame, width=20, height=20)
            canvas.pack(pady=2)
            led = canvas.create_oval(5, 5, 15, 15, fill='gray')
            
            # Positions-Label
            pos_label = ttk.Label(servo_frame, text="?")
            pos_label.pack(pady=2)
            
            # Buttons
            btn_frame = ttk.Frame(servo_frame)
            btn_frame.pack(pady=2)
            
            # Command mit Lambda um Servo-ID zu übergeben
            ttk.Button(btn_frame, text="Links", 
                      command=lambda id=i: self.move_servo(id, 'left')).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_frame, text="Rechts",
                      command=lambda id=i: self.move_servo(id, 'right')).pack(side=tk.LEFT, padx=2)
            
            # Speichere Frame-Daten für Updates
            self.servo_frames[i] = {
                'frame': servo_frame,
                'canvas': canvas,
                'led': led,
                'pos_label': pos_label
            }
            
        # Konfiguriere Grid
        for i in range(4):
            control_frame.columnconfigure(i, weight=1)
            control_frame.rowconfigure(i, weight=1)

    def update_status(self):
        """Aktualisiert den Status aller Servos"""
        try:
            # Aktualisiere Status-LEDs
            for servo_id in range(16):
                frame_data = self.servo_frames.get(servo_id)
                if not frame_data:
                    continue
                    
                # Hole Servo-Status
                state = self.servo_controller.servo_states.get(servo_id, {})
                position = state.get('position')
                last_move = state.get('last_move', 0)
                error = state.get('error', False)
                
                # Aktualisiere Positions-Label
                if position in ['left', 'right']:
                    frame_data['pos_label'].config(text=position.capitalize())
                else:
                    frame_data['pos_label'].config(text='?')
                
                # Aktualisiere LED-Farbe
                if error:
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='red')
                elif time.time() - last_move < 0.5:  # Bewegung in den letzten 0.5 Sekunden
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='yellow')
                elif position in ['left', 'right']:  # Position bekannt
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='green')
                else:
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='gray')
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Status: {e}")
            
        # Plane nächste Aktualisierung
        self.after(500, self.update_status)
        
    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            success = self.servo_controller.move_servo(servo_id, direction)
            if not success:
                self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}")
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id}: {str(e)}")
            
    def create_map_tab(self, parent):
        # Gleiskarte erstellen
        self.track_map = TrackMap(parent)
        
    def create_calibration_tab(self, parent):
        """Erstellt den Kalibrierungs-Tab"""
        frame = ttk.Frame(parent, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Kalibrierungsassistent
        assistant_frame = ttk.LabelFrame(frame, text="Kalibrierungsassistent", padding="5")
        assistant_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Servo-Auswahl
        select_frame = ttk.Frame(assistant_frame)
        select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(select_frame, text="Servo:").pack(side=tk.LEFT, padx=5)
        servo_select = ttk.Combobox(select_frame, 
                                  textvariable=self.servo_var,
                                  values=[f"Servo {i+1}" for i in range(16)],
                                  width=15,
                                  state="readonly")
        servo_select.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(assistant_frame, text="Assistent starten",
                  command=self.start_calibration_assistant).pack(pady=5)
        
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
                    "Es gibt lokale Änderungen. Möchten Sie diese erst speichern?\n"
                    "- Ja: Änderungen werden committet\n"
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
                                         "Es sind Updates verfügbar. Möchten Sie diese jetzt installieren?\n"
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
            
    def update_servo_status(self, servo_id, position=None):
        """Aktualisiert die Statusanzeige für einen Servo"""
        try:
            if not hasattr(self, 'status_labels'):
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
        frame = ttk.LabelFrame(parent, text=f"Servo {servo_id}")
        
        # Status-LED und Position
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # LED-Canvas
        canvas = tk.Canvas(status_frame, width=20, height=20)
        canvas.pack(side=tk.LEFT, padx=2)
        led = canvas.create_oval(2, 2, 18, 18, fill='gray')
        
        # Positions-Label
        pos_label = ttk.Label(status_frame, text="--")
        pos_label.pack(side=tk.LEFT, padx=5)
        
        # Steuerungsbuttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Servo-IDs sind 1-basiert in der GUI, aber 0-basiert im Controller
        btn_left = ttk.Button(btn_frame, text="Links", 
                            command=lambda s=servo_id: self.move_servo(s-1, "left"))
        btn_left.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        btn_right = ttk.Button(btn_frame, text="Rechts", 
                             command=lambda s=servo_id: self.move_servo(s-1, "right"))
        btn_right.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # Speichere Frame-Daten
        self.servo_frames[servo_id] = {
            'frame': frame,
            'canvas': canvas,
            'led': led,
            'pos_label': pos_label,
            'btn_left': btn_left,
            'btn_right': btn_right
        }
        
        return frame

    def update_status(self):
        """Aktualisiert den Status aller Servos"""
        try:
            # Aktualisiere Status-LEDs
            for servo_id in range(16):
                frame_data = self.servo_frames.get(servo_id)
                if not frame_data:
                    continue
                    
                # Hole Servo-Status
                state = self.servo_controller.servo_states.get(servo_id, {})
                position = state.get('position')
                last_move = state.get('last_move', 0)
                error = state.get('error', False)
                
                # Aktualisiere Positions-Label
                if position in ['left', 'right']:
                    frame_data['pos_label'].config(text=position.capitalize())
                else:
                    frame_data['pos_label'].config(text='?')
                
                # Aktualisiere LED-Farbe
                if error:
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='red')
                elif time.time() - last_move < 0.5:  # Bewegung in den letzten 0.5 Sekunden
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='yellow')
                elif position in ['left', 'right']:  # Position bekannt
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='green')
                else:
                    frame_data['canvas'].itemconfig(frame_data['led'], fill='gray')
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Status: {e}")
            
        # Plane nächste Aktualisierung
        self.after(500, self.update_status)
        
    def start_calibration_assistant(self):
        """Startet den Kalibrierungsassistenten"""
        try:
            # Hole ausgewählten Servo
            servo_id = int(self.servo_var.get().split()[1]) - 1
            self.current_servo = servo_id
            
            # Erstelle neues Fenster
            self.window = tk.Toplevel(self)
            self.window.title("Kalibrierungsassistent")
            self.window.geometry("400x300")
            
            # Erstelle Widgets
            frame = ttk.Frame(self.window, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Info-Label
            self.info_label = ttk.Label(frame, text="Stellen Sie den linken Anschlag ein\n"
                                                  "Benutzen Sie die Pfeiltasten zum Einstellen\n"
                                                  "Klicken Sie auf 'Position übernehmen' wenn fertig")
            self.info_label.pack(pady=10)
            
            # Aktueller Winkel
            angle_frame = ttk.Frame(frame)
            angle_frame.pack(pady=5)
            ttk.Label(angle_frame, text="Aktueller Winkel: ").pack(side=tk.LEFT)
            self.angle_label = ttk.Label(angle_frame, text="90°")
            self.angle_label.pack(side=tk.LEFT)
            
            # Anzeige der gespeicherten Werte
            values_frame = ttk.Frame(frame)
            values_frame.pack(pady=5)
            ttk.Label(values_frame, text="Links: ").grid(row=0, column=0, padx=5)
            self.left_value = ttk.Label(values_frame, text="--")
            self.left_value.grid(row=0, column=1, padx=5)
            ttk.Label(values_frame, text="Rechts: ").grid(row=0, column=2, padx=5)
            self.right_value = ttk.Label(values_frame, text="--")
            self.right_value.grid(row=0, column=3, padx=5)
            
            # Steuerungsbuttons
            ctrl_frame = ttk.Frame(frame)
            ctrl_frame.pack(pady=10)
            
            # Fein-Einstellung (1°)
            ttk.Button(ctrl_frame, text="◄", command=lambda: self.adjust_angle(-1)).grid(row=0, column=0, padx=2)
            ttk.Button(ctrl_frame, text="►", command=lambda: self.adjust_angle(1)).grid(row=0, column=1, padx=2)
            
            # Grob-Einstellung (10°)
            ttk.Button(ctrl_frame, text="◄◄", command=lambda: self.adjust_angle(-10)).grid(row=0, column=2, padx=2)
            ttk.Button(ctrl_frame, text="►►", command=lambda: self.adjust_angle(10)).grid(row=0, column=3, padx=2)
            
            # Position übernehmen
            ttk.Button(frame, text="Position übernehmen", 
                      command=self.set_position).pack(pady=10)
            
            # Initialisierung
            self.current_angle = 90  # Startposition
            self.config = {}  # Speicher für die Konfiguration
            self.step = 1  # Schritt 1: Linker Anschlag
            
            # Setze Servo auf 90 Grad
            self.servo_controller.set_servo_angle(servo_id, 90)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Starten des Assistenten: {str(e)}")
            if hasattr(self, 'window'):
                self.window.destroy()

    def adjust_angle(self, delta):
        """Passt den Winkel an"""
        try:
            # Berechne neuen Winkel
            new_angle = round(self.current_angle + delta)  # Runde auf ganze Zahlen
            
            # Prüfe Grenzen
            if not (0 <= new_angle <= 180):
                return
                
            # Setze neuen Winkel
            self.current_angle = new_angle
            self.servo_controller.set_servo_angle(self.current_servo, new_angle)
            self.angle_label.config(text=f"{new_angle}°")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Anpassen des Winkels: {str(e)}")
            
    def set_position(self):
        """Übernimmt die aktuelle Position"""
        try:
            if self.step == 1:
                # Linke Position speichern
                self.config['left_angle'] = self.current_angle
                self.left_value.config(text=f"{self.current_angle}°")
                self.step = 2
                
                # Fahre wieder auf 90 Grad
                self.current_angle = 90
                self.servo_controller.set_servo_angle(self.current_servo, 90)
                self.angle_label.config(text=f"{self.current_angle}°")
                
                self.info_label.config(text="Stellen Sie den rechten Anschlag ein\n"
                                          "Benutzen Sie die Pfeiltasten zum Einstellen\n"
                                          "Klicken Sie auf 'Position übernehmen' wenn fertig")
                
            elif self.step == 2:
                # Rechte Position speichern
                self.config['right_angle'] = self.current_angle
                self.right_value.config(text=f"{self.current_angle}°")
                
                # Speichere Konfiguration
                try:
                    success = self.servo_controller.set_servo_config(self.current_servo, {
                        'left_angle': self.config['left_angle'],
                        'right_angle': self.config['right_angle'],
                        'speed': 0.1  # Langsamere Geschwindigkeit
                    })
                    
                    if success:
                        messagebox.showinfo("Erfolg", 
                                          f"Kalibrierung erfolgreich gespeichert!\n"
                                          f"Linker Anschlag: {self.config['left_angle']}°\n"
                                          f"Rechter Anschlag: {self.config['right_angle']}°")
                        self.window.destroy()
                    else:
                        messagebox.showerror("Fehler", "Fehler beim Speichern der Kalibrierung")
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Setzen der Position: {str(e)}")
            
    def run(self):
        """Startet den Assistenten"""
        self.window.grab_set()  # Modal
        self.window.wait_window()
        
    def init_servo_controller(self):
        """Initialisiert den Servo-Controller"""
        try:
            # Initialisiere pigpio
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise ConnectionError("Konnte nicht mit pigpio daemon verbinden")
                
            # GPIO-Pin-Zuordnung entsprechend der Tabelle
            servo_pins = [
                17,  # Servo 1  - GPIO 17 (Pin 11)
                18,  # Servo 2  - GPIO 18 (Pin 12)
                27,  # Servo 3  - GPIO 27 (Pin 13)
                22,  # Servo 4  - GPIO 22 (Pin 15)
                23,  # Servo 5  - GPIO 23 (Pin 16)
                24,  # Servo 6  - GPIO 24 (Pin 18)
                25,  # Servo 7  - GPIO 25 (Pin 22)
                4,   # Servo 8  - GPIO 4  (Pin 7)
                5,   # Servo 9  - GPIO 5  (Pin 29)
                6,   # Servo 10 - GPIO 6  (Pin 31)
                13,  # Servo 11 - GPIO 13 (Pin 33)
                19,  # Servo 12 - GPIO 19 (Pin 35)
                26,  # Servo 13 - GPIO 26 (Pin 37)
                16,  # Servo 14 - GPIO 16 (Pin 36)
                20,  # Servo 15 - GPIO 20 (Pin 38)
                21   # Servo 16 - GPIO 21 (Pin 40)
            ]
            
            # Initialisiere Servo-Controller
            self.servo_controller = PiGPIOServoController(
                self.pi, 
                servo_pins,
                config_file='config.json'
            )
            
            # Automation-Controller initialisieren
            self.automation_controller = AutomationController(self.servo_controller)
            
            # Hall-Sensor initialisieren
            self.hall_sensor = HallSensor()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren: {e}")
            messagebox.showerror("Fehler", f"Initialisierung fehlgeschlagen: {e}")
            raise

def main():
    try:
        root = WeichensteuerungGUI()
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Starten: {str(e)}")
        raise

if __name__ == "__main__":
    main()