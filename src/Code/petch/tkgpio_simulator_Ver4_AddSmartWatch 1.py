from tkinter import Tk, Label, Button, Scale, HORIZONTAL
from PIL import Image, ImageTk
from tkgpio import TkCircuit
from gpiozero import PWMLED
import threading
import socket
import json
import re
import numpy as np
import cv2
from collections import deque
from time import sleep
from ultralytics import YOLO
import paho.mqtt.client as mqtt

# ---------- CONFIG GUI ----------
config = {
    "width": 900,
    "height": 450,
    "leds": [
        {"x": 800, "y": 60, "name": "LED", "pin": 18}
    ]
}
circuit = TkCircuit(config)

# ---------- MQTT CONFIG ----------
# MQTT_BROKER = "172.20.10.12"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/status"

# Initialize MQTT client
mqtt_client = mqtt.Client()
try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Start MQTT client loop in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
    mqtt_thread.start()
    print("✅ MQTT Connected to", MQTT_BROKER)
except Exception as e:
    print(f"❌ MQTT Connection failed: {e}")

# Function to publish data to MQTT
def publish_mqtt(data):
    try:
        json_data = json.dumps(data)
        mqtt_client.publish(MQTT_TOPIC, json_data)
    except Exception as e:
        print(f"❌ MQTT Publish error: {e}")

# ---------- SENSOR CONFIG ----------
# UDP_IP = "172.20.10.12"
UDP_IP = "0.0.0.0"
UDP_PORT = 6666
accel_status = "🙆 ยังไม่นอน"
accel_history = deque(maxlen=20)
gyro_history = deque(maxlen=20)
accel_buffer = ""
accel_x = accel_y = accel_z = accel_std = 0.0
gyro_x = gyro_y = gyro_z = gyro_std = 0.0

def extract_json(text):
    return re.findall(r'\{.*?\}', text, re.DOTALL)

def compute_stability(hist, value, threshold):
    hist.append(value)
    if len(hist) == hist.maxlen:
        std = np.std(hist)
        return std, std < threshold
    return 0.0, False

def sensor_thread():
    global accel_status, accel_buffer, accel_x, accel_y, accel_z, accel_std
    global gyro_x, gyro_y, gyro_z, gyro_std

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    while True:
        try:
            data, _ = sock.recvfrom(4096)
            chunk = data.decode("utf-8", errors="ignore")
            accel_buffer += chunk
            json_objects = extract_json(accel_buffer)
            for obj_str in json_objects:
                try:
                    d = json.loads(obj_str)
                    ax = float(d.get("accelerometerAccelerationX", 0))
                    ay = float(d.get("accelerometerAccelerationY", 0))
                    az = float(d.get("accelerometerAccelerationZ", 0))
                    gx = float(d.get("gyroRotationX", d.get("gyroscopeRotationX", 0)))
                    gy = float(d.get("gyroRotationY", d.get("gyroscopeRotationY", 0)))
                    gz = float(d.get("gyroRotationZ", d.get("gyroscopeRotationZ", 0)))

                    accel_x, accel_y, accel_z = ax, ay, az
                    gyro_x, gyro_y, gyro_z = gx, gy, gz

                    mag_accel = np.sqrt(ax**2 + ay**2 + az**2)
                    mag_gyro = np.sqrt(gx**2 + gy**2 + gz**2)

                    accel_std, accel_still = compute_stability(accel_history, mag_accel, threshold=0.05)
                    gyro_std, gyro_stable = compute_stability(gyro_history, mag_gyro, threshold=0.1)

                    if accel_still and gyro_stable and -1.1 < az < -0.9:
                        accel_status = "🛌 กำลังนอนนิ่ง"
                    else:
                        accel_status = "🙆 ยังไม่นอน"
                        
                    # Send sensor data to MQTT
                    sensor_data = {
                        "accel_status": accel_status,
                        "accel_x": accel_x,
                        "accel_y": accel_y, 
                        "accel_z": accel_z,
                        "accel_std": accel_std,
                        "gyro_x": gyro_x,
                        "gyro_y": gyro_y,
                        "gyro_z": gyro_z,
                        "gyro_std": gyro_std
                    }
                    publish_mqtt(sensor_data)

                except Exception:
                    continue

            if json_objects:
                last_obj = json_objects[-1]
                idx = accel_buffer.rfind(last_obj) + len(last_obj)
                accel_buffer = accel_buffer[idx:]

        except Exception as e:
            print("⚠️ Sensor Thread Error:", e)

# ---------- FADE FUNCTION ----------
def fade_out(led, duration=5.0, steps=20):
    for i in range(steps):
        led.value = 1 - (i / steps)
        sleep(duration / steps)
    led.off()

def fade_in(led, duration=5.0, steps=20):
    for i in range(steps):
        led.value = i / steps
        sleep(duration / steps)
    led.on()

# ---------- YOLO POSE DETECTION ----------
model = YOLO("yolov8n-pose.pt")

def analyze_frame(frame):
    results = model(frame, stream=False, verbose=False)
    result = results[0]
    for pose in result.keypoints:
        keypoints = pose.data[0].cpu().numpy()
        if len(keypoints) < 17:
            continue
        for x, y, conf in keypoints:
            if conf > 0.3:
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 0), -1)
        return "Lying", frame
    return "No Person", frame

# ---------- GUI ----------
@circuit.run
def main():
    global accel_status, accel_x, accel_y, accel_z, accel_std, gyro_x, gyro_y, gyro_z, gyro_std

    led = PWMLED(18)
    cap = cv2.VideoCapture(0)
    root = circuit._root
    root.title("Smart Posture-Controlled Lighting System")

    # ---- Camera Feed ----
    video_label = Label(root)
    video_label.place(x=20, y=20)
    image_label = Label(root, text="Image: ---", font=("Arial", 12))
    image_label.place(x=20, y=180)
    image_criteria = Label(root, text="📏 Pose == 'Lying'", fg="gray")
    image_criteria.place(x=20, y=200)

    # ---- Sensor Info ----
    accel_label = Label(root, text="Accel: ---", font=("Arial", 12))
    accel_label.place(x=20, y=230)
    accel_detail_label = Label(root, text="Accel XYZ: ---", font=("Arial", 10))
    accel_detail_label.place(x=20, y=250)
    gyro_detail_label = Label(root, text="Gyro XYZ: ---", font=("Arial", 10))
    gyro_detail_label.place(x=20, y=270)

    criteria1 = Label(root, text="📏 Accel std < 0.05 & Z ≈ -1", fg="gray")
    criteria1.place(x=20, y=290)
    criteria2 = Label(root, text="📏 Gyro std < 0.1", fg="gray")
    criteria2.place(x=20, y=310)

    # ---- Physiological Inputs ----
    hr_label = Label(root, text="Heart Rate (BPM):")
    hr_label.place(x=350, y=180)
    hr_slider = Scale(root, from_=40, to=120, orient=HORIZONTAL)
    hr_slider.set(70)
    hr_slider.place(x=500, y=170)
    hr_criteria = Label(root, text="✅ < 60 BPM = หลับ", fg="gray")
    hr_criteria.place(x=670, y=180)

    spo2_label = Label(root, text="SpO2 (%):")
    spo2_label.place(x=350, y=230)
    spo2_slider = Scale(root, from_=80, to=100, orient=HORIZONTAL)
    spo2_slider.set(98)
    spo2_slider.place(x=500, y=220)
    spo2_criteria = Label(root, text="✅ > 95% = ปกติ", fg="gray")
    spo2_criteria.place(x=670, y=230)

    hrv_label = Label(root, text="HRV (ms):")
    hrv_label.place(x=350, y=280)
    hrv_slider = Scale(root, from_=10, to=100, orient=HORIZONTAL)
    hrv_slider.set(50)
    hrv_slider.place(x=500, y=270)
    hrv_criteria = Label(root, text="✅ > 50 ms = ผ่อนคลาย", fg="gray")
    hrv_criteria.place(x=670, y=280)

    # ---- LED Status ----
    led_label = Label(root, text="LED: ---", font=("Arial", 12))
    led_label.place(x=750, y=100)
    Button(root, text="Exit", command=lambda: root.quit()).place(x=20, y=390)

    threading.Thread(target=sensor_thread, daemon=True).start()
    prev_led_state = None

    def update_gui():
        nonlocal prev_led_state
        ret, frame = cap.read()
        image_status = "No Person"
        if ret:
            image_status, frame = analyze_frame(frame)
            resized = cv2.resize(frame, (200, 150))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(rgb))
            video_label.imgtk = img
            video_label.config(image=img)

        heart_rate = hr_slider.get()
        spo2 = spo2_slider.get()
        hrv = hrv_slider.get()

        if accel_status == "🛌 กำลังนอนนิ่ง" and image_status == "Lying" and heart_rate < 60 and spo2 > 95:
            if prev_led_state != "OFF":
                threading.Thread(target=fade_out, args=(led,), daemon=True).start()
                prev_led_state = "OFF"
            led_msg = "💡 FADING OFF"
        else:
            if prev_led_state != "ON":
                threading.Thread(target=fade_in, args=(led,), daemon=True).start()
                prev_led_state = "ON"
            led_msg = "💡 FADING ON"

        accel_label.config(text=f"Accel: {accel_status}")
        accel_detail_label.config(text=f"Accel: x={accel_x:.2f}, y={accel_y:.2f}, z={accel_z:.2f}, std={accel_std:.4f}")
        gyro_detail_label.config(text=f"Gyro: x={gyro_x:.3f}, y={gyro_y:.3f}, z={gyro_z:.3f}, std={gyro_std:.4f}")
        image_label.config(text=f"Image: {image_status}")
        led_label.config(text=f"LED: {led_msg}")

        # Send data to MQTT
        mqtt_data = {
            "accel_status": accel_status,
            "accel_x": accel_x,
            "accel_y": accel_y,
            "accel_z": accel_z,
            "accel_std": accel_std,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
            "gyro_std": gyro_std,
            "image_status": image_status,
            "heart_rate": heart_rate,
            "spo2": spo2,
            "hrv": hrv,
            "led_status": led_msg
        }
        publish_mqtt(mqtt_data)
        
        root.after(300, update_gui)

    update_gui()
    root.mainloop()
    cap.release()
    led.off()