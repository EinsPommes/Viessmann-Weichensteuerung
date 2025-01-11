#!/bin/bash

# Prüfe Berechtigungen
if [ ! -w /home/mika/Viessmann-Weichensteuerung ]; then
    echo "Fehler: Keine Schreibrechte im Projektverzeichnis"
    exit 1
fi

# Aktiviere Python-Umgebung falls vorhanden
if [ -f /home/mika/Viessmann-Weichensteuerung/venv/bin/activate ]; then
    source /home/mika/Viessmann-Weichensteuerung/venv/bin/activate
fi

# Wechsle in das Projektverzeichnis
cd /home/mika/Viessmann-Weichensteuerung/src || exit 1

# Prüfe ob Python-Abhängigkeiten installiert sind
if ! python3 -c "import RPi.GPIO" 2>/dev/null; then
    echo "Fehler: RPi.GPIO nicht installiert"
    exit 1
fi

# Warte auf Netzwerk
sleep 10

# Starte die GUI
python3 main.py &

# Starte den Webserver
python3 web_server.py &

# Warte auf beide Prozesse
wait
