from tkgpio import TkCircuit

configuration = {
    "width": 300,
    "height": 400,
    "buttons": [
        {"x": 50, "y": 130, "name": "Press to simulate water leak!", "pin": 17}
    ]
}

circuit = TkCircuit(configuration)


@circuit.run
def main():
    import watersensortest