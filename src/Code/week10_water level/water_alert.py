from gpiozero import Servo, MCP3008, Button, LED, Buzzer
from time import sleep
import signal

print("Water Level Alert System is running...")

led_low = LED(17)    
led_medium = LED(27)    
led_high = LED(22)
servo = Servo(24)     
buzzer = Buzzer(25)
water_sensor = MCP3008(0) 

def main():
    print("System active. Press Ctrl+C to exit.")

    while True:
        water_level = water_sensor.value
        print(f"Water level: {water_level:.2f} ({int(water_level * 100)}%)")
        
        # (Low) (0-33%)
        if water_level >= 0:
            led_low.on()
        else:
            led_low.off()
            
        # Medium (34-66%)
        if water_level > 0.33:
            led_medium.on()
        else:
            led_medium.off()
            
        # High (67-100%)
        if water_level > 0.66:
            led_high.on()
            buzzer.on()
        else:
            led_high.off()
            buzzer.off()
        
        servo_position = (2 * water_level) - 1
        servo.value = servo_position
        
        sleep(0.5)

if __name__ == "__main__":
    main()