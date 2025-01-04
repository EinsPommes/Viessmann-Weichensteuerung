# Schaltplan für Viessmann Weichensteuerung

## Komponenten-Verbindungen

### PCA9685 PWM-Controller (I2C)
- VCC → Raspberry Pi 5V
- GND → Raspberry Pi GND
- SDA → Raspberry Pi GPIO2 (Pin 3)
- SCL → Raspberry Pi GPIO3 (Pin 5)
- OE → Raspberry Pi GND

### Servomotoren (an PCA9685)
Servomotor 1-16 jeweils:
- Braun/Schwarz → GND
- Rot → 5V vom externen Netzteil
- Orange/Gelb → PWM0-PWM15 am PCA9685

### Hall-Sensoren
Sensor 1:
- VCC → Raspberry Pi 3.3V
- GND → Raspberry Pi GND
- Signal → GPIO17 (Pin 11)

Sensor 2:
- VCC → Raspberry Pi 3.3V
- GND → Raspberry Pi GND
- Signal → GPIO18 (Pin 12)

[... weitere Sensoren analog mit den Pins aus main.py]

### Stromversorgung
5V Netzteil (20A):
- V+ → PCA9685 V+
- V+ → Servomotoren V+ (über Verteilerleiste)
- GND → PCA9685 GND
- GND → Servomotoren GND (über Verteilerleiste)
- GND → Raspberry Pi GND (für gemeinsame Masse)

## GPIO-Pinbelegung Raspberry Pi

| GPIO (BCM) | Pin | Funktion           |
|------------|-----|-------------------|
| 2 (SDA)    | 3   | I2C SDA          |
| 3 (SCL)    | 5   | I2C SCL          |
| 17         | 11  | Hall-Sensor 1    |
| 18         | 12  | Hall-Sensor 2    |
| 27         | 13  | Hall-Sensor 3    |
| 22         | 15  | Hall-Sensor 4    |
| 23         | 16  | Hall-Sensor 5    |
| 24         | 18  | Hall-Sensor 6    |
| 25         | 22  | Hall-Sensor 7    |
| 4          | 7   | Hall-Sensor 8    |
| 5          | 29  | Hall-Sensor 9    |
| 6          | 31  | Hall-Sensor 10   |
| 12         | 32  | Hall-Sensor 11   |
| 13         | 33  | Hall-Sensor 12   |
| 16         | 36  | Hall-Sensor 13   |
| 19         | 35  | Hall-Sensor 14   |
| 20         | 38  | Hall-Sensor 15   |
| 21         | 40  | Hall-Sensor 16   |

## Wichtige Hinweise
1. Verwenden Sie eine separate Stromversorgung für die Servomotoren
2. Stellen Sie sicher, dass alle GND-Verbindungen miteinander verbunden sind
3. Verwenden Sie ausreichend dimensionierte Kabel für die Stromversorgung
4. Schließen Sie die Hall-Sensoren an 3.3V an, NICHT an 5V
5. Prüfen Sie die Polarität aller Verbindungen vor dem Einschalten

## Verkabelungsanleitung für Servos

### Servo-Anschlüsse

#### Grundlegende Verkabelung für jeden Servo
- **Rot**: 5V Stromversorgung
- **Braun/Schwarz**: Ground (GND)
- **Orange/Gelb**: Signal (GPIO)

#### Pin-Belegung für jeden Servo

| Servo | GPIO | Pin | Funktion |
|-------|------|-----|-----------|
| 1 | 17 | 11 | Signal |
| 2 | 18 | 12 | Signal |
| 3 | 27 | 13 | Signal |
| 4 | 22 | 15 | Signal |
| 5 | 23 | 16 | Signal |
| 6 | 24 | 18 | Signal |
| 7 | 25 | 22 | Signal |
| 8 | 4  | 7  | Signal |
| 9 | 5  | 29 | Signal |
| 10| 6  | 31 | Signal |
| 11| 13 | 33 | Signal |
| 12| 19 | 35 | Signal |
| 13| 26 | 37 | Signal |
| 14| 16 | 36 | Signal |
| 15| 20 | 38 | Signal |
| 16| 21 | 40 | Signal |

### Stromversorgung (5V und GND)
Verbinden Sie die roten und schwarzen Kabel wie folgt:
- **5V**: Pin 2 oder 4
- **GND**: Pin 6, 9, 14, 20, 25, 30, 34, oder 39

### Beispiel für Servo 1
1. **Rot** → Pin 2 (5V)
2. **Schwarz** → Pin 6 (GND)
3. **Orange** → Pin 11 (GPIO 17)

## Wichtige Hinweise
1. Stellen Sie sicher, dass der Raspberry Pi ausgeschaltet ist, bevor Sie Verbindungen herstellen
2. Überprüfen Sie die Polarität der Anschlüsse
3. Verwenden Sie eine externe 5V-Stromversorgung für mehrere Servos
4. Verbinden Sie die GND der externen Stromversorgung mit dem GND des Raspberry Pi

## Raspberry Pi GPIO-Layout
```
3V3     (1)  (2)  5V
GPIO2   (3)  (4)  5V
GPIO3   (5)  (6)  GND
GPIO4   (7)  (8)  GPIO14
GND     (9)  (10) GPIO15
GPIO17  (11) (12) GPIO18
GPIO27  (13) (14) GND
GPIO22  (15) (16) GPIO23
3V3     (17) (18) GPIO24
GPIO10  (19) (20) GND
GPIO9   (21) (22) GPIO25
GPIO11  (23) (24) GPIO8
GND     (25) (26) GPIO7
GPIO0   (27) (28) GPIO1
GPIO5   (29) (30) GND
GPIO6   (31) (32) GPIO12
GPIO13  (33) (34) GND
GPIO19  (35) (36) GPIO16
GPIO26  (37) (38) GPIO20
GND     (39) (40) GPIO21
```

## Sicherheitshinweise

1. **Stromversorgung**:
   - NIEMALS die Servos direkt über den Raspberry Pi mit Strom versorgen
   - Immer ein ausreichend dimensioniertes externes Netzteil verwenden
   - Auf gemeinsamen GND zwischen Netzteil und Raspberry Pi achten

2. **Kabelführung**:
   - Signalkabel von Stromkabeln getrennt verlegen
   - Auf sichere Isolierung achten
   - Kabel vor mechanischer Belastung schützen

3. **Überlastschutz**:
   - Sicherung zwischen Netzteil und Servos einbauen
   - Bei Rauchentwicklung sofort Stromversorgung trennen
   - Regelmäßig Kabel und Anschlüsse auf Beschädigungen prüfen

## Fehlersuche

1. **Servo zittert**:
   - Prüfen ob GND korrekt angeschlossen
   - Netzteil auf ausreichende Leistung prüfen
   - PWM-Signal-Qualität überprüfen

2. **Servo bewegt sich nicht**:
   - Signal-Kabel auf korrekten GPIO-Pin prüfen
   - Stromversorgung testen
   - GPIO-Konfiguration in Software überprüfen

3. **Ungleichmäßige Bewegung**:
   - Netzteil auf Stabilität prüfen
   - Kabelquerschnitt kontrollieren
   - Mechanische Blockaden ausschließen
