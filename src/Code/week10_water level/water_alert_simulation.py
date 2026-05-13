from tkgpio import TkCircuit

configuration = {
    "name": "Water Level Alert System",
    "width": 700,
    "height": 400,
    
    "leds": [
        {"x": 105, "y": 80, "name": "LED1 (Low)", "pin": 17},
        {"x": 205, "y": 80, "name": "LED2 (Medium)", "pin": 27},
        {"x": 305, "y": 80, "name": "LED3 (High)", "pin": 22}
    ],
    "servos": [
        {"x": 500, "y": 80, "name": "Water Gate Servo", "pin": 24, "min_angle": -90, "max_angle": 90, "initial_angle": 0}
    ],
    "buzzers": [
        {"x": 400, "y": 80, "name": "Alert Buzzer", "pin": 25}
    ],
    "adc": {
      "mcp_chip": 3008,
      "potentiometers": [
        {"x": 250, "y": 200, "name": "Water Level Sensor", "channel": 0}
      ]  
    },
    "labels": [
        {"x": 15, "y": 25, "text": "Water Level Alert System", "font": ("Arial", 16, "bold")},
        {"x": 250, "y": 180, "text": "Water Level Sensor", "font": ("Arial", 10)},
        {"x": 105, "y": 60, "text": "Low", "font": ("Arial", 10)},
        {"x": 205, "y": 60, "text": "Medium", "font": ("Arial", 10)},
        {"x": 305, "y": 60, "text": "High", "font": ("Arial", 10)},
        {"x": 500, "y": 60, "text": "Water Gate", "font": ("Arial", 10)},
        {"x": 400, "y": 60, "text": "Buzzer", "font": ("Arial", 10)},
        {"x": 15, "y": 280, "text": "Low: 0-33% | Medium: 34-66% | High: 67-100%", "font": ("Arial", 10)}
    ]
}

circuit = TkCircuit(configuration)

@circuit.run
def main():
    import water_alert

    water_alert.main()