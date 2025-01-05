#!/bin/bash

# Warte auf X-Server
sleep 10

# Setze DISPLAY Variable
export DISPLAY=:0

# Starte das Programm
cd /home/mika/Viessmann-Weichensteuerung/src
python3 main.py
