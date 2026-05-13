from gpiozero import LED, Button
from time import sleep

red_light = LED(17)
yellow_light = LED(27)
green_light = LED(22)

pedestrian_button = Button(11)

# initial
red_light.on()
yellow_light.off()
green_light.off()

auto_mode = True
red_time = 5
yellow_time = 2
green_time = 5
pedestrian_requested = False

def pedestrian_crossing_request():
    global pedestrian_requested
    print("Pedestrian requested to cross!")
    pedestrian_requested = True

# กำหนดให้เรียกฟังก์ชันเมื่อกดปุ่ม
pedestrian_button.when_pressed = pedestrian_crossing_request

def traffic_light_sequence():
    global pedestrian_requested
    
    while True:
        # ไฟแดง
        red_light.on()
        yellow_light.off()
        green_light.off()
        print("Red light: Stop")
        sleep(red_time)
        
        # ถ้าไม่มีคนกดปุ่มข้ามถนน ไฟจะเปลี่ยนตามปกติ
        if auto_mode or pedestrian_requested:
            # ไฟเขียว
            red_light.off()
            yellow_light.off()
            green_light.on()
            print("Green light: Go")
            sleep(green_time)
            
            # ไฟเหลือง
            red_light.off()
            yellow_light.on()
            green_light.off()
            print("Yellow light: Prepare to stop")
            sleep(yellow_time)
            
            pedestrian_requested = False

try:
    traffic_light_sequence()
except KeyboardInterrupt:
    red_light.off()
    yellow_light.off()
    green_light.off()
    print("\nTraffic light simulation stopped")