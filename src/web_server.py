from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import asyncio
from functools import wraps
from servokit_controller import ServoKitController
import os
import socket

app = Flask(__name__)
CORS(app)

# Logging einrichten
logger = logging.getLogger('car_motion_system')
logger.setLevel(logging.INFO)

def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'car_motion.log'),
        maxBytes=1024*1024,
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def get_ip_address():
    """Ermittelt die IP-Adresse des Servers"""
    try:
        # Erstelle einen Socket und verbinde mit einem externen Server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"  # Fallback auf localhost

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
    def __init__(self, servo_controller=None):
        # Erstelle neuen Controller wenn keiner übergeben wurde
        self.servo_controller = servo_controller or ServoKitController()
        setup_logging()
        
        # Routes definieren
        self.setup_routes()
        
    def setup_routes(self):
        @app.route('/')
        def index():
            return render_template('index.html')
            
        @app.route('/api/ip')
        def ip():
            """Liefert die IP-Adresse des Servers"""
            return jsonify({
                'ip': f"{get_ip_address()}:5000"
            })
            
        @app.route('/api/servos', methods=['GET'])
        def get_servos():
            """Liefert Status aller Servos"""
            try:
                servos = {}
                for i in range(16):
                    state = self.servo_controller.servo_states.get(str(i), {})
                    servos[str(i)] = {
                        'position': state.get('position', 'unknown'),
                        'initialized': state.get('initialized', False),
                        'error': state.get('error', False),
                        'status': state.get('status', 'unknown')
                    }
                return jsonify(servos)
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Servos: {e}")
                return jsonify({'error': str(e)}), 500
                
        @app.route('/api/servo/<int:servo_id>', methods=['POST'])
        def set_servo(servo_id):
            """Setzt die Position eines Servos"""
            try:
                data = request.get_json()
                position = data.get('position')
                
                if position not in ['left', 'right']:
                    return jsonify({'error': 'Ungültige Position'}), 400
                    
                self.servo_controller.move_servo(servo_id, position)
                return jsonify({'status': 'success'})
                
            except Exception as e:
                logger.error(f"Fehler beim Setzen von Servo {servo_id}: {e}")
                return jsonify({'error': str(e)}), 500
                
        @app.route('/api/servo/<int:servo_id>', methods=['GET'])
        def get_servo(servo_id):
            """Liefert Status eines Servos"""
            try:
                state = self.servo_controller.servo_states.get(str(servo_id), {})
                return jsonify({
                    'position': state.get('position', 'unknown'),
                    'initialized': state.get('initialized', False),
                    'error': state.get('error', False),
                    'status': state.get('status', 'unknown')
                })
            except Exception as e:
                logger.error(f"Fehler beim Abrufen von Servo {servo_id}: {e}")
                return jsonify({'error': str(e)}), 500

def init_controller():
    """Initialisiert den ServoController"""
    try:
        return ServoKitController()
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des ServoControllers: {e}")
        raise

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Startet den Car Motion System Server"""
    try:
        servo_controller = init_controller()
        server = WebServer(servo_controller)
        logger.info(f"Car Motion System startet auf http://{get_ip_address()}:{port}")
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Fehler beim Starten des Servers: {e}")
        raise

if __name__ == '__main__':
    run_server()
