from gpiozero import Servo, MCP3008, Button, LED, Buzzer
from time import sleep
import signal
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

print("Water Level Alert System is running...")

# Hardware Setup
led_low = LED(17)
led_medium = LED(27)
led_high = LED(22)
servo = Servo(24)
buzzer = Buzzer(25)
water_sensor = MCP3008(0)

# MQTT Control Variables
manual_control = False
forced_servo_position = 0.0

# MQTT Callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("water/control")

def on_message(client, userdata, msg):
    global manual_control, forced_servo_position
    payload = msg.payload.decode()
    
    try:
        # พยายามแปลงค่าเป็น float
        value = float(payload)
        # ตรวจสอบว่าค่าอยู่ในช่วงที่ถูกต้อง (-1.0 ถึง 1.0)
        if -1.0 <= value <= 1.0:
            manual_control = True
            forced_servo_position = value
            print(f"Setting servo position to {value}")
        else:
            print(f"Value {value} out of range (-1.0 to 1.0)")
    except ValueError:
        # ถ้าแปลงเป็น float ไม่ได้ ให้ตรวจสอบคำสั่งแบบสตริง
        command = payload.upper()
        if command == "OPEN":
            manual_control = True
            forced_servo_position = 1.0  # เปิดสุด
            print("Force opening water gate")
        elif command == "CLOSE":
            manual_control = True
            forced_servo_position = -1.0  # ปิดสุด
            print("Force closing water gate")
        elif command == "AUTO":
            manual_control = False
            print("Returning to auto mode")
        else:
            print(f"Unknown command: {payload}")

# MQTT Client Setup
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set('pk', 'YOUR_MQTT_PASSWORD')
client.connect("127.0.0.1", 1883, 60)
client.loop_start()

def main():
    print("System active. Press Ctrl+C to exit.")
    try:
        while True:
            water_level = water_sensor.value
            
            print(f"Water level: {water_level:.2f} ({int(water_level * 100)}%)")
            
            # คุมไฟ
            led_low.on() if water_level >= 0 else led_low.off()
            led_medium.on() if water_level > 0.33 else led_medium.off()
            
            if water_level > 0.66:
                led_high.on()
                buzzer.on()
            else:
                led_high.off()
                buzzer.off()

            # คุม Servo
            if manual_control:
                servo.value = forced_servo_position
            else:
                servo_position = (2 * water_level) - 1
                servo.value = servo_position

            sleep(0.5)
            
    except KeyboardInterrupt:
        client.loop_stop()
        print("\nSystem stopped")

if __name__ == "__main__":
    main()
