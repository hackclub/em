#This code is provided by Hack Club for use in our #accelerate program.
#It is licensed under the MIT License (see LICENSE).
#Feel free to use and modify it as you see fit!

#Remember to install Hackatime, and use it to track your coding time!

#Your goal is to think outside the box. Think about what cool features you could add to this model.

#You have two weeks for this. You must submit your progress by the end of the first week, and your final project by the end of the second week.

import math, threading
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Coulomb's constant (scaled for visualization)
K = 5000

class PointCharge:
    def __init__(self, x: float, y: float, charge: float, mass: float = 1.0, 
                 vx: float = 0, vy: float = 0, fixed: bool = False):
        self.x = x
        self.y = y
        self.charge = charge  # Positive or negative
        self.mass = mass
        self.vx = vx
        self.vy = vy
        self.fixed = fixed  # Fixed charges don't move
        self.radius = 12
    
    def get_state(self):
        return {
            'x': self.x,
            'y': self.y,
            'charge': self.charge,
            'vx': self.vx,
            'vy': self.vy,
            'fixed': self.fixed,
            'radius': self.radius
        }

class EMSimulation:
    def __init__(self):
        self.charges = []
        self.width = 800
        self.height = 600
        self.damping = 0.995  # Slight damping to prevent infinite acceleration
        self.reset()
    
    def reset(self):
        self.charges = [
            # Two particles shot towards each other from opposite sides
            PointCharge(50, 300, charge=5.0, mass=1.0, vx=200, vy=0, fixed=False),
            PointCharge(750, 300, charge=5.0, mass=1.0, vx=-200, vy=0, fixed=False),
            # Additional particles for more chaos
            PointCharge(400, 50, charge=-4.0, mass=0.8, vx=0, vy=180, fixed=False),
            PointCharge(400, 550, charge=-4.0, mass=0.8, vx=0, vy=-180, fixed=False),
        ]
    
    def calculate_force(self, charge1: PointCharge, charge2: PointCharge):
        """Calculate electrostatic force on charge1 due to charge2"""
        dx = charge1.x - charge2.x
        dy = charge1.y - charge2.y
        distance_sq = dx * dx + dy * dy
        distance = math.sqrt(distance_sq)
        
        if distance < 20:  # Minimum distance to prevent singularity
            distance = 20
            distance_sq = 400
        
        # Coulomb's law: F = k * q1 * q2 / r^2
        force_magnitude = K * charge1.charge * charge2.charge / distance_sq
        
        # Force direction (unit vector from charge2 to charge1)
        fx = force_magnitude * dx / distance
        fy = force_magnitude * dy / distance
        
        return fx, fy
    
    def step(self, dt: float = 0.016):
        # Calculate forces on each movable charge
        for i, charge in enumerate(self.charges):
            if charge.fixed:
                continue
            
            total_fx = 0
            total_fy = 0
            
            # Sum forces from all other charges
            for j, other in enumerate(self.charges):
                if i != j:
                    fx, fy = self.calculate_force(charge, other)
                    total_fx += fx
                    total_fy += fy
            
            # F = ma -> a = F/m
            ax = total_fx / charge.mass
            ay = total_fy / charge.mass
            
            # Update velocity
            charge.vx += ax * dt
            charge.vy += ay * dt
            
            # Apply damping
            charge.vx *= self.damping
            charge.vy *= self.damping
            
            # Update position
            charge.x += charge.vx * dt
            charge.y += charge.vy * dt
            
            # Bounce off walls
            if charge.x < charge.radius:
                charge.x = charge.radius
                charge.vx *= -0.8
            elif charge.x > self.width - charge.radius:
                charge.x = self.width - charge.radius
                charge.vx *= -0.8
            
            if charge.y < charge.radius:
                charge.y = charge.radius
                charge.vy *= -0.8
            elif charge.y > self.height - charge.radius:
                charge.y = self.height - charge.radius
                charge.vy *= -0.8
    
    def get_state(self):
        return {
            'charges': [c.get_state() for c in self.charges]
        }

# Create simulation instance
simulation = EMSimulation()

def run_simulation():
    while True:
        simulation.step()
        threading.Event().wait(0.016)  # ~60 FPS

# Start simulation in background thread
threading.Thread(target=run_simulation, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html',
                         width=simulation.width,
                         height=simulation.height)

@app.route('/state')
def state():
    return jsonify(simulation.get_state())

@app.route('/reset')
def reset():
    simulation.reset()
    return jsonify({'status': 'ok'})
