#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration file for Viessmann Weichensteuerung with CarMotion InduktivCharger
"""

# GPIO Pin Konfiguration für Viessmann 8408 CarMotion InduktivCharger
CHARGER_STATUS_PIN = 17    # Input: Liest den Ladezustand (HIGH = lädt)
CHARGER_CONTROL_PIN = 27   # Output: Aktiviert/deaktiviert den Ladevorgang

# Zeitintervalle (in Sekunden)
CHARGER_STATUS_CHECK_INTERVAL = 1.0  # Intervall für die Überprüfung des Ladestatus
