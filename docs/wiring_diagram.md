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

## Verkabelungsanleitung für MG90S Servos

Der MG90S Servo hat drei Kabel:
- **Braun/Schwarz**: GND (Ground/Masse)
- **Rot**: VCC (5V Stromversorgung)
- **Orange/Gelb**: Signal (PWM vom GPIO)

### Anschluss an Raspberry Pi

#### Servo-Anschlüsse
1. **GND (Braun/Schwarz)**
   - An einen GND-Pin des Raspberry Pi (Pin 6, 9, 14, 20, 25, 30, 34 oder 39)
   - Alle Servos können einen gemeinsamen GND-Pin nutzen

2. **VCC (Rot)**
   - An 5V vom externen Netzteil
   - NICHT direkt an 5V des Raspberry Pi anschließen!
   - Alle Servos können gemeinsam am 5V-Netzteil angeschlossen werden

3. **Signal (Orange/Gelb)**
   - An die entsprechenden GPIO-Pins laut Tabelle:

| Weiche | GPIO-Pin | GPIO-Nr. (BCM) | Pin-Nr. (Board) |
|--------|----------|----------------|-----------------|
| 1      | GPIO17   | 17            | 11             |
| 2      | GPIO18   | 18            | 12             |
| 3      | GPIO27   | 27            | 13             |
| 4      | GPIO22   | 22            | 15             |
| 5      | GPIO23   | 23            | 16             |
| 6      | GPIO24   | 24            | 18             |
| 7      | GPIO25   | 25            | 22             |
| 8      | GPIO4    | 4             | 7              |
| 9      | GPIO5    | 5             | 29             |
| 10     | GPIO6    | 6             | 31             |
| 11     | GPIO13   | 13            | 33             |
| 12     | GPIO19   | 19            | 35             |

### Stromversorgung

**WICHTIG**: Die Servos müssen über ein externes 5V-Netzteil versorgt werden!

1. **Netzteil-Anforderungen**:
   - Spannung: 5V DC
   - Strom: Mindestens 2A für 12 Servos
   - Empfohlen: 5V 3A Netzteil für Reserven

2. **Verkabelung Netzteil**:
   - Netzteil GND → Gemeinsamer GND mit Raspberry Pi
   - Netzteil 5V → Servos VCC (Rot)

### Beispiel-Verkabelung für einen Servo

```
Raspberry Pi                MG90S Servo
-------------             --------------
GPIO17 (Pin 11) ----→ Signal (Orange/Gelb)
GND (Pin 6)     ----→ GND (Braun/Schwarz)

Externes Netzteil         MG90S Servo
----------------        --------------
5V              ----→ VCC (Rot)
GND             ----→ GND (Braun/Schwarz)
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
