from tkgpio import TkCircuit

configuration = {
    "width": 300, 
    "height": 400,
    "leds": [
        {"x": 50, "y": 40, "name": "LED 1", "pin": 16},
        # {"x": 50, "y": 140, "name": "LED 2", "pin": 17}
    ],
    "motion_sensors": [
        {"x": 100, "y": 40, "name": "Motion Sensor", "pin": 4,
            "detection_radius": 50, "delay_duration": 5, "block_duration": 3},
        # {"x": 100, "y": 140, "name": "Motion Sensor 2", "pin": 5,
            # "detection_radius": 50, "delay_duration": 5, "block_duration": 3}
    ]
}

circuit = TkCircuit(configuration)


@circuit.run
def main():
    import motion
