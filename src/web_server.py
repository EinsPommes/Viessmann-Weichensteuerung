from flask import Flask, render_template, jsonify, request
from servo_controller import ServoController
import threading
import logging

app = Flask(__name__)
servo_controller = None

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_controller():
    global servo_controller
    try:
        servo_controller = ServoController()
        logger.info("Servo Controller erfolgreich initialisiert")
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des Servo Controllers: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/servo/<int:servo_id>/<position>', methods=['POST'])
def set_servo_position(servo_id, position):
    try:
        if position not in ['left', 'right']:
            return jsonify({'error': 'Ungültige Position'}), 400
        
        servo_controller.set_servo_position(servo_id, position)
        return jsonify({'success': True, 'message': f'Servo {servo_id} auf Position {position} gesetzt'})
    except Exception as e:
        logger.error(f"Fehler beim Setzen der Servo-Position: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/servos/status', methods=['GET'])
def get_servo_status():
    try:
        status = {}
        for i in range(16):
            status[i] = servo_controller.get_servo_position(i)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Servo-Status: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_server():
    try:
        init_controller()
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Fehler beim Starten des Servers: {str(e)}")
        raise

if __name__ == '__main__':
    run_server()
