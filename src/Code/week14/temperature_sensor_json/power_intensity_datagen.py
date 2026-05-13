import numpy as np
import time
import datetime
import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import os
import sys

# Status variable for generator
generator_on = False

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    # Subscribe to sensor data topic
    client.subscribe("sensor/sensor_value")
    # Subscribe to control topic for generator
    client.subscribe("control/generator")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    global generator_on
    if msg.topic == "control/generator":
        command = msg.payload.decode()
        if command == "ON":
            generator_on = True
            print("Generator turned ON")
        elif command == "OFF":
            generator_on = False
            print("Generator turned OFF")

# Callback when a message is published
def on_publish(client, userdata, mid, reason_code=0, properties=None):
    pass

# Function to simulate solar panel power and light intensity based on current time
def calculate_solar_and_light(current_time):
    hour = current_time.hour
    minute = current_time.minute
    
    # Calculate time-based factor (peak at noon)
    time_factor = np.cos((hour - 12 + minute / 60) * np.pi / 12) ** 2
    
    # Set power and light to zero during nighttime (6 PM to 6 AM)
    if hour < 6 or hour >= 18:
        time_factor = 0
    
    # Base values for solar power and light intensity
    base_solar_power = 800 * time_factor  # max 800W
    base_light_intensity = 100000 * time_factor  # max 100,000 lux
    
    # Add random fluctuation
    solar_power = base_solar_power + np.random.normal(0, 30)
    light_intensity = base_light_intensity + np.random.normal(0, 3000)
    
    # Ensure no negative values
    solar_power = max(0, solar_power)
    light_intensity = max(0, light_intensity)
    
    return round(solar_power, 2), round(light_intensity, 2)

# Function to simulate generator power output
def calculate_generator_power():
    if generator_on:
        return round(100 + np.random.normal(0, 10), 2)  # approx. 1200W ± 50W
    else:
        return 0.0

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

    # Infinite loop to send data every second
    while True:
        now = datetime.datetime.now()
        date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate solar power and light intensity
        solar_power, light_intensity = calculate_solar_and_light(now)
        
        # Calculate generator power
        generator_power = calculate_generator_power()
        
        # Calculate total power
        total_power = solar_power + generator_power
        
        # Create data payload
        data = {
            'timestamp': date_time_str,
            'solar_panel_power_watt': solar_power,
            'generator_power_watt': generator_power,
            'total_power_watt': total_power,
            'light_intensity_lux': light_intensity,
            'generator_status': "ON" if generator_on else "OFF"
        }

        # Convert dictionary to JSON string
        data_json_str = json.dumps(data)
        
        # Print to console
        print(data_json_str)
        
        # Publish data to MQTT topic
        client.publish("sensor/sensor_value", data_json_str)
        
        # Wait for 1 second before sending the next message
        time.sleep(1)
