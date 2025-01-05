#!/bin/bash

# Warte auf Netzwerk
sleep 10

# Starte die GUI
python3 /home/mika/Viessmann-Weichensteuerung/src/main.py &

# Starte den Webserver
python3 /home/mika/Viessmann-Weichensteuerung/src/web_server.py &

# Warte auf beide Prozesse
wait
