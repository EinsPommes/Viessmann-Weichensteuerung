#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from servo_controller import ServoController
from automation_controller import AutomationController
from track_map import TrackMap
import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler
import subprocess
import shutil
from datetime import datetime

try:
    # Konfiguration laden
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    if not os.path.exists(config_path):
        # Standard-Konfiguration wenn keine Datei existiert
        CONFIG = {
            "display": {
                "width": 1024,
                "height": 600,
                "scaling": 1.4
            },
            "logging": {
                "level": "INFO",
                "backup_count": 5,
                "max_size": 1048576
            }
        }
    else:
        with open(config_path, 'r') as f:
            CONFIG = json.load(f)

    # Logging konfigurieren
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Rotating File Handler einrichten
    log_file = os.path.join(log_dir, 'weichensteuerung.log')
    handler = RotatingFileHandler(
        log_file,
        maxBytes=CONFIG['logging']['max_size'],
        backupCount=CONFIG['logging']['backup_count']
    )
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Logger konfigurieren
    logger = logging.getLogger('weichensteuerung')
    logger.setLevel(CONFIG['logging']['level'])
    logger.addHandler(handler)

except Exception as e:
    print(f"Fehler beim Initialisieren der Konfiguration: {str(e)}")
    sys.exit(1)

class WeichensteuerungGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Weichensteuerung")
        logger.info("Starte Weichensteuerung GUI")
        
        # Fenstergröße aus Konfiguration
        self.root.geometry(f"{CONFIG['display']['width']}x{CONFIG['display']['height']}")
        
        # Skalierung aus Konfiguration
        self.root.tk.call('tk', 'scaling', CONFIG['display']['scaling'])

        # Style konfigurieren
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=(10, 5))
        
        # Notebook (Tab-Container) erstellen
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Tabs erstellen
        self.control_frame = ttk.Frame(self.notebook)
        self.track_frame = ttk.Frame(self.notebook)
        self.calibration_frame = ttk.Frame(self.notebook)
        self.automation_frame = ttk.Frame(self.notebook)
        self.info_frame = ttk.Frame(self.notebook)
        
        # Tabs zum Notebook hinzufügen
        self.notebook.add(self.control_frame, text='Steuerung')
        self.notebook.add(self.track_frame, text='Gleiskarte')
        self.notebook.add(self.calibration_frame, text='Kalibrierung')
        self.notebook.add(self.automation_frame, text='Automation')
        self.notebook.add(self.info_frame, text='Info & Settings')
        
        # Controller initialisieren
        try:
            self.servo_controller = ServoController()
            self.automation_controller = AutomationController(self.servo_controller)
            self.system_status = "Ready"
        except Exception as e:
            self.system_status = f"Error: {str(e)}"
            logger.error(f"Fehler beim Initialisieren der Controller: {str(e)}")
            
        # Tabs erstellen
        self.create_control_tab(self.control_frame)
        self.create_track_tab(self.track_frame)
        self.create_calibration_tab(self.calibration_frame)
        self.create_automation_tab(self.automation_frame)
        self.create_info_tab(self.info_frame)
        
        # Grid-Konfiguration
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

    def create_control_tab(self, parent):
        # Frame für Servo-Grid
        control_frame = ttk.Frame(parent, padding="3")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Grid für Servos (4x4)
        for i in range(16):
            row = i // 4
            col = i % 4
            
            # Servo Frame
            servo_frame = ttk.Labelframe(control_frame, text=f"Servo {i+1}", 
                                       style='Servo.TLabelframe')
            servo_frame.grid(row=row, column=col, padx=3, pady=3, sticky=(tk.W, tk.E))
            
            # Status Label
            status_label = ttk.Label(servo_frame, text="Position: Links",
                                   style='Servo.TLabel')
            status_label.grid(row=0, column=0, columnspan=2, pady=2)
            
            # Buttons
            ttk.Button(servo_frame, text="Links", width=8,
                      style='Servo.TButton',
                      command=lambda x=i: self.set_servo_position(x, 'left')).grid(
                          row=1, column=0, padx=2, pady=2)
            
            ttk.Button(servo_frame, text="Rechts", width=8,
                      style='Servo.TButton',
                      command=lambda x=i: self.set_servo_position(x, 'right')).grid(
                          row=1, column=1, padx=2, pady=2)
            
            self.servo_status[i]['frame'] = servo_frame
            self.servo_status[i]['label'] = status_label
        
        # Grid-Konfiguration
        for i in range(4):
            control_frame.columnconfigure(i, weight=1)
            control_frame.rowconfigure(i, weight=1)

    def create_track_tab(self, parent):
        """Gleiskarte-Tab erstellen"""
        # Frame für die Karte
        map_frame = ttk.Frame(parent, padding="5")
        map_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Gleiskarte erstellen
        self.track_map = TrackMap(map_frame)
        
        # Grid-Konfiguration
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

    def create_calibration_tab(self, parent):
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
        self.left_angle = tk.StringVar(value="2.5")
        left_entry = ttk.Entry(config_frame, textvariable=self.left_angle, width=10)
        left_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(config_frame, text="(2.5-12.5)", font=('TkDefaultFont', 8)).grid(row=0, column=2, padx=2)
        
        # Position B (Rechts)
        ttk.Label(config_frame, text="Position B (Rechts):", font=('TkDefaultFont', 10)).grid(row=1, column=0, padx=5, pady=5)
        self.right_angle = tk.StringVar(value="12.5")
        right_entry = ttk.Entry(config_frame, textvariable=self.right_angle, width=10)
        right_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(config_frame, text="(2.5-12.5)", font=('TkDefaultFont', 8)).grid(row=1, column=2, padx=2)
        
        # Geschwindigkeit
        ttk.Label(config_frame, text="Geschwindigkeit:", font=('TkDefaultFont', 10)).grid(row=2, column=0, padx=5, pady=5)
        self.speed = tk.StringVar(value="0.5")
        speed_entry = ttk.Entry(config_frame, textvariable=self.speed, width=10)
        speed_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(config_frame, text="(0.1-1.0)", font=('TkDefaultFont', 8)).grid(row=2, column=2, padx=2)
        
        # Trace-Funktionen für die StringVars
        self.left_angle.trace_add('write', self.update_left_angle)
        self.right_angle.trace_add('write', self.update_right_angle)
        self.speed.trace_add('write', self.update_speed)
        
        # Button-Frame
        button_frame = ttk.Frame(config_main)
        button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Test Position A", width=15,
                  command=lambda: self.test_position('left')).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Test Position B", width=15,
                  command=lambda: self.test_position('right')).grid(row=0, column=1, padx=5, pady=5)
<<<<<<< HEAD
        ttk.Button(button_frame, text="Speichern", width=15,
                  command=self.save_calibration).grid(row=0, column=2, padx=5, pady=5)
=======
>>>>>>> 5ec4887295d416231d885e6cfb7c462acd87b57e

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
        """Erstellt den Info & Settings Tab"""
        info_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(info_frame, text='Info & Settings')
        
        # Container für Text und Buttons
        content_frame = ttk.Frame(info_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Info-Text
        info_text = """Entwickelt von: EinsPommes
Website: Chill-zone.xyz

Version: 1.1
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
        
        # Label für den Info-Text
        ttk.Label(content_frame, text=info_text, justify=tk.LEFT).pack(side='left', anchor='nw')
        
        # Frame für die Buttons auf der rechten Seite
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(side='right', anchor='ne')
        
        # Update und Beenden Buttons
        update_button = ttk.Button(button_frame, text="Update", command=self.check_for_updates)
        update_button.pack(pady=2)
        
        quit_button = ttk.Button(button_frame, text="Beenden", command=self.quit_application)
        quit_button.pack(pady=2)
    
    def on_servo_selected(self, event):
        if not self.selected_servo.get():
            return
            
        servo_id = int(self.selected_servo.get().split()[1]) - 1
        config = self.servo_controller.get_servo_config(servo_id)
        
        self.left_angle.set(f"{config['left_angle']:.1f}")
        self.right_angle.set(f"{config['right_angle']:.1f}")
        self.speed.set(f"{config['speed']:.1f}")
    
    def update_left_angle(self, *args):
        """Aktualisiert den linken Winkel in der Konfiguration"""
        if not self.selected_servo.get():
            return
        try:
            value = self.left_angle.get()
            if value and value != ".":
                angle = float(value)
                if 2.5 <= angle <= 12.5:
                    servo_id = int(self.selected_servo.get().split()[1]) - 1
                    # Nur Konfiguration aktualisieren, keine Bewegung
                    self.servo_controller.servo_config[servo_id]['left_angle'] = angle
        except ValueError:
            pass

    def update_right_angle(self, *args):
        """Aktualisiert den rechten Winkel in der Konfiguration"""
        if not self.selected_servo.get():
            return
        try:
            value = self.right_angle.get()
            if value and value != ".":
                angle = float(value)
                if 2.5 <= angle <= 12.5:
                    servo_id = int(self.selected_servo.get().split()[1]) - 1
                    # Nur Konfiguration aktualisieren, keine Bewegung
                    self.servo_controller.servo_config[servo_id]['right_angle'] = angle
        except ValueError:
            pass

    def update_speed(self, *args):
        """Aktualisiert die Geschwindigkeit in der Konfiguration"""
        if not self.selected_servo.get():
            return
        try:
            value = self.speed.get()
            if value and value != ".":
                speed = float(value)
                if 0.1 <= speed <= 1.0:
                    servo_id = int(self.selected_servo.get().split()[1]) - 1
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

    def test_position(self, position):
        """Testet eine Position (bewegt den Servo)"""
        if not self.selected_servo.get():
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst einen Servo aus.")
            return
            
        try:
            servo_id = int(self.selected_servo.get().split()[1]) - 1
            
            # Aktuelle Werte aus den Eingabefeldern holen
            if position == 'left':
                angle = float(self.left_angle.get())
                if not (2.5 <= angle <= 12.5):
                    messagebox.showerror("Fehler", "Ungültiger Winkel für Position A (2.5-12.5)")
                    return
            else:
                angle = float(self.right_angle.get())
                if not (2.5 <= angle <= 12.5):
                    messagebox.showerror("Fehler", "Ungültiger Winkel für Position B (2.5-12.5)")
                    return
                    
            speed = float(self.speed.get())
            if not (0.1 <= speed <= 1.0):
                messagebox.showerror("Fehler", "Ungültige Geschwindigkeit (0.1-1.0)")
                return
            
            # Konfiguration aktualisieren
            self.servo_controller.set_servo_config(servo_id, 
                left_angle=float(self.left_angle.get()),
                right_angle=float(self.right_angle.get()),
                speed=speed)
            
            # Servo bewegen
            self.servo_controller.set_servo_position(servo_id, position)
            
        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {str(e)}")
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
            
    def check_for_updates(self):
        """Prüft auf Updates"""
        messagebox.showinfo("Update", "Keine Updates verfügbar.")
        
    def quit_application(self):
        """Beendet die Anwendung"""
        if messagebox.askokcancel("Beenden", "Möchten Sie die Anwendung wirklich beenden?"):
            self.servo_controller.cleanup()
            self.root.quit()
            
    def update_software(self):
        """Software über Git aktualisieren"""
        import subprocess
        import sys
        import os
        import shutil
        from datetime import datetime

        try:
            logger.info("Starte Software-Update")
            # Aktuelles Verzeichnis speichern
            current_dir = os.getcwd()
            
            # In das Projektverzeichnis wechseln
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            os.chdir(project_dir)
            logger.info(f"Wechsle in Verzeichnis: {project_dir}")

            # Backup erstellen
            backup_dir = os.path.join(project_dir, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
            
            logger.info(f"Erstelle Backup: {backup_path}")
            shutil.copytree(project_dir, backup_path, 
                          ignore=shutil.ignore_patterns('backups', 'logs', '.git'))
            
            # Git-Befehle ausführen
            logger.info("Führe git fetch aus")
            subprocess.check_call(['git', 'fetch', 'origin'])
            
            logger.info("Führe git reset aus")
            subprocess.check_call(['git', 'reset', '--hard', 'origin/main'])
            
            # Zurück zum ursprünglichen Verzeichnis
            os.chdir(current_dir)
            
            # Erfolgsmeldung
            logger.info("Update erfolgreich abgeschlossen")
            messagebox.showinfo("Update", 
                              "Update erfolgreich! Ein Backup wurde erstellt.\n"
                              f"Backup-Pfad: {backup_path}\n\n"
                              "Bitte starten Sie das Programm neu.")
            
            # Programm beenden
            self.quit_application()
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Update fehlgeschlagen: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Fehler", error_msg)
        except Exception as e:
<<<<<<< HEAD
            messagebox.showerror("Fehler", f"Unerwarteter Fehler: {str(e)}")
            
    def save_calibration(self):
        """Speichert die aktuelle Konfiguration"""
        if not self.selected_servo.get():
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst einen Servo aus.")
            return
            
        try:
            # Aktuelle Werte aus den Eingabefeldern holen
            left_angle = float(self.left_angle.get())
            right_angle = float(self.right_angle.get())
            speed = float(self.speed.get())
            
            # Werte validieren
            if not (2.5 <= left_angle <= 12.5):
                messagebox.showerror("Fehler", "Ungültiger Winkel für Position A (2.5-12.5)")
                return
                
            if not (2.5 <= right_angle <= 12.5):
                messagebox.showerror("Fehler", "Ungültiger Winkel für Position B (2.5-12.5)")
                return
                
            if not (0.1 <= speed <= 1.0):
                messagebox.showerror("Fehler", "Ungültige Geschwindigkeit (0.1-1.0)")
                return
            
            # Servo-ID aus Combobox-Text extrahieren (z.B. "Servo 1" -> 0)
            servo_id = int(self.selected_servo.get().split()[1]) - 1
            
            # Konfiguration aktualisieren
            self.servo_controller.set_servo_config(servo_id,
                left_angle=left_angle,
                right_angle=right_angle,
                speed=speed)
            
            # Konfiguration speichern
            if self.servo_controller.save_config():
                messagebox.showinfo("Erfolg", "Konfiguration erfolgreich gespeichert")
            else:
                messagebox.showerror("Fehler", "Fehler beim Speichern der Konfiguration")
            
        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {str(e)}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
=======
            error_msg = f"Unerwarteter Fehler: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Fehler", error_msg)
>>>>>>> 5ec4887295d416231d885e6cfb7c462acd87b57e

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
