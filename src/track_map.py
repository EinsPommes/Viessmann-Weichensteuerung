import tkinter as tk
from tkinter import ttk, Canvas

class TrackMap:
    def __init__(self, parent):
        self.parent = parent
        
        # Mittlere Kartengröße
        self.canvas = Canvas(parent, bg='white', width=700, height=350)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame für die Legende
        legend_frame = ttk.Frame(parent)
        legend_frame.grid(row=1, column=0, pady=5)
        
        # Legende
        ttk.Label(legend_frame, text="Rot = Geschlossen", 
                 font=('TkDefaultFont', 10)).grid(row=0, column=0, padx=15)
        ttk.Label(legend_frame, text="Grün = Offen", 
                 font=('TkDefaultFont', 10)).grid(row=0, column=1, padx=15)
        
        # Straßen zeichnen
        self.draw_roads()
        
        # Servos/Barrieren zeichnen
        self.barriers = {}
        self.draw_barriers()
    
    def draw_roads(self):
        # Hauptstraße (horizontal)
        self.canvas.create_line(50, 175, 650, 175, width=25, fill='gray')
        
        # Parkplatz-Zufahrten
        self.canvas.create_line(200, 175, 200, 75, width=25, fill='gray')
        self.canvas.create_line(500, 175, 500, 75, width=25, fill='gray')
        
        # Parkplätze (Rechtecke)
        for x in [200, 500]:
            self.canvas.create_rectangle(x-40, 30, x+40, 65, fill='lightgray')
        
        # Beschriftungen
        self.canvas.create_text(200, 47, text="P1", font=('Arial', 12, 'bold'))
        self.canvas.create_text(500, 47, text="P2", font=('Arial', 12, 'bold'))
        
        # Hauptstraßen-Text
        self.canvas.create_text(350, 220, text="Hauptstraße", font=('Arial', 10))
    
    def draw_barriers(self):
        # Barrieren als Linien mit Servos
        barrier_positions = [(200, 125), (500, 125)]
        for i, pos in enumerate(barrier_positions):
            # Servo
            servo = self.canvas.create_oval(pos[0]-10, pos[1]-10, 
                                         pos[0]+10, pos[1]+10, 
                                         fill='red', tags=f'servo_{i+1}')
            
            # Barriere
            barrier = self.canvas.create_line(pos[0], pos[1], 
                                           pos[0]+35, pos[1], 
                                           width=3, fill='red',
                                           tags=f'barrier_{i+1}')
            
            self.barriers[i+1] = {'servo': servo, 'barrier': barrier}
            
            # Label für Servo-Nummer
            self.canvas.create_text(pos[0]-20, pos[1], 
                                  text=f'S{i+1}', font=('Arial', 10))
    
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
                                center_x, center_y-35)
            else:
                # Barriere geschlossen (horizontal)
                self.canvas.coords(barrier['barrier'],
                                center_x, center_y,
                                center_x+35, center_y)
