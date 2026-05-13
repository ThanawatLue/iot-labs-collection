from gpiozero import Servo
from time import sleep
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

servo = Servo(17)
forced_servo_position = 0.0

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("servo_control/servo_position")

def on_message(client, userdata, msg):
    global forced_servo_position
    file = msg.payload.decode()
    
    if "filament_type = ABS" in file:
        forced_servo_position = 1.0
        print("Servo motor ON")
    else:
        forced_servo_position = -1.0
        print(f"Servo motor OFF")

def main():
    print("System active. Press Ctrl+C to exit.")

    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set('user', '123456')
    client.connect("192.168.18.43", 1883, 60)
    client.loop_start()

    try:
        while True:
            servo.value = forced_servo_position
            sleep(1)
            
    except KeyboardInterrupt:
        client.loop_stop()
        print("\nSystem stopped")

if __name__ == "__main__":
    main()
