import tkinter as tk
from tkinter import ttk, Canvas

class TrackMap:
    def __init__(self, parent):
        self.parent = parent
        self.canvas = Canvas(parent, bg='white', width=800, height=400)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Straßen zeichnen
        self.draw_roads()
        
        # Servos/Barrieren zeichnen
        self.barriers = {}
        self.draw_barriers()
    
    def draw_roads(self):
        # Hauptstraße (horizontal)
        self.canvas.create_line(50, 200, 750, 200, width=20, fill='gray')
        
        # Parkplatz-Zufahrten
        self.canvas.create_line(200, 200, 200, 100, width=20, fill='gray')
        self.canvas.create_line(400, 200, 400, 100, width=20, fill='gray')
        self.canvas.create_line(600, 200, 600, 100, width=20, fill='gray')
        
        # Parkplätze (Rechtecke)
        for x in [150, 350, 550]:
            self.canvas.create_rectangle(x-30, 20, x+30, 80, fill='lightgray')
        
        # Beschriftungen
        self.canvas.create_text(200, 50, text="P1", font=('Arial', 12, 'bold'))
        self.canvas.create_text(400, 50, text="P2", font=('Arial', 12, 'bold'))
        self.canvas.create_text(600, 50, text="P3", font=('Arial', 12, 'bold'))
        
        # Hauptstraßen-Text
        self.canvas.create_text(400, 250, text="Hauptstraße", font=('Arial', 10))
    
    def draw_barriers(self):
        # Barrieren als Linien mit Servos
        barrier_positions = [(200, 150), (400, 150), (600, 150)]
        for i, pos in enumerate(barrier_positions):
            # Servo (Kreis)
            servo = self.canvas.create_oval(pos[0]-8, pos[1]-8, 
                                         pos[0]+8, pos[1]+8, 
                                         fill='red', tags=f'servo_{i+1}')
            
            # Barriere (Linie)
            barrier = self.canvas.create_line(pos[0], pos[1], 
                                           pos[0]+30, pos[1], 
                                           width=3, fill='red',
                                           tags=f'barrier_{i+1}')
            
            self.barriers[i+1] = {'servo': servo, 'barrier': barrier}
            
            # Label für Servo-Nummer
            self.canvas.create_text(pos[0]-20, pos[1], 
                                  text=f'S{i+1}', font=('Arial', 8))
    
    def update_switch(self, switch_id, position):
        """Aktualisiert die Anzeige einer Barriere"""
        if switch_id in self.barriers:
            color = 'green' if position == 'right' else 'red'
            barrier = self.barriers[switch_id]
            
            # Aktualisiere Servo-Farbe
            self.canvas.itemconfig(barrier['servo'], fill=color)
            self.canvas.itemconfig(barrier['barrier'], fill=color)
            
            # Rotiere Barriere
            pos = self.canvas.coords(barrier['servo'])
            center_x = (pos[0] + pos[2]) / 2
            center_y = (pos[1] + pos[3]) / 2
            
            if position == 'right':
                # Barriere offen (vertikal)
                self.canvas.coords(barrier['barrier'],
                                center_x, center_y,
                                center_x, center_y-30)
            else:
                # Barriere geschlossen (horizontal)
                self.canvas.coords(barrier['barrier'],
                                center_x, center_y,
                                center_x+30, center_y)
