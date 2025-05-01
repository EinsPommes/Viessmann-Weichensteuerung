#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beispiel für die Integration des Viessmann 8408 CarMotion InduktivCharger
in die bestehende Weichensteuerung
"""

import time
import log
import gpio
import control

# Logging einrichten
logger = log.setup_logging(log_level=logging.INFO)

def main():
    """
    Hauptfunktion für das Beispiel
    """
    try:
        # GPIO initialisieren
        logger.info("Initialisiere GPIO für CarMotion InduktivCharger...")
        if not gpio.setup():
            logger.error("GPIO-Initialisierung fehlgeschlagen")
            return
            
        # Controller initialisieren
        logger.info("Initialisiere ChargerController...")
        if not control.init():
            logger.error("Controller-Initialisierung fehlgeschlagen")
            return
            
        # Monitoring starten
        logger.info("Starte Ladestatus-Monitoring...")
        control.start_monitoring()
        
        # Automatische Steuerung aktivieren
        logger.info("Aktiviere automatische Steuerung...")
        control.enable_auto_control(True)
        
        # Beispiel für manuelle Abfrage
        if control.is_charging():
            logger.info("Auto wird geladen")
        else:
            logger.info("Kein Auto erkannt – Ladepad frei")
            
        # Beispiel für manuelles Starten des Ladevorgangs
        logger.info("Starte Ladevorgang manuell...")
        control.start_charging()
        
        # Warten und Status abfragen
        time.sleep(2)
        status = control.get_status()
        logger.info(f"Aktueller Status: {status}")
        
        # Beispiel für manuelles Stoppen des Ladevorgangs
        logger.info("Stoppe Ladevorgang manuell...")
        control.stop_charging()
        
        # Hauptschleife (in der Praxis würde dies in die bestehende Hauptschleife integriert)
        logger.info("Starte Hauptschleife (Drücken Sie Strg+C zum Beenden)...")
        try:
            while True:
                status = control.get_status()
                print(f"Ladestatus: {'Lädt' if status['is_charging'] else 'Lädt nicht'}")
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Benutzerabbruch")
            
    except Exception as e:
        logger.error(f"Fehler: {str(e)}")
    finally:
        # Aufräumen
        logger.info("Räume auf...")
        control.cleanup()
        
if __name__ == "__main__":
    main()
