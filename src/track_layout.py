import tkinter as tk

class TrackLayout:
    def __init__(self, canvas_width=800, canvas_height=500):
        self.width = canvas_width
        self.height = canvas_height
        
        # Streckenlayout als Dictionary
        self.layout = {
            'switches': {
                # Linke Seite
                1: {'x': 100, 'y': 100},  # Links oben
                2: {'x': 100, 'y': 200},  # Links mitte
                3: {'x': 100, 'y': 300},  # Links unten
                4: {'x': 100, 'y': 400},  # Links ganz unten
                
                # Mittlere Kreuzung oben
                5: {'x': 300, 'y': 150},  # Kreuzung oben links
                6: {'x': 400, 'y': 150},  # Kreuzung oben rechts
                
                # Mittlere Kreuzung unten
                7: {'x': 300, 'y': 350},  # Kreuzung unten links
                8: {'x': 400, 'y': 350},  # Kreuzung unten rechts
                
                # Rechte Seite
                9: {'x': 600, 'y': 100},   # Rechts oben
                10: {'x': 700, 'y': 200},  # Rechts mitte oben
                11: {'x': 600, 'y': 400},  # Rechts unten
                12: {'x': 700, 'y': 300}   # Rechts mitte unten
            },
            'tracks': [
                # Linke vertikale Strecke
                {'from': 1, 'to': 2},
                {'from': 2, 'to': 3},
                {'from': 3, 'to': 4},
                
                # Mittlere Kreuzung oben
                {'from': 1, 'to': 5},
                {'from': 5, 'to': 6},
                {'from': 6, 'to': 9},
                
                # Mittlere Kreuzung unten
                {'from': 4, 'to': 7},
                {'from': 7, 'to': 8},
                {'from': 8, 'to': 11},
                
                # Diagonale Verbindungen
                {'from': 2, 'to': 5},
                {'from': 3, 'to': 7},
                {'from': 6, 'to': 10},
                {'from': 8, 'to': 12}
            ]
        }
    
    def draw(self, canvas, switch_states):
        """Zeichnet das Streckenlayout auf dem Canvas"""
        # Canvas leeren
        canvas.delete("all")
        
        # Gleise zeichnen
        for track in self.layout['tracks']:
            start = self.layout['switches'][track['from']]
            end = self.layout['switches'][track['to']]
            canvas.create_line(start['x'], start['y'], 
                             end['x'], end['y'], 
                             width=2)
        
        # Weichen zeichnen
        for switch_id, pos in self.layout['switches'].items():
            # Weichenstatus abrufen
            state = switch_states.get(switch_id, {'position': 'left', 'sensor_ok': True})
            
            # Farbe basierend auf Sensor-Status
            color = 'green' if state['sensor_ok'] else 'red'
            
            # Weiche als Kreis zeichnen
            canvas.create_oval(pos['x']-10, pos['y']-10,
                             pos['x']+10, pos['y']+10,
                             fill=color, outline='black')
            
            # Weichennummer
            canvas.create_text(pos['x'], pos['y'],
                             text=str(switch_id),
                             fill='white')
            
            # Position anzeigen
            pos_text = "←" if state['position'] == 'left' else "→"
            canvas.create_text(pos['x'], pos['y']-20,
                             text=pos_text,
                             fill='black')
