# from adafruit_servokit import ServoKit
import time

class ServoController:
    def __init__(self, num_servos=16, pca_address=0x40):
        """
        Initialisiert den Servo-Controller
        
        Args:
            num_servos (int): Anzahl der Servomotoren (Standard: 16)
            pca_address (hex): I2C-Adresse des PCA9685 (Standard: 0x40)
        """
        # self.kit = ServoKit(channels=16, address=pca_address)
        self.num_servos = num_servos
        self.servo_positions = [0] * num_servos  # 0 = links, 1 = rechts
        
        # Servo-Winkel für links/rechts Position (konfigurierbar)
        self.LEFT_ANGLE = 0
        self.RIGHT_ANGLE = 180
        self.MIN_PULSE = 500
        self.MAX_PULSE = 2500
        
        # Initialisierung der Servos
        self._init_servos()
    
    def _init_servos(self):
        """Initialisiert alle Servos mit Standardwerten"""
        for i in range(self.num_servos):
            # self.kit.servo[i].set_pulse_width_range(self.MIN_PULSE, self.MAX_PULSE)
            self.set_position(i, "left")  # Standardposition: links
    
    def calibrate_servo(self, servo_num, min_pulse, max_pulse):
        """
        Kalibriert einen einzelnen Servo
        
        Args:
            servo_num (int): Nummer des Servos (0-15)
            min_pulse (int): Minimale Pulsweite in µs
            max_pulse (int): Maximale Pulsweite in µs
        """
        if servo_num < 0 or servo_num >= self.num_servos:
            raise ValueError(f"Ungültige Servo-Nummer: {servo_num}")
            
        # self.kit.servo[servo_num].set_pulse_width_range(min_pulse, max_pulse)
        print(f"Kalibriere Servo {servo_num} mit Pulsen {min_pulse}-{max_pulse}")
    
    def set_position(self, servo_num, position):
        """
        Setzt die Position eines Servos
        
        Args:
            servo_num (int): Nummer des Servos (0-15)
            position (str): "left" oder "right"
        """
        if servo_num < 0 or servo_num >= self.num_servos:
            raise ValueError(f"Ungültige Servo-Nummer: {servo_num}")
            
        if position.lower() not in ["left", "right"]:
            raise ValueError("Position muss 'left' oder 'right' sein")
            
        angle = self.LEFT_ANGLE if position.lower() == "left" else self.RIGHT_ANGLE
        # self.kit.servo[servo_num].angle = angle
        print(f"Setze Servo {servo_num} auf Position {position} (Winkel: {angle})")
        self.servo_positions[servo_num] = 0 if position.lower() == "left" else 1
        
        # Kurze Pause für die Servobewegung
        time.sleep(0.1)
    
    def get_position(self, servo_num):
        """
        Gibt die aktuelle Position eines Servos zurück
        
        Args:
            servo_num (int): Nummer des Servos (0-15)
            
        Returns:
            str: "left" oder "right"
        """
        if servo_num < 0 or servo_num >= self.num_servos:
            raise ValueError(f"Ungültige Servo-Nummer: {servo_num}")
            
        return "left" if self.servo_positions[servo_num] == 0 else "right"
        
    def test_servo(self, servo_num):
        """
        Testet einen Servo durch Bewegung in beide Positionen
        
        Args:
            servo_num (int): Nummer des Servos (0-15)
        """
        if servo_num < 0 or servo_num >= self.num_servos:
            raise ValueError(f"Ungültige Servo-Nummer: {servo_num}")
            
        print(f"Teste Servo {servo_num}...")
        self.set_position(servo_num, "left")
        time.sleep(1)
        self.set_position(servo_num, "right")
        time.sleep(1)
        self.set_position(servo_num, "left")
