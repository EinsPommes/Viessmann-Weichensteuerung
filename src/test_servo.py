import RPi.GPIO as GPIO
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Servo an GPIO 17 anschließen
SERVO_PIN = 17

# Pin als Ausgang setzen
GPIO.setup(SERVO_PIN, GPIO.OUT)

try:
    # PWM mit 50Hz erstellen
    pwm = GPIO.PWM(SERVO_PIN, 50)
    pwm.start(7.5)  # Mittelposition
    print("Servo in Mittelposition")
    time.sleep(1)

    while True:
        # Links (0°)
        print("Bewege nach links...")
        pwm.ChangeDutyCycle(2.5)
        time.sleep(1)

        # Mitte (90°)
        print("Bewege zur Mitte...")
        pwm.ChangeDutyCycle(7.5)
        time.sleep(1)

        # Rechts (180°)
        print("Bewege nach rechts...")
        pwm.ChangeDutyCycle(12.5)
        time.sleep(1)

except KeyboardInterrupt:
    print("Programm beendet")
    pwm.stop()
    GPIO.cleanup()
except Exception as e:
    print(f"Fehler: {e}")
    GPIO.cleanup()
