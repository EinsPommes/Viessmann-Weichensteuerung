import time
import threading
import random

class AutomationController:
    def __init__(self, servo_controller):
        """Initialisiert den Automation-Controller"""
        self.servo_controller = servo_controller
        self.running = False
        self.thread = None
        self.current_pattern = None
        self.pattern_functions = {
            'left_to_right': self._pattern_left_to_right,
            'right_to_left': self._pattern_right_to_left,
            'alternate': self._pattern_alternate,
            'random': self._pattern_random
        }
        
    def start_automation(self, pattern):
        """Startet die Automation mit dem gewählten Muster"""
        if pattern not in self.pattern_functions:
            raise ValueError(f"Unbekanntes Muster: {pattern}")
            
        if self.running:
            self.stop_automation()
            
        self.running = True
        self.current_pattern = pattern
        self.thread = threading.Thread(target=self._run_automation)
        self.thread.daemon = True
        self.thread.start()
        
    def stop_automation(self):
        """Stoppt die laufende Automation"""
        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None
            
    def _run_automation(self):
        """Führt die Automation aus"""
        while self.running:
            pattern_func = self.pattern_functions[self.current_pattern]
            pattern_func()
            time.sleep(1)  # Pause zwischen Durchläufen
            
    def _pattern_left_to_right(self):
        """Muster: Von links nach rechts"""
        for i in range(16):
            if not self.running:
                break
            self.servo_controller.move_servo(i, 'right')
            time.sleep(0.5)
            
    def _pattern_right_to_left(self):
        """Muster: Von rechts nach links"""
        for i in range(15, -1, -1):
            if not self.running:
                break
            self.servo_controller.move_servo(i, 'left')
            time.sleep(0.5)
            
    def _pattern_alternate(self):
        """Muster: Abwechselnd links und rechts"""
        for i in range(16):
            if not self.running:
                break
            direction = 'left' if i % 2 == 0 else 'right'
            self.servo_controller.move_servo(i, direction)
            time.sleep(0.5)
            
    def _pattern_random(self):
        """Muster: Zufällige Bewegungen"""
        import random
        for i in range(16):
            if not self.running:
                break
            direction = random.choice(['left', 'right'])
            servo = random.randint(0, 15)
            self.servo_controller.move_servo(servo, direction)
            time.sleep(0.5)
