import RPi.GPIO as GPIO
import time

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

SERVO_PIN = 15  # GPIO15 = Pin 10

# Setup
print("Setup GPIO...")
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Create PWM with specific frequency for MG90S
print("Create PWM...")
pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz = 20ms period

try:
    # Start with neutral position
    print("Start PWM...")
    pwm.start(7.5)  # 7.5% = 1.5ms = neutral position
    time.sleep(2)
    
    for _ in range(3):  # Try 3 times
        print("0 degrees...")
        pwm.ChangeDutyCycle(5)  # 1ms pulse
        time.sleep(1)
        
        print("90 degrees...")
        pwm.ChangeDutyCycle(7.5)  # 1.5ms pulse
        time.sleep(1)
        
        print("180 degrees...")
        pwm.ChangeDutyCycle(10)  # 2ms pulse
        time.sleep(1)

finally:
    print("Cleanup...")
    pwm.stop()
    GPIO.cleanup()
