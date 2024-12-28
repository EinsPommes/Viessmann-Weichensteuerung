# Viessmann Weichensteuerung

Dieses Projekt implementiert ein Steuerungssystem für 16 Servomotoren zur Kontrolle von unsichtbaren Weichen eines Viessmann Car Motion Systems. Das System verwendet einen Raspberry Pi 4 zur Steuerung und Hall-Sensoren zur Positionsüberwachung.

## Hardware-Anforderungen

- Raspberry Pi 4
- 16x Servomotoren (SG90 oder MG996R)
- 1-2x PWM-Expander (PCA9685)
- 16x Hall-Sensoren (A3144)
- Magnete für die Positionsbestimmung
- 5V Netzteil (20A)
- Verbindungskabel

## Installation

1. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

2. GPIO-Pins konfigurieren:
   - Die Hall-Sensoren sind standardmäßig an den Pins 17-21 angeschlossen
   - Die Konfiguration kann in `main.py` angepasst werden

## Verwendung

Das Programm wird gestartet mit:
```bash
python src/main.py
```

Die GUI zeigt den Status aller Weichen an:
- Grün: Weiche korrekt positioniert
- Rot: Position stimmt nicht mit Hall-Sensor überein
- ✓/✗: Hall-Sensor-Status

## Projektstruktur

- `src/servo_controller.py`: Steuerung der Servomotoren
- `src/hall_sensor.py`: Verwaltung der Hall-Sensoren
- `src/gui.py`: Grafische Benutzeroberfläche
- `src/main.py`: Hauptprogramm

## Schaltplan

[Hier wird später der Schaltplan eingefügt]

## Erweiterungsmöglichkeiten

- Automatische Weichenstellung basierend auf Fahrzeugpositionen
- Speichern und Laden von Weichenkonfigurationen
- Integration in übergeordnete Steuerungssysteme

## Lizenz

[Ihre Lizenz hier]
