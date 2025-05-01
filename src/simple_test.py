#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfaches Testprogramm für die Weichensteuerung ohne GUI
"""

import time
import logging
import RPi.GPIO as GPIO

# Konfiguration
SERVO_COUNT = 16  # Anzahl der Servos

# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('weichensteuerung_test')

def setup():
    """Initialisiert die GPIO-Pins"""
    logger.info("Initialisiere GPIO...")
    # Hier können Sie GPIO-Pins initialisieren, falls nötig
    logger.info("GPIO initialisiert")

def cleanup():
    """Bereinigt die GPIO-Pins"""
    logger.info("Bereinige GPIO...")
    GPIO.cleanup()
    logger.info("GPIO bereinigt")

def main():
    """Hauptfunktion"""
    try:
        logger.info("Starte einfaches Testprogramm für die Weichensteuerung")
        
        # Setup
        setup()
        
        # Einfache Konsolenausgabe
        print("\nWeichensteuerung Testprogramm")
        print("=============================")
        print("Befehle:")
        print("  l <servo_id> - Bewege Servo nach links")
        print("  r <servo_id> - Bewege Servo nach rechts")
        print("  s - Status anzeigen")
        print("  q - Beenden")
        print("=============================\n")
        
        # Hauptschleife
        while True:
            cmd = input("Befehl: ")
            
            if cmd.lower() == 'q':
                break
            elif cmd.lower() == 's':
                print("Status: Simulierter Betrieb (keine echte Hardware angeschlossen)")
            elif cmd.lower().startswith('l '):
                try:
                    servo_id = int(cmd.split()[1])
                    if 1 <= servo_id <= SERVO_COUNT:
                        print(f"Bewege Servo {servo_id} nach links (simuliert)")
                    else:
                        print(f"Ungültige Servo-ID. Muss zwischen 1 und {SERVO_COUNT} sein.")
                except (IndexError, ValueError):
                    print("Ungültiges Format. Verwenden Sie 'l <servo_id>'")
            elif cmd.lower().startswith('r '):
                try:
                    servo_id = int(cmd.split()[1])
                    if 1 <= servo_id <= SERVO_COUNT:
                        print(f"Bewege Servo {servo_id} nach rechts (simuliert)")
                    else:
                        print(f"Ungültige Servo-ID. Muss zwischen 1 und {SERVO_COUNT} sein.")
                except (IndexError, ValueError):
                    print("Ungültiges Format. Verwenden Sie 'r <servo_id>'")
            else:
                print("Unbekannter Befehl")
                
    except KeyboardInterrupt:
        print("\nProgramm wird beendet...")
    except Exception as e:
        logger.error(f"Fehler: {e}")
    finally:
        cleanup()
        logger.info("Programm beendet")

if __name__ == "__main__":
    main()
