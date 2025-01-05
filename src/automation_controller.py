import time
import threading
import random

class AutomationController:
    def __init__(self, servo_controller):
        self.servo_controller = servo_controller
        self.running = False
        self.thread = None
        self.pattern = "Muster 1"
        self.speed = 1.0  # Sekunden zwischen Bewegungen
    
    def set_pattern(self, pattern):
        """Setzt das Automatik-Muster"""
        self.pattern = pattern
    
    def set_speed(self, speed):
        """Setzt die Geschwindigkeit (0.1 = schnell, 2.0 = langsam)"""
        self.speed = speed
    
    def start(self):
        """Startet die Automation"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_automation)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stoppt die Automation"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run_automation(self):
        """Führt das ausgewählte Muster aus"""
        while self.running:
            if self.pattern == "Muster 1":
                self._pattern_left_to_right()
            elif self.pattern == "Muster 2":
                self._pattern_right_to_left()
            elif self.pattern == "Muster 3":
                self._pattern_alternating()
            elif self.pattern == "Muster 4":
                self._pattern_random()
            elif self.pattern == "Muster 5":
                self._pattern_wave()
            elif self.pattern == "Muster 6":
                self._pattern_cross()
            
            time.sleep(self.speed * 2)  # Pause zwischen Durchläufen
    
    def _pattern_left_to_right(self):
        """Alle Servos nacheinander von links nach rechts"""
        for i in range(16):
            if not self.running:
                break
            self.servo_controller.set_servo_position(i, 'right')
            time.sleep(self.speed)
        
        for i in range(16):
            if not self.running:
                break
            self.servo_controller.set_servo_position(i, 'left')
            time.sleep(self.speed)
    
    def _pattern_right_to_left(self):
        """Alle Servos nacheinander von rechts nach links"""
        for i in range(15, -1, -1):
            if not self.running:
                break
            self.servo_controller.set_servo_position(i, 'right')
            time.sleep(self.speed)
        
        for i in range(15, -1, -1):
            if not self.running:
                break
            self.servo_controller.set_servo_position(i, 'left')
            time.sleep(self.speed)
    
    def _pattern_alternating(self):
        """Servos abwechselnd links und rechts"""
        for i in range(16):
            if not self.running:
                break
            position = 'right' if i % 2 == 0 else 'left'
            self.servo_controller.set_servo_position(i, position)
            time.sleep(self.speed)
        
        for i in range(16):
            if not self.running:
                break
            position = 'left' if i % 2 == 0 else 'right'
            self.servo_controller.set_servo_position(i, position)
            time.sleep(self.speed)
    
    def _pattern_random(self):
        """Zufällige Servo-Bewegungen"""
        servos = list(range(16))
        random.shuffle(servos)
        
        for i in servos:
            if not self.running:
                break
            position = random.choice(['left', 'right'])
            self.servo_controller.set_servo_position(i, position)
            time.sleep(self.speed)
    
    def _pattern_wave(self):
        """Wellenförmige Bewegung"""
        # Erste Welle: von links nach rechts
        for col in range(4):
            if not self.running:
                break
            for row in range(4):
                servo_id = row * 4 + col
                self.servo_controller.set_servo_position(servo_id, 'right')
                time.sleep(self.speed / 2)
        
        # Zweite Welle: von rechts nach links
        for col in range(3, -1, -1):
            if not self.running:
                break
            for row in range(4):
                servo_id = row * 4 + col
                self.servo_controller.set_servo_position(servo_id, 'left')
                time.sleep(self.speed / 2)
    
    def _pattern_cross(self):
        """Kreuzförmige Bewegung"""
        # Horizontale Linie
        for i in range(4):
            if not self.running:
                break
            # Mittlere Reihe nach rechts
            self.servo_controller.set_servo_position(4 + i, 'right')
            self.servo_controller.set_servo_position(8 + i, 'right')
            time.sleep(self.speed)
        
        # Vertikale Linie
        for i in range(4):
            if not self.running:
                break
            # Mittlere Spalte nach rechts
            servo_id = i * 4 + 1
            self.servo_controller.set_servo_position(servo_id, 'right')
            servo_id = i * 4 + 2
            self.servo_controller.set_servo_position(servo_id, 'right')
            time.sleep(self.speed)
        
        time.sleep(self.speed * 2)
        
        # Alles zurück nach links
        for i in range(16):
            if not self.running:
                break
            self.servo_controller.set_servo_position(i, 'left')
            time.sleep(self.speed / 2)
