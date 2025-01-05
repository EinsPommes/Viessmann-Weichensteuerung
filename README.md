# Viessmann Weichensteuerung

Eine GUI-basierte Steuerung für Servomotoren zur Kontrolle von Parkplatz-Barrieren, entwickelt für den Raspberry Pi.

## Features

- Steuerung von bis zu 16 Servomotoren
- Intuitive grafische Benutzeroberfläche
- Visualisierung der Barrieren-Positionen
- Automatisierungsmöglichkeiten
- Kalibrierungsfunktionen
- Optimiert für 10-Zoll-Display

## Installation

1. Repository klonen:
```bash
git clone https://github.com/EinsPommes/Viessmann-Weichensteuerung.git
cd Viessmann-Weichensteuerung
```

2. Abhängigkeiten installieren:
```bash
sudo apt-get update
sudo apt-get install python3-tk python3-pip
pip3 install RPi.GPIO
```

## Autostart einrichten

1. Startskript ausführbar machen:
```bash
sudo chmod +x /home/mika/Viessmann-Weichensteuerung/start_weichensteuerung.sh
```

2. Service installieren:
```bash
sudo cp /home/mika/Viessmann-Weichensteuerung/weichensteuerung.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable weichensteuerung.service
sudo systemctl start weichensteuerung.service
```

## Verwendung

### Hauptfunktionen

- **Steuerung**: Direktes Steuern der Servos/Barrieren
- **Gleiskarte**: Visuelle Darstellung der Barrieren-Positionen
- **Kalibrierung**: Anpassen der Servo-Positionen
- **Automation**: Automatische Steuerungssequenzen
- **Info & Settings**: Systeminformationen und Einstellungen

### Servo-Steuerung

- Links-Taste: Barriere schließen
- Rechts-Taste: Barriere öffnen
- Status-Anzeige zeigt aktuelle Position

## Hardware-Anforderungen

- Raspberry Pi (getestet mit Raspberry Pi 4)
- 10-Zoll-Display (1024x600)
- Servomotoren (z.B. MG90S)
- Externe Stromversorgung für Servos

## GPIO-Pins

Die Servos sind wie folgt konfiguriert:
- Servo 1: GPIO 15
- Servo 2: GPIO 18
- usw.

## Entwickelt von

- EinsPommes
- Website: Chill-zone.xyz

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.
