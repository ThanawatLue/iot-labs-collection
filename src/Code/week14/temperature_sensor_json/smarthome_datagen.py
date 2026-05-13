import numpy as np
import time
import datetime
import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import os
import sys
import random

# Status variables for monitoring
monitoring_active = True
security_mode = False

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    # Subscribe to sensor data topic
    client.subscribe("smarthome/sensor_data")
    # Subscribe to control topic for monitoring
    client.subscribe("control/monitoring")
    # Subscribe to security control
    client.subscribe("control/security")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    global monitoring_active, security_mode
    
    if msg.topic == "control/monitoring":
        command = msg.payload.decode()
        if command == "START":
            monitoring_active = True
            print("Smart home monitoring started")
        elif command == "STOP":
            monitoring_active = False
            print("Smart home monitoring stopped")
    
    elif msg.topic == "control/security":
        command = msg.payload.decode()
        if command == "ON":
            security_mode = True
            print("Security mode activated")
        elif command == "OFF":
            security_mode = False
            print("Security mode deactivated")

# Callback when a message is published
def on_publish(client, userdata, mid, reason_code=0, properties=None):
    pass

# Function to generate realistic smart home sensor data
def generate_smarthome_data():
    # Indoor Temperature (°C) - Normal 20-26°C
    if security_mode:
        # When security mode is on, house might be unoccupied, temperature varies more
        indoor_temp = round(np.random.normal(22, 3), 1)
    else:
        # Normal occupied temperature
        indoor_temp = round(np.random.normal(24, 1.5), 1)
    indoor_temp = max(15, min(35, indoor_temp))
    
    # Indoor Humidity (%) - Normal 40-60%
    indoor_humidity = max(30, min(80, int(np.random.normal(50, 8))))
    
    # Light Level (Lux) - Indoor lighting 0-1000 Lux
    hour = datetime.datetime.now().hour
    if security_mode:
        # Security mode: minimal lighting or motion-activated
        if 6 <= hour <= 22:  # Daytime with some natural light
            light_level = max(50, min(300, int(np.random.normal(150, 50))))
        else:  # Nighttime
            light_level = max(0, min(50, int(np.random.normal(10, 15))))
    else:
        # Normal mode: lights on when occupied
        if 6 <= hour <= 22:  # Daytime
            light_level = max(200, min(800, int(np.random.normal(400, 100))))
        else:  # Evening/night
            light_level = max(100, min(600, int(np.random.normal(300, 80))))
    
    # Motion Detection (0=No motion, 1=Motion detected)
    if security_mode:
        # In security mode, any motion is suspicious
        motion_detected = 1 if random.random() < 0.1 else 0  # 10% chance
    else:
        # Normal mode: regular movement
        motion_detected = 1 if random.random() < 0.7 else 0  # 70% chance
    
    # Door/Window Status (0=Closed, 1=Open)
    if security_mode:
        # In security mode, doors/windows should be closed
        door_window_open = 1 if random.random() < 0.05 else 0  # 5% chance (suspicious)
    else:
        # Normal mode: some doors/windows might be open
        door_window_open = 1 if random.random() < 0.3 else 0  # 30% chance
    
    # Air Quality Index (0-500, lower is better)
    # Good: 0-50, Moderate: 51-100, Unhealthy for sensitive: 101-150
    air_quality = max(20, min(200, int(np.random.normal(60, 25))))
    
    # Energy Consumption (kW) - Typical home usage
    if security_mode:
        # Lower consumption when unoccupied
        energy_consumption = round(np.random.normal(0.8, 0.3), 2)
    else:
        # Normal consumption when occupied
        if 7 <= hour <= 9 or 17 <= hour <= 22:  # Peak usage times
            energy_consumption = round(np.random.normal(2.5, 0.8), 2)
        else:
            energy_consumption = round(np.random.normal(1.2, 0.4), 2)
    energy_consumption = max(0.1, min(5.0, energy_consumption))
    
    return indoor_temp, indoor_humidity, light_level, motion_detected, door_window_open, air_quality, energy_consumption

# Function to determine home security status
def get_home_status(indoor_temp, indoor_humidity, light_level, motion_detected, door_window_open, air_quality, energy_consumption):
    if security_mode:
        # In security mode, check for intrusions
        if motion_detected and door_window_open:
            return "INTRUSION"  # Motion + open door/window = potential break-in
        elif motion_detected:
            return "ALERT"      # Motion detected but doors closed
        elif door_window_open:
            return "WARNING"    # Door/window open but no motion yet
        else:
            return "SECURE"     # All secure
    else:
        # Normal mode: check for environmental issues
        issues = 0
        
        # Check temperature
        if indoor_temp < 18 or indoor_temp > 28:
            issues += 1
        
        # Check air quality
        if air_quality > 100:
            issues += 1
        
        # Check energy consumption (unusual spikes)
        if energy_consumption > 4.0:
            issues += 1
        
        # Check humidity
        if indoor_humidity < 30 or indoor_humidity > 70:
            issues += 1
        
        if issues >= 2:
            return "WARNING"
        elif issues >= 1:
            return "ALERT"
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
            
            # Generate smart home sensor data
            indoor_temp, indoor_humidity, light_level, motion_detected, door_window_open, air_quality, energy_consumption = generate_smarthome_data()
            
            # Get home status
            home_status = get_home_status(indoor_temp, indoor_humidity, light_level, motion_detected, door_window_open, air_quality, energy_consumption)
            
            # Create data payload
            data = {
                'timestamp': date_time_str,
                'indoor_temperature_celsius': indoor_temp,
                'indoor_humidity_percent': indoor_humidity,
                'light_level_lux': light_level,
                'motion_detected': motion_detected,
                'door_window_open': door_window_open,
                'air_quality_index': air_quality,
                'energy_consumption_kw': energy_consumption,
                'home_status': home_status,
                'monitoring_active': monitoring_active,
                'security_mode': security_mode
            }
            
            # Convert dictionary to JSON string
            data_json_str = json.dumps(data)
            
            # Print to console
            print(data_json_str)
            
            # Publish data to MQTT topic
            client.publish("smarthome/sensor_data", data_json_str)
        
        # Wait for 2 seconds before sending the next message
        time.sleep(2)
