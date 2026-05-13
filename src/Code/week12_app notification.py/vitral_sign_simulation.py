from tkgpio import TkCircuit

configuration = {
    "name": "Vitral Sign Alert System",
    "width": 500,
    "height": 600,
    
    "leds": [
        {"x": 250, "y": 100, "name": "LED_HR (HR)", "pin": 17},
        {"x": 250, "y": 250, "name": "LED_BS (BS)", "pin": 27},
        {"x": 250, "y": 400, "name": "LED_BP (BP)", "pin": 22}
    ],

    "adc": {
      "mcp_chip": 3008,
      "potentiometers": [
        {"x": 250, "y": 150, "name": "Heart Rate Sensor", "channel": 0},
        {"x": 250, "y": 300, "name": "Blood Sugar Sensor", "channel": 1},
        {"x": 250, "y": 450, "name": "Blood Pressure Sensor", "channel": 2}
      ]  
    },

    "labels": [
        {"x": 250, "y": 30, "text": "Vitral Sign Alert System", "font": ("Arial", 16, "bold")},
        {"x": 250, "y": 80, "text": "High Heart Rate", "font": ("Arial", 10)},
        {"x": 250, "y": 230, "text": "High Blood Sugar", "font": ("Arial", 10)},
        {"x": 250, "y": 380, "text": "High Blood Pressure", "font": ("Arial", 10)},
        {"x": 100, "y": 150, "text": "Heart Rate (BPM)", "font": ("Arial", 10)},
        {"x": 100, "y": 300, "text": "Blood Sugar (mg/dl)", "font": ("Arial", 10)},
        {"x": 100, "y": 450, "text": "Blood Pressure (mmHg)", "font": ("Arial", 10)}
    ]
}

circuit = TkCircuit(configuration)

@circuit.run
def main():
    import vitral_sign

    vitral_sign.main()