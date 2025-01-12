from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import asyncio
from functools import wraps
from servo_controller import ServoController
import os

app = Flask(__name__)
CORS(app)

# Logging einrichten
logger = logging.getLogger('web_server')
logger.setLevel(logging.INFO)

def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'web_server.log'),
        maxBytes=1024*1024,
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapped

class WebServer:
    def __init__(self, servo_controller):
        self.servo_controller = servo_controller
        setup_logging()
        
        # Routes definieren
        self.setup_routes()
    
    def setup_routes(self):
        @app.route('/')
        def index():
            """Rendert die Hauptseite"""
            return render_template('index.html')

        @app.route('/api/servo/<int:servo_id>/position', methods=['POST'])
        @async_route
        async def set_position(servo_id):
            try:
                data = request.get_json()
                position = data.get('position')
                
                if position not in ['left', 'right']:
                    return jsonify({'error': 'Ungültige Position'}), 400
                
                await self.servo_controller.set_servo_position(servo_id, position)
                return jsonify({'status': 'success'})
                
            except Exception as e:
                logger.error(f"Fehler beim Setzen der Position: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/servo/<int:servo_id>/position', methods=['GET'])
        def get_position(servo_id):
            try:
                position = self.servo_controller.get_servo_position(servo_id)
                return jsonify({'position': position})
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Position: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/servo/<int:servo_id>/config', methods=['GET'])
        def get_config(servo_id):
            try:
                config = self.servo_controller.get_servo_config(servo_id)
                return jsonify(config)
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Konfiguration: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/servo/<int:servo_id>/config', methods=['POST'])
        def set_config(servo_id):
            try:
                config = request.get_json()
                success = self.servo_controller.set_servo_config(servo_id, **config)
                if success:
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Konfiguration konnte nicht gespeichert werden'}), 500
            except Exception as e:
                logger.error(f"Fehler beim Setzen der Konfiguration: {e}")
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/status')
        def get_status():
            """Liefert den aktuellen Status aller Servos"""
            try:
                status = {}
                for servo_id in range(16):
                    state = servo_controller.servo_states.get(servo_id, {})
                    status[servo_id] = {
                        'position': state.get('position', None),
                        'is_moving': state.get('is_moving', False),
                        'last_error': state.get('last_error', None),
                        'config': {
                            'left_angle': servo_controller.servo_config[servo_id]['left_angle'],
                            'right_angle': servo_controller.servo_config[servo_id]['right_angle'],
                            'speed': servo_controller.servo_config[servo_id]['speed']
                        }
                    }
                return jsonify({'status': status, 'success': True})
            except Exception as e:
                return jsonify({'error': str(e), 'success': False}), 500

        @app.route('/api/calibrate/<int:servo_id>', methods=['POST'])
        def calibrate_servo(servo_id):
            """Kalibriert einen Servo mit den gegebenen Werten"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Keine Daten erhalten', 'success': False}), 400
                    
                # Konfiguration aktualisieren
                servo_controller.set_servo_config(
                    servo_id,
                    left_angle=float(data.get('left_angle', 0)),
                    right_angle=float(data.get('right_angle', 180)),
                    speed=float(data.get('speed', 0.5))
                )
                
                return jsonify({'message': 'Kalibrierung erfolgreich', 'success': True})
            except Exception as e:
                return jsonify({'error': str(e), 'success': False}), 500

        @app.route('/static/<path:path>')
        def send_static(path):
            return send_from_directory('static', path)
    
    def run(self, host='0.0.0.0', port=5000):
        app.run(host=host, port=port)

def init_controller():
    try:
        servo_controller = ServoController()
        logger.info("Servo Controller erfolgreich initialisiert")
        return servo_controller
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des Servo Controllers: {str(e)}")
        raise

def run_server():
    try:
        servo_controller = init_controller()
        web_server = WebServer(servo_controller)
        web_server.run()
    except Exception as e:
        logger.error(f"Fehler beim Starten des Servers: {str(e)}")
        raise

if __name__ == '__main__':
    run_server()
