#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging-Modul für Viessmann Weichensteuerung mit CarMotion InduktivCharger
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Standard-Konfiguration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_FILE = 'weichensteuerung.log'
LOG_DIR = 'logs'

def setup_logging(log_level=DEFAULT_LOG_LEVEL, log_file=DEFAULT_LOG_FILE, console=True):
    """
    Richtet das Logging-System ein
    
    Args:
        log_level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name der Log-Datei
        console: Ob Logs auch auf der Konsole ausgegeben werden sollen
    """
    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Formatter erstellen
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    # Log-Verzeichnis erstellen, falls es nicht existiert
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    
    # Datei-Handler hinzufügen
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=1024*1024,  # 1 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Konsolen-Handler hinzufügen, wenn gewünscht
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Logger für dieses Modul erstellen
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialisiert (Level: {logging.getLevelName(log_level)})")
    
    return root_logger

def get_logger(name):
    """
    Gibt einen benannten Logger zurück
    
    Args:
        name: Name des Loggers
        
    Returns:
        Logger-Instanz
    """
    return logging.getLogger(name)
