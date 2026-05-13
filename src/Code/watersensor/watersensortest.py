
from gpiozero import InputDevice
import time

pin = InputDevice(17, pull_up=True)  

alert_trigger = False

while True:
    if pin.is_active:
        print("Water detected")
    else:
        print("No water detected")
        
    time.sleep(1)
