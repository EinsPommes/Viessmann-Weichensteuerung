import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import logging
import os
import socket
from servokit_controller import ServoKitController
from web_server import run_server
import subprocess

class WeichensteuerungGUI(tk.Tk):
    def __init__(self):
        try:
            # Logger initialisieren
            self.setup_logging()
            self.logger.debug("GUI Initialisierung gestartet")
            
            # Hauptfenster erstellen
            super().__init__()
            
            # Fenstergröße für 10 Zoll Display (1024x600)
            self.geometry("1024x600")
            self.minsize(1024, 600)
            
            # Styles für 10 Zoll Display anpassen
            self.style = ttk.Style()
            self.style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
            self.style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
            self.style.configure('Normal.TLabel', font=('Helvetica', 12))
            self.style.configure('Small.TLabel', font=('Helvetica', 10))
            self.style.configure('Big.TButton', font=('Helvetica', 12), padding=5)
            
            # Fenstertitel
            self.title("Weichensteuerung")
            
            # Initialisiere Dictionaries für LED Canvas und Position Labels
            self.led_canvas = {}
            self.position_labels = {}
            self.servo_leds = {}
            self.status_labels = {}
            self.servo_frames = {}
            
            # Kalibrierungs-Variablen
            self.cal_servo_var = tk.StringVar(value="Servo 1")
            self.left_angle_var = tk.StringVar(value="30.0")
            self.right_angle_var = tk.StringVar(value="150.0")
            self.current_servo = 0
            
            # Flag für Beenden
            self._closing = False
            
            # Initialisiere ServoKit Controller
            self.init_servo_controller()
            self.logger.info("Servo-Controller wurde initialisiert")
            
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
            self.update_status()
            
            # Bind Closing Event
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            self.logger.debug("GUI Initialisierung abgeschlossen")
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Fehler bei der GUI Initialisierung: {e}")
            else:
                print(f"Logger nicht verfügbar. Fehler: {e}")
            messagebox.showerror("Fehler", f"GUI Initialisierung fehlgeschlagen: {str(e)}")
            raise
            
    def setup_logging(self):
        """Initialisiert den Logger"""
        try:
            # Erstelle Logger
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.DEBUG)
            
            # Erstelle Handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            
            # Erstelle Formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            
            # Füge Handler zum Logger hinzu
            self.logger.addHandler(console_handler)
            
            self.logger.debug("Logger wurde initialisiert")
            
        except Exception as e:
            print(f"Fehler bei der Logger-Initialisierung: {e}")
            raise

    def create_control_tab(self):
        """Erstellt den Control-Tab mit LED-Anzeigen und Buttons für jeden Servo"""
        self.logger.debug("Erstelle Control-Tab")
        
        # Frame für Control-Tab
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text='Steuerung')
        
        # Grid-Konfiguration für 4x4 Layout
        for i in range(4):
            control_frame.grid_columnconfigure(i, weight=1, minsize=250)  # Mindestbreite für Servo-Frames
            control_frame.grid_rowconfigure(i, weight=1, minsize=140)     # Mindesthöhe für Servo-Frames
        
        # Grid für Servo-Steuerung (4x4)
        for row in range(4):
            for col in range(4):
                i = row * 4 + col  # Servo-ID
                
                # Frame für jeden Servo mit mehr Padding
                servo_frame = ttk.LabelFrame(control_frame, text=f"Servo {i+1}", padding="10")
                servo_frame.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
                
                # Status-Frame
                status_frame = ttk.Frame(servo_frame)
                status_frame.pack(fill=tk.X, pady=5)
                
                # LED-Canvas (größer)
                canvas = tk.Canvas(status_frame, width=24, height=24, bg=self.cget('bg'), highlightthickness=0)
                canvas.pack(side=tk.LEFT, padx=5)
                
                # LED (Kreis) zeichnen
                led = canvas.create_oval(4, 4, 20, 20, fill='gray')
                self.led_canvas[i] = (canvas, led)
                self.logger.debug(f"LED Canvas für Servo {i+1} erstellt")
                
                # Label für Position (größere Schrift)
                pos_label = ttk.Label(servo_frame, text="---", style='Normal.TLabel')
                pos_label.pack(pady=5)
                self.position_labels[i] = pos_label
                self.logger.debug(f"Position Label für Servo {i+1} erstellt")
                
                # Button-Frame
                btn_frame = ttk.Frame(servo_frame)
                btn_frame.pack(pady=5)
                
                # Größere Buttons mit mehr Padding
                ttk.Button(btn_frame, 
                          text="←", 
                          width=4,
                          style='Big.TButton',
                          command=lambda s=i: self.move_left(s)).pack(side=tk.LEFT, padx=3)
                
                ttk.Button(btn_frame, 
                          text="→", 
                          width=4,
                          style='Big.TButton',
                          command=lambda s=i: self.move_right(s)).pack(side=tk.LEFT, padx=3)
                
        self.logger.debug(f"Control-Tab erstellt mit {len(self.led_canvas)} LED Canvas und {len(self.position_labels)} Position Labels")
        
    def create_calibration_tab(self):
        """Erstellt den Kalibrierungs-Tab"""
        self.logger.debug("Erstelle Kalibrierungs-Tab")
        
        # Frame für Kalibrierungs-Tab
        cal_frame = ttk.Frame(self.notebook)
        self.notebook.add(cal_frame, text='Kalibrierung')
        
        # Servo-Auswahl
        select_frame = ttk.LabelFrame(cal_frame, text="Servo-Auswahl", padding=10)
        select_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Dropdown für Servo-Auswahl
        servo_list = [f"Servo {i+1}" for i in range(16)]
        servo_select = ttk.OptionMenu(select_frame, self.cal_servo_var, "Servo 1", *servo_list)
        servo_select.config(width=20)
        servo_select.pack(pady=10)
        
        # Winkel-Einstellung
        angle_frame = ttk.LabelFrame(cal_frame, text="Winkel-Einstellung", padding=10)
        angle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Links
        left_frame = ttk.Frame(angle_frame)
        left_frame.pack(fill=tk.X, pady=5)
        ttk.Label(left_frame, text="Links (°):", style='Normal.TLabel').pack(side=tk.LEFT, padx=5)
        ttk.Entry(left_frame, textvariable=self.left_angle_var, width=10).pack(side=tk.LEFT)
        ttk.Button(left_frame, text="Test", style='Big.TButton',
                  command=lambda: self.test_angle('left')).pack(side=tk.LEFT, padx=5)
        
        # Rechts
        right_frame = ttk.Frame(angle_frame)
        right_frame.pack(fill=tk.X, pady=5)
        ttk.Label(right_frame, text="Rechts (°):", style='Normal.TLabel').pack(side=tk.LEFT, padx=5)
        ttk.Entry(right_frame, textvariable=self.right_angle_var, width=10).pack(side=tk.LEFT)
        ttk.Button(right_frame, text="Test", style='Big.TButton',
                  command=lambda: self.test_angle('right')).pack(side=tk.LEFT, padx=5)
        
        # Speichern-Button
        ttk.Button(angle_frame, text="Speichern", style='Big.TButton',
                  command=self.save_calibration).pack(pady=10)
        
        self.logger.debug("Kalibrierungs-Tab erstellt")

    def create_status_tab(self):
        """Erstellt den Status-Tab"""
        self.logger.debug("Erstelle Status-Tab")
        
        # Frame für Status-Tab
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text='Status')
        
        # Status-Überschrift
        ttk.Label(status_frame, text="System-Status", style='Title.TLabel').pack(pady=10)
        
        # Status-Anzeigen
        for i in range(16):
            servo_frame = ttk.LabelFrame(status_frame, text=f"Servo {i+1}", padding=5)
            servo_frame.pack(fill=tk.X, padx=10, pady=2)
            
            # Status-Label
            status_label = ttk.Label(servo_frame, text="---", style='Normal.TLabel')
            status_label.pack(side=tk.LEFT, padx=5)
            self.status_labels[i] = status_label
        
        self.logger.debug("Status-Tab erstellt")

    def create_track_tab(self):
        """Erstellt den Gleiskarten-Tab"""
        self.logger.debug("Erstelle Gleiskarten-Tab")
        
        # Frame für Gleiskarten-Tab
        track_frame = ttk.Frame(self.notebook)
        self.notebook.add(track_frame, text='Gleiskarte')
        
        # Platzhalter-Text
        ttk.Label(track_frame, text="Gleiskarte wird hier angezeigt", style='Normal.TLabel').pack(pady=20)
        
        self.logger.debug("Gleiskarten-Tab erstellt")

    def create_settings_tab(self):
        """Erstellt den Einstellungen-Tab"""
        self.logger.debug("Erstelle Settings-Tab")
        
        # Frame für Settings-Tab
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text='Einstellungen')
        
        # IP-Adresse
        ip_frame = ttk.LabelFrame(settings_frame, text="Netzwerk", padding=10)
        ip_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.ip_label = ttk.Label(ip_frame, text="IP-Adresse: ---", style='Normal.TLabel')
        self.ip_label.pack()
        
        # Aktualisiere IP alle 5 Sekunden
        self.update_ip()
        
        self.logger.debug("Settings-Tab erstellt")
        
    def update_ip(self):
        """Aktualisiert die IP-Adresse in der GUI"""
        ip = self.get_ip_address()
        self.ip_label.config(text=f"IP-Adresse: {ip}:5000")
        self.after(5000, self.update_ip)  # Erneut in 5 Sekunden

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

    def update_servo_status(self, servo_id=None):
        """Aktualisiert die Statusanzeige für einen oder alle Servos"""
        try:
            if servo_id is None:
                # Aktualisiere alle Servos
                for i in range(16):
                    self.update_servo_status(i)
                return

            # Hole Servo-Status
            state = self.servo_controller.get_servo_status(servo_id)
            
            # Aktualisiere LED
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                
                if state.get('error'):
                    canvas.itemconfig(led, fill='red')
                elif state.get('status') == 'moving':
                    canvas.itemconfig(led, fill='yellow')
                elif state.get('position') in ['left', 'right']:
                    canvas.itemconfig(led, fill='green')
                else:
                    canvas.itemconfig(led, fill='gray')
            
            # Aktualisiere Position Label
            if servo_id in self.position_labels:
                position = state.get('position')
                if position == 'left':
                    self.position_labels[servo_id].config(text='Links')
                elif position == 'right':
                    self.position_labels[servo_id].config(text='Rechts')
                else:
                    self.position_labels[servo_id].config(text='---')
                    
            # Aktualisiere Status Label
            if servo_id in self.status_labels:
                status = state.get('status', '---')
                error = state.get('error')
                if error:
                    self.status_labels[servo_id].config(text=f"Fehler: {error}")
                else:
                    self.status_labels[servo_id].config(text=status.capitalize())
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Servo-Status: {e}")
            if servo_id in self.led_canvas:
                canvas, led = self.led_canvas[servo_id]
                canvas.itemconfig(led, fill='red')

    def update_status(self):
        """Aktualisiert den Status aller Servos"""
        if self._closing:
            return
            
        try:
            # Status für alle Servos aktualisieren
            for i in range(16):
                self.update_servo_status(i)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Status: {e}")
            
        # Plane nächste Aktualisierung wenn nicht beendet
        if not self._closing:
            self.after(500, self.update_status)

    def move_servo(self, servo_id, direction):
        """Bewegt einen Servo in die angegebene Richtung"""
        try:
            self.logger.info(f"Bewege Servo {servo_id + 1} nach {direction}")
            
            # Bewege Servo
            result = self.servo_controller.move_servo(servo_id, direction)
            
            if result.get('error'):
                raise Exception(result['error'])
                
            # Aktualisiere GUI
            self.update_servo_status(servo_id)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen von Servo {servo_id + 1}: {e}")
            messagebox.showerror("Fehler", str(e))

    def move_left(self, servo_id):
        """Bewegt den Servo nach links"""
        try:
            self.move_servo(servo_id, 'left')
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen nach links: {e}")
            messagebox.showerror("Fehler", str(e))

    def move_right(self, servo_id):
        """Bewegt den Servo nach rechts"""
        try:
            self.move_servo(servo_id, 'right')
        except Exception as e:
            self.logger.error(f"Fehler beim Bewegen nach rechts: {e}")
            messagebox.showerror("Fehler", str(e))

    def init_servo_controller(self):
        """Initialisiert den Servo-Controller"""
        try:
            self.logger.info("Initialisiere Servo-Controller...")
            self.servo_controller = ServoKitController()
            self.logger.info("Servo-Controller erfolgreich initialisiert")
            
        except Exception as e:
            self.logger.error(f"Fehler bei Controller-Initialisierung: {str(e)}")
            messagebox.showerror("Fehler", f"Konnte Servo-Controller nicht initialisieren: {str(e)}")
            raise

    def update_software(self):
        """Software über Git aktualisieren"""
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
            self.quit_program()
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Fehler", f"Update fehlgeschlagen: {str(e)}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Unerwarteter Fehler: {str(e)}")

    def test_angle(self, position):
        """Testet einen Winkel während der Kalibrierung"""
        try:
            # Hole Servo-ID
            servo_str = self.cal_servo_var.get()
            servo_id = int(servo_str.split()[1]) - 1  # "Servo 1" -> 0
            
            # Hole Winkel
            if position == 'left':
                angle = float(self.left_angle_var.get())
            else:  # right
                angle = float(self.right_angle_var.get())
            
            self.logger.info(f"Test: Bewege Servo {servo_id + 1} nach {position} (Winkel: {angle}°)")
            
            # Setze Winkel
            if servo_id < 16:
                self.servo_controller.kit1.servo[servo_id].angle = angle
            else:
                if not self.servo_controller.kit2:
                    raise Exception("Zweites Board nicht verfügbar")
                self.servo_controller.kit2.servo[servo_id-16].angle = angle
            
        except Exception as e:
            self.logger.error(f"Fehler beim Testen des Winkels: {e}")
            messagebox.showerror("Fehler", str(e))

    def save_calibration(self):
        """Speichert die Kalibrierungseinstellungen"""
        try:
            # Hole aktuelle Servo-ID
            servo_str = self.cal_servo_var.get()
            servo_id = int(servo_str.split()[1]) - 1  # "Servo 1" -> 0
            
            # Hole die Winkel
            left_angle = float(self.left_angle_var.get())
            right_angle = float(self.right_angle_var.get())
            
            self.logger.info(f"Speichere Kalibrierung für Servo {servo_id+1}: Links={left_angle}°, Rechts={right_angle}°")
            
            # Aktualisiere die Servo-Konfiguration
            config_data = {
                'left_angle': left_angle,
                'right_angle': right_angle
            }
            
            # Speichere die Konfiguration
            self.servo_controller.update_servo_config(servo_id, config_data)
            
            messagebox.showinfo("Erfolg", f"Kalibrierung für Servo {servo_id+1} gespeichert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Kalibrierung: {e}")
            messagebox.showerror("Fehler", f"Kalibrierung konnte nicht gespeichert werden: {str(e)}")

    def quit_program(self):
        """Beendet das Programm"""
        try:
            if messagebox.askyesno("Beenden", "Möchten Sie das Programm wirklich beenden?"):
                self.logger.info("Programm wird beendet")
                self.destroy()
        except Exception as e:
            self.logger.error(f"Fehler beim Beenden: {e}")
            messagebox.showerror("Fehler", str(e))

    def check_for_updates(self):
        """Prüft auf Updates"""
        try:
            # Hier könnte später die Update-Logik implementiert werden
            messagebox.showinfo("Updates", "Keine neuen Updates verfügbar.")
        except Exception as e:
            self.logger.error(f"Fehler bei der Update-Prüfung: {e}")
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

def main():
    try:
        root = WeichensteuerungGUI()
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Starten: {str(e)}")
        raise

if __name__ == "__main__":
    main()