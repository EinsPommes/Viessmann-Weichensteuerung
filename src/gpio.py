#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPIO-Steuerung für Viessmann Weichensteuerung mit CarMotion InduktivCharger
"""

import RPi.GPIO as GPIO
import logging
from config import CHARGER_STATUS_PIN, CHARGER_CONTROL_PIN

# Logger einrichten
logger = logging.getLogger(__name__)

def setup():
    """
    Initialisiert die GPIO-Pins für den CarMotion InduktivCharger
    """
    try:
        # GPIO-Modus setzen (BCM = Broadcom SOC channel, verwendet GPIO-Nummern)
        GPIO.setmode(GPIO.BCM)
        
        # Status-Pin als Eingang konfigurieren
        GPIO.setup(CHARGER_STATUS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        logger.info(f"Charger Status-Pin {CHARGER_STATUS_PIN} als Eingang konfiguriert")
        
        # Steuer-Pin als Ausgang konfigurieren und initial auf LOW setzen
        GPIO.setup(CHARGER_CONTROL_PIN, GPIO.OUT)
        GPIO.output(CHARGER_CONTROL_PIN, GPIO.LOW)
        logger.info(f"Charger Control-Pin {CHARGER_CONTROL_PIN} als Ausgang konfiguriert (initial LOW)")
        
        return True
    except Exception as e:
        logger.error(f"Fehler bei der GPIO-Initialisierung: {str(e)}")
        return False

def is_charging():
    """
    Prüft, ob ein Auto auf dem Charger steht und geladen wird
    
    Returns:
        bool: True wenn ein Auto geladen wird, sonst False
    """
    try:
        status = GPIO.input(CHARGER_STATUS_PIN) == GPIO.HIGH
        logger.debug(f"Ladestatus abgefragt: {'Lädt' if status else 'Lädt nicht'}")
        return status
    except Exception as e:
        logger.error(f"Fehler beim Abfragen des Ladestatus: {str(e)}")
        return False

def start_charging():
    """
    Startet den Ladevorgang durch Setzen des Control-Pins auf HIGH
    """
    try:
        GPIO.output(CHARGER_CONTROL_PIN, GPIO.HIGH)
        logger.info("Ladevorgang gestartet")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Starten des Ladevorgangs: {str(e)}")
        return False

def stop_charging():
    """
    Stoppt den Ladevorgang durch Setzen des Control-Pins auf LOW
    """
    try:
        GPIO.output(CHARGER_CONTROL_PIN, GPIO.LOW)
        logger.info("Ladevorgang gestoppt")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Stoppen des Ladevorgangs: {str(e)}")
        return False

def cleanup():
    """
    Bereinigt die GPIO-Konfiguration
    """
    try:
        GPIO.cleanup([CHARGER_STATUS_PIN, CHARGER_CONTROL_PIN])
        logger.info("GPIO-Pins für CarMotion InduktivCharger bereinigt")
    except Exception as e:
        logger.error(f"Fehler bei der GPIO-Bereinigung: {str(e)}")
