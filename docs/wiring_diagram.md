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
