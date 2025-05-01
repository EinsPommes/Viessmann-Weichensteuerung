# KI-Tracking-Modelle

Dieses Verzeichnis enthält die Modelle für das KI-gestützte Echtzeit-Tracking von Fahrzeugen.

## Benötigte Dateien

Für die Fahrzeugerkennung werden folgende Dateien benötigt:

1. `efficientdet_lite0_320_ptq_edgetpu.tflite` - Das EfficientDet Lite Modell für den Google Coral Edge TPU
2. `coco_labels.txt` - Die Beschriftungsdatei mit den Klassennamen

## Modelle herunterladen

### EfficientDet Lite für Google Coral

Das EfficientDet Lite Modell für den Google Coral Edge TPU kann von der offiziellen Coral-Website heruntergeladen werden:

```bash
wget https://github.com/google-coral/test_data/raw/master/efficientdet_lite0_320_ptq_edgetpu.tflite
```

### COCO Labels

Die COCO-Labels-Datei kann mit folgendem Befehl heruntergeladen werden:

```bash
wget https://raw.githubusercontent.com/google-coral/test_data/master/coco_labels.txt
```

## Alternativ: Eigene Modelle verwenden

Sie können auch eigene TensorFlow Lite Modelle verwenden. Stellen Sie sicher, dass diese kompatibel mit dem Google Coral Edge TPU sind, wenn Sie den Hardware-Beschleuniger nutzen möchten.

## Verwendung ohne Google Coral

Das System kann auch ohne Google Coral Edge TPU betrieben werden. In diesem Fall wird TensorFlow Lite ohne Hardware-Beschleunigung verwendet, was zu einer langsameren Verarbeitung führen kann.
