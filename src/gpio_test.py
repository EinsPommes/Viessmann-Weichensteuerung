from gpiozero import Servo
from time import sleep

# Erstelle Servo an GPIO17
servo = Servo(17)

try:
    print("Servo Test Start")
    
    print("Maximum")
    servo.max()
    sleep(2)
    
    print("Minimum")
    servo.min()
    sleep(2)
    
    print("Mitte")
    servo.mid()
    sleep(2)
    
except Exception as e:
    print(f"Fehler: {e}")
finally:
    servo.close()
