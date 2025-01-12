import pigpio
import time

# Verbinde mit pigpio
pi = pigpio.pi()

# Test-Pin (GPIO 5 für Servo 3)
SERVO_PIN = 5

try:
    print("Teste Servo auf Pin", SERVO_PIN)
    
    # Mittelposition (1500µs)
    print("Mittelposition...")
    pi.set_servo_pulsewidth(SERVO_PIN, 1500)
    time.sleep(1)
    
    # Links (500µs)
    print("Links...")
    pi.set_servo_pulsewidth(SERVO_PIN, 500)
    time.sleep(1)
    
    # Rechts (2500µs)
    print("Rechts...")
    pi.set_servo_pulsewidth(SERVO_PIN, 2500)
    time.sleep(1)
    
    # Servo ausschalten
    pi.set_servo_pulsewidth(SERVO_PIN, 0)
    
finally:
    # Cleanup
    pi.stop()
