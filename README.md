# Viessmann Weichensteuerung

Eine Raspberry Pi-basierte Steuerung für Modellbahn-Weichen mit MG90S Servomotoren.

## Features

- Steuerung von bis zu 12 Weichen
- Grafische Benutzeroberfläche mit Streckenlayout
- Automatik-Modus für vorprogrammierte Abläufe
- Hall-Sensor-Überwachung für Weichenpositionen
- Konfigurierbare Servo-Positionen

## Hardware

### Benötigte Komponenten

- Raspberry Pi (3B+ oder neuer empfohlen)
- MG90S Servomotoren (bis zu 12 Stück)
- Hall-Sensoren (optional)
- 5V Netzteil (min. 2A)

### MG90S Servomotor Spezifikationen

- Betriebsspannung: 4.8V-6V
- Drehmoment: 1.8kg/cm (4.8V) bis 2.2kg/cm (6V)
- Geschwindigkeit: 0.1s/60° (4.8V)
- Winkelbereich: 0° bis 180°
- Größe: 22.5x12x35.5mm
- Gewicht: 13.4g
- Metallgetriebe für lange Haltbarkeit

### GPIO-Anschlüsse

Die Servos sind wie folgt an die GPIO-Pins angeschlossen:

| Weiche | GPIO-Pin |
|--------|----------|
| 1      | 17       |
| 2      | 18       |
| 3      | 27       |
| 4      | 22       |
| 5      | 23       |
| 6      | 24       |
| 7      | 25       |
| 8      | 4        |
| 9      | 5        |
| 10     | 6        |
| 11     | 13       |
| 12     | 19       |

## Software

### Installation

1. Repository klonen:
```bash
git clone https://github.com/EinsPommes/Viessmann-Weichensteuerung.git
cd Viessmann-Weichensteuerung
```

2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

3. Programm starten:
```bash
python src/main.py
```

### Konfiguration

Die Servo-Positionen können in der `config.json` angepasst werden:

```json
{
    "servo_pins": [17, 18, 27, 22, 23, 24, 25, 4, 5, 6, 13, 19],
    "servo_left_angles": [6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5],
    "servo_right_angles": [8.5, 8.5, 8.5, 8.5, 8.5, 8.5, 8.5, 8.5, 8.5, 8.5, 8.5, 8.5]
}
```

- `servo_pins`: GPIO-Pins für die Servos
- `servo_left_angles`: PWM-Werte für die linke Position (~45°)
- `servo_right_angles`: PWM-Werte für die rechte Position (~135°)

## Bedienung

1. **Manuelle Steuerung**
   - Klicken Sie auf die Weichenschalter in der GUI
   - Grün = Position korrekt
   - Rot = Positionsfehler

2. **Automatik-Modus**
   - Wählen Sie einen Modus (Sequentiell/Zufällig)
   - Start/Stop über die Buttons

3. **Test-Funktion**
   - Jede Weiche kann einzeln getestet werden
   - Prüft Servo-Bewegung und Sensor-Status

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.

## Autor

Entwickelt von EinsPommes
