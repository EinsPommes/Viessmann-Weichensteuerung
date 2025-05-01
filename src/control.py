#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steuerungslogik für Viessmann Weichensteuerung mit CarMotion InduktivCharger
"""

import logging
import threading
import time
from config import CHARGER_STATUS_CHECK_INTERVAL
import gpio

# Logger einrichten
logger = logging.getLogger(__name__)

class ChargerController:
    """
    Controller-Klasse für den Viessmann 8408 CarMotion InduktivCharger
    """
    
    def __init__(self):
        """
        Initialisiert den ChargerController
        """
        self.is_running = False
        self.monitor_thread = None
        self.last_status = False
        self.auto_control_enabled = False
        
    def setup(self):
        """
        Initialisiert die GPIO-Pins für den CarMotion InduktivCharger
        """
        return gpio.setup()
        
    def start_monitoring(self):
        """
        Startet einen Hintergrund-Thread zur Überwachung des Ladestatus
        """
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            logger.warning("Monitoring läuft bereits")
            return False
            
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_status)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Charger-Monitoring gestartet")
        return True
        
    def stop_monitoring(self):
        """
        Stoppt die Überwachung des Ladestatus
        """
        self.is_running = False
        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=2.0)
            logger.info("Charger-Monitoring gestoppt")
        return True
        
    def _monitor_status(self):
        """
        Hintergrund-Thread zur Überwachung des Ladestatus
        """
        logger.info("Charger-Monitor-Thread gestartet")
        
        while self.is_running:
            try:
                # Aktuellen Ladestatus abfragen
                current_status = gpio.is_charging()
                
                # Status-Änderung erkennen und loggen
                if current_status != self.last_status:
                    if current_status:
                        logger.info("Auto erkannt - Ladevorgang aktiv")
                    else:
                        logger.info("Kein Auto erkannt - Ladepad frei")
                    
                    # Automatische Steuerung, falls aktiviert
                    if self.auto_control_enabled:
                        if current_status:
                            # Auto erkannt, Ladevorgang starten
                            gpio.start_charging()
                        else:
                            # Kein Auto erkannt, Ladevorgang stoppen
                            gpio.stop_charging()
                
                # Status speichern
                self.last_status = current_status
                
                # Warten bis zur nächsten Überprüfung
                time.sleep(CHARGER_STATUS_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Fehler im Monitor-Thread: {str(e)}")
                time.sleep(CHARGER_STATUS_CHECK_INTERVAL)
    
    def enable_auto_control(self, enable=True):
        """
        Aktiviert oder deaktiviert die automatische Steuerung
        
        Args:
            enable (bool): True zum Aktivieren, False zum Deaktivieren
        """
        self.auto_control_enabled = enable
        logger.info(f"Automatische Steuerung {'aktiviert' if enable else 'deaktiviert'}")
        return True
    
    def get_status(self):
        """
        Gibt den aktuellen Ladestatus zurück
        
        Returns:
            dict: Status-Informationen
        """
        is_active = gpio.is_charging()
        return {
            "is_charging": is_active,
            "status": "Lädt" if is_active else "Lädt nicht",
            "auto_control": self.auto_control_enabled,
            "monitoring_active": self.is_running
        }
    
    def cleanup(self):
        """
        Bereinigt Ressourcen beim Beenden
        """
        self.stop_monitoring()
        gpio.cleanup()
        logger.info("ChargerController bereinigt")

# Singleton-Instanz
charger_controller = ChargerController()

def init():
    """
    Initialisiert den ChargerController
    """
    return charger_controller.setup()

def start_monitoring():
    """
    Startet die Überwachung des Ladestatus
    """
    return charger_controller.start_monitoring()

def stop_monitoring():
    """
    Stoppt die Überwachung des Ladestatus
    """
    return charger_controller.stop_monitoring()

def enable_auto_control(enable=True):
    """
    Aktiviert oder deaktiviert die automatische Steuerung
    """
    return charger_controller.enable_auto_control(enable)

def get_status():
    """
    Gibt den aktuellen Ladestatus zurück
    """
    return charger_controller.get_status()

def start_charging():
    """
    Startet den Ladevorgang manuell
    """
    return gpio.start_charging()

def stop_charging():
    """
    Stoppt den Ladevorgang manuell
    """
    return gpio.stop_charging()

def is_charging():
    """
    Prüft, ob ein Auto auf dem Charger steht und geladen wird
    """
    return gpio.is_charging()

def cleanup():
    """
    Bereinigt Ressourcen beim Beenden
    """
    return charger_controller.cleanup()
