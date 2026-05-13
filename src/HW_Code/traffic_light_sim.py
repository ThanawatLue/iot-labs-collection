from tkgpio import TkCircuit

configuration = {
    "width": 400,
    "height": 300,
    "leds": [
        {"x": 200, "y": 50, "name": "RED", "pin": 17},
        {"x": 200, "y": 100, "name": "YELLOW", "pin": 27},
        {"x": 200, "y": 150, "name": "GREEN", "pin": 22}
    ],
    "buttons": [
        {"x": 100, "y": 230, "name": "Pedestrian Crossing", "pin": 11}
    ],
    "title": "Traffic Light Simulation"
}

circuit = TkCircuit(configuration)

@circuit.run
def main():
    import traffic_light
    
if __name__ == "__main__":
    print("Starting Traffic Light Simulation...")