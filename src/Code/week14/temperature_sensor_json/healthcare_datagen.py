import numpy as np
import time
import datetime
import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import os
import sys

# Status variables for monitoring
monitoring_active = True
emergency_mode = False

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    # Subscribe to sensor data topic
    client.subscribe("healthcare/sensor_data")
    # Subscribe to control topic for monitoring
    client.subscribe("control/monitoring")
    # Subscribe to emergency control
    client.subscribe("control/emergency")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    global monitoring_active, emergency_mode
    
    if msg.topic == "control/monitoring":
        command = msg.payload.decode()
        if command == "START":
            monitoring_active = True
            print("Health monitoring started")
        elif command == "STOP":
            monitoring_active = False
            print("Health monitoring stopped")
    
    elif msg.topic == "control/emergency":
        command = msg.payload.decode()
        if command == "ON":
            emergency_mode = True
            print("Emergency mode activated")
        elif command == "OFF":
            emergency_mode = False
            print("Emergency mode deactivated")

# Callback when a message is published
def on_publish(client, userdata, mid, reason_code=0, properties=None):
    pass

# Function to generate realistic healthcare sensor data
def generate_healthcare_data():
    # Heart Rate (60-100 bpm normal, higher if emergency)
    if emergency_mode:
        base_heart_rate = np.random.normal(120, 15)  # Elevated heart rate
    else:
        base_heart_rate = np.random.normal(75, 10)   # Normal heart rate
    heart_rate = max(40, min(200, int(base_heart_rate)))
    
    # Blood Pressure (mmHg) - Systolic/Diastolic
    if emergency_mode:
        systolic = max(90, min(200, int(np.random.normal(150, 20))))
        diastolic = max(60, min(120, int(np.random.normal(95, 15))))
    else:
        systolic = max(90, min(180, int(np.random.normal(120, 15))))
        diastolic = max(60, min(100, int(np.random.normal(80, 10))))
    
    # Blood Glucose Level (mg/dL) - Normal 70-100 fasting
    if emergency_mode:
        glucose = max(50, min(400, int(np.random.normal(180, 30))))  # High glucose
    else:
        glucose = max(70, min(140, int(np.random.normal(90, 15))))   # Normal range
    
    # Body Temperature (°C) - Normal 36.1-37.2
    if emergency_mode:
        temperature = round(np.random.normal(38.5, 0.8), 1)  # Fever
    else:
        temperature = round(np.random.normal(36.8, 0.4), 1)  # Normal
    temperature = max(35.0, min(42.0, temperature))
    
    # Blood Oxygen Saturation (SpO2) - Normal 95-100%
    if emergency_mode:
        spo2 = max(85, min(100, int(np.random.normal(92, 4))))  # Low oxygen
    else:
        spo2 = max(95, min(100, int(np.random.normal(98, 2))))  # Normal
    
    return heart_rate, systolic, diastolic, glucose, temperature, spo2

# Function to determine health status
def get_health_status(heart_rate, systolic, diastolic, glucose, temperature, spo2):
    if emergency_mode:
        return "EMERGENCY"
    
    # Check for abnormal values
    if (heart_rate > 100 or heart_rate < 60 or 
        systolic > 140 or diastolic > 90 or 
        glucose > 140 or glucose < 70 or 
        temperature > 37.5 or temperature < 36.0 or 
        spo2 < 95):
        return "ABNORMAL"
    else:
        return "NORMAL"

if __name__ == '__main__':
    # Define the path to certificate files
    parent_dir = r"."
    ca_file = os.path.join(parent_dir, "ca.crt")
    cert_file = os.path.join(parent_dir, "client.crt")
    key_file = os.path.join(parent_dir, "client.key")
    
    # Create MQTT client
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    
    # Set username and password for broker
    client.username_pw_set('pk', 'YOUR_MQTT_PASSWORD')
    
    # Set TLS for secure connection
    client.tls_set(
        ca_certs=ca_file,
        certfile=cert_file,
        keyfile=key_file
    )
    
    # Connect to MQTT broker
    client.connect("localhost", 8883, 60)
    client.loop_start()
    
    # Infinite loop to send data every 2 seconds
    while True:
        if monitoring_active:
            now = datetime.datetime.now()
            date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate healthcare sensor data
            heart_rate, systolic, diastolic, glucose, temperature, spo2 = generate_healthcare_data()
            
            # Get health status
            health_status = get_health_status(heart_rate, systolic, diastolic, glucose, temperature, spo2)
            
            # Create data payload
            data = {
                'timestamp': date_time_str,
                'heart_rate_bpm': heart_rate,
                'blood_pressure_systolic': systolic,
                'blood_pressure_diastolic': diastolic,
                'blood_glucose_mg_dl': glucose,
                'body_temperature_celsius': temperature,
                'blood_oxygen_spo2': spo2,
                'health_status': health_status,
                'monitoring_active': monitoring_active,
                'emergency_mode': emergency_mode
            }
            
            # Convert dictionary to JSON string
            data_json_str = json.dumps(data)
            
            # Print to console
            print(data_json_str)
            
            # Publish data to MQTT topic
            client.publish("healthcare/sensor_data", data_json_str)
        
        # Wait for 2 seconds before sending the next message
        time.sleep(2)