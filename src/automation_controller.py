import time
import random
from threading import Thread, Event

class AutomationController:
    def __init__(self, servo_controller):
        """
        Initialisiert den Automatik-Controller
        
        Args:
            servo_controller: Instance of ServoController
        """
        self.servo_controller = servo_controller
        self.running = False
        self.stop_event = Event()
        self.automation_thread = None
        self.current_mode = "sequence"  # sequence, random, oder pattern
        
        # Vordefinierte Muster
        self.patterns = {
            "alternating": [(i, "left" if i % 2 == 0 else "right") for i in range(16)],
            "all_left": [(i, "left") for i in range(16)],
            "all_right": [(i, "right") for i in range(16)],
            "zigzag": [(i, "left" if (i//4 + i%4) % 2 == 0 else "right") for i in range(16)]
        }
        
    def start_automation(self, mode="sequence"):
        """
        Startet den Automatik-Modus
        
        Args:
            mode (str): Automatikmodus (sequence, random, pattern)
        """
        if self.running:
            return
            
        self.current_mode = mode
        self.running = True
        self.stop_event.clear()
        self.automation_thread = Thread(target=self._automation_loop)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        
    def stop_automation(self):
        """Stoppt den Automatik-Modus"""
        self.running = False
        self.stop_event.set()
        if self.automation_thread:
            self.automation_thread.join()
            
    def _automation_loop(self):
        """Hauptschleife für die Automation"""
        while self.running and not self.stop_event.is_set():
            if self.current_mode == "sequence":
                self._run_sequence_mode()
            elif self.current_mode == "random":
                self._run_random_mode()
            elif self.current_mode == "pattern":
                self._run_pattern_mode()
            
            # Kurze Pause zwischen den Durchläufen
            time.sleep(0.5)
            
    def _run_sequence_mode(self):
        """Sequenzielles Schalten der Weichen"""
        for i in range(16):
            if not self.running:
                break
            current_pos = self.servo_controller.get_position(i)
            new_pos = "right" if current_pos == "left" else "left"
            self.servo_controller.set_position(i, new_pos)
            time.sleep(0.5)
            
    def _run_random_mode(self):
        """Zufälliges Schalten der Weichen"""
        switch = random.randint(0, 15)
        position = random.choice(["left", "right"])
        self.servo_controller.set_position(switch, position)
        time.sleep(0.2)
        
    def _run_pattern_mode(self):
        """Ausführen vordefinierter Muster"""
        # Rotiere durch die verschiedenen Muster
        for pattern_name, pattern in self.patterns.items():
            if not self.running:
                break
            print(f"Aktiviere Muster: {pattern_name}")
            for switch, position in pattern:
                if not self.running:
                    break
                self.servo_controller.set_position(switch, position)
                time.sleep(0.2)
            time.sleep(2)  # Pause zwischen den Mustern
            
    def set_mode(self, mode):
        """
        Ändert den Automatik-Modus
        
        Args:
            mode (str): Neuer Modus (sequence, random, pattern)
        """
        if mode not in ["sequence", "random", "pattern"]:
            raise ValueError("Ungültiger Modus")
        self.current_mode = mode
