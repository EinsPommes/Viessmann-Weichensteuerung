import RPi.GPIO as GPIO
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Servo an GPIO 17
SERVO_PIN = 17

print(f"1. Setze Pin {SERVO_PIN} als Ausgang...")
GPIO.setup(SERVO_PIN, GPIO.OUT)

print("2. Setze Pin auf HIGH...")
GPIO.output(SERVO_PIN, GPIO.HIGH)
print("Pin ist jetzt HIGH")
time.sleep(2)

print("3. Setze Pin auf LOW...")
GPIO.output(SERVO_PIN, GPIO.LOW)
print("Pin ist jetzt LOW")
time.sleep(2)

print("4. Starte PWM-Test...")
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(7.5)
print("PWM gestartet mit 7.5")
time.sleep(2)

print("5. Stoppe PWM...")
pwm.stop()

print("6. Cleanup...")
GPIO.cleanup()

print("Test beendet!")
