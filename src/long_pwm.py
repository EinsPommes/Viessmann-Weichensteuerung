import RPi.GPIO as GPIO
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Servo an GPIO 17
SERVO_PIN = 17

try:
    print(f"1. Setze Pin {SERVO_PIN} als Ausgang...")
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    
    print("2. Erstelle PWM mit 50Hz...")
    pwm = GPIO.PWM(SERVO_PIN, 50)
    
    print("3. Starte PWM...")
    pwm.start(0)
    time.sleep(1)
    
    print("4. Teste verschiedene Positionen...")
    for i in range(10):  # 10 Versuche
        print(f"Versuch {i+1}: Links (2.5)")
        pwm.ChangeDutyCycle(2.5)
        time.sleep(2)
        
        print(f"Versuch {i+1}: Rechts (12.5)")
        pwm.ChangeDutyCycle(12.5)
        time.sleep(2)
    
    print("5. Ende")
    pwm.stop()
    GPIO.cleanup()

except KeyboardInterrupt:
    print("Programm durch Benutzer beendet")
    if 'pwm' in locals():
        pwm.stop()
    GPIO.cleanup()
    
except Exception as e:
    print(f"Fehler: {e}")
    if 'pwm' in locals():
        pwm.stop()
    GPIO.cleanup()
