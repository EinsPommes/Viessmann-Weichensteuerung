import pigpio
import time

# Verbindung zum pigpio daemon herstellen
pi = pigpio.pi()

if not pi.connected:
    print("Konnte keine Verbindung zu pigpio daemon herstellen")
    exit()

# Servo an GPIO 17
SERVO_PIN = 17

print("1. Setze Servo auf 0 Grad...")
pi.set_servo_pulsewidth(SERVO_PIN, 500)  # 500µs = 0 Grad
time.sleep(1)

print("2. Setze Servo auf 90 Grad...")
pi.set_servo_pulsewidth(SERVO_PIN, 1500)  # 1500µs = 90 Grad
time.sleep(1)

print("3. Setze Servo auf 180 Grad...")
pi.set_servo_pulsewidth(SERVO_PIN, 2500)  # 2500µs = 180 Grad
time.sleep(1)

print("4. Cleanup...")
pi.set_servo_pulsewidth(SERVO_PIN, 0)  # PWM aus
pi.stop()

print("Test beendet!")
