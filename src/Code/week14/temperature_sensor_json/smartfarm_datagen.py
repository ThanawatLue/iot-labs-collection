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
irrigation_mode = False

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    # Subscribe to sensor data topic
    client.subscribe("smartfarm/sensor_data")
    # Subscribe to control topic for monitoring
    client.subscribe("control/monitoring")
    # Subscribe to irrigation control
    client.subscribe("control/irrigation")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    global monitoring_active, irrigation_mode
    
    if msg.topic == "control/monitoring":
        command = msg.payload.decode()
        if command == "START":
            monitoring_active = True
            print("Farm monitoring started")
        elif command == "STOP":
            monitoring_active = False
            print("Farm monitoring stopped")
    
    elif msg.topic == "control/irrigation":
        command = msg.payload.decode()
        if command == "ON":
            irrigation_mode = True
            print("Irrigation system activated")
        elif command == "OFF":
            irrigation_mode = False
            print("Irrigation system deactivated")

# Callback when a message is published
def on_publish(client, userdata, mid, reason_code=0, properties=None):
    pass

# Function to generate realistic smart farm sensor data
def generate_smartfarm_data():
    # Soil Moisture (%) - Normal 40-60%, affected by irrigation
    if irrigation_mode:
        base_soil_moisture = np.random.normal(65, 8)  # Higher when irrigating
    else:
        base_soil_moisture = np.random.normal(45, 12)  # Normal range
    soil_moisture = max(10, min(100, int(base_soil_moisture)))
    
    # Soil Temperature (°C) - Typical range 18-30°C
    soil_temperature = round(np.random.normal(24, 4), 1)
    soil_temperature = max(15, min(35, soil_temperature))
    
    # Air Temperature (°C) - Outdoor range 20-35°C
    air_temperature = round(np.random.normal(28, 5), 1)
    air_temperature = max(15, min(40, air_temperature))
    
    # Air Humidity (%) - Normal 50-80%
    if irrigation_mode:
        air_humidity = max(60, min(95, int(np.random.normal(80, 8))))  # Higher when irrigating
    else:
        air_humidity = max(40, min(85, int(np.random.normal(65, 10))))
    
    # Light Intensity (Lux) - 0-100000 Lux (daylight simulation)
    hour = datetime.datetime.now().hour
    if 6 <= hour <= 18:  # Daytime
        if 10 <= hour <= 16:  # Peak sunlight
            light_intensity = max(30000, min(100000, int(np.random.normal(75000, 15000))))
        else:  # Morning/evening
            light_intensity = max(10000, min(50000, int(np.random.normal(25000, 8000))))
    else:  # Nighttime
        light_intensity = max(0, min(1000, int(np.random.normal(50, 100))))
    
    # pH Level - Normal range 6.0-7.5 for most crops
    ph_level = round(np.random.normal(6.8, 0.4), 1)
    ph_level = max(4.0, min(9.0, ph_level))
    
    # Nutrient Level (ppm) - NPK nutrients, normal 100-300 ppm
    if irrigation_mode:
        nutrient_level = max(80, min(400, int(np.random.normal(250, 40))))  # Higher with fertigation
    else:
        nutrient_level = max(50, min(300, int(np.random.normal(180, 50))))
    
    return soil_moisture, soil_temperature, air_temperature, air_humidity, light_intensity, ph_level, nutrient_level

# Function to determine farm status
def get_farm_status(soil_moisture, soil_temp, air_temp, air_humidity, light_intensity, ph_level, nutrient_level):
    critical_conditions = 0
    warning_conditions = 0
    
    # Check soil moisture
    if soil_moisture < 30 or soil_moisture > 80:
        critical_conditions += 1
    elif soil_moisture < 35 or soil_moisture > 70:
        warning_conditions += 1
    
    # Check temperatures
    if soil_temp < 18 or soil_temp > 32 or air_temp < 20 or air_temp > 35:
        critical_conditions += 1
    elif soil_temp < 20 or soil_temp > 30 or air_temp < 22 or air_temp > 33:
        warning_conditions += 1
    
    # Check pH level
    if ph_level < 5.5 or ph_level > 8.0:
        critical_conditions += 1
    elif ph_level < 6.0 or ph_level > 7.5:
        warning_conditions += 1
    
    # Check nutrient level
    if nutrient_level < 80 or nutrient_level > 350:
        critical_conditions += 1
    elif nutrient_level < 100 or nutrient_level > 300:
        warning_conditions += 1
    
    # Check air humidity
    if air_humidity < 40 or air_humidity > 90:
        warning_conditions += 1
    
    if critical_conditions >= 2:
        return "CRITICAL"
    elif critical_conditions >= 1 or warning_conditions >= 2:
        return "WARNING"
    else:
        return "OPTIMAL"

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
    
    # Infinite loop to send data every 3 seconds
    while True:
        if monitoring_active:
            now = datetime.datetime.now()
            date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate smart farm sensor data
            soil_moisture, soil_temp, air_temp, air_humidity, light_intensity, ph_level, nutrient_level = generate_smartfarm_data()
            
            # Get farm status
            farm_status = get_farm_status(soil_moisture, soil_temp, air_temp, air_humidity, light_intensity, ph_level, nutrient_level)
            
            # Create data payload
            data = {
                'timestamp': date_time_str,
                'soil_moisture_percent': soil_moisture,
                'soil_temperature_celsius': soil_temp,
                'air_temperature_celsius': air_temp,
                'air_humidity_percent': air_humidity,
                'light_intensity_lux': light_intensity,
                'ph_level': ph_level,
                'nutrient_level_ppm': nutrient_level,
                'farm_status': farm_status,
                'monitoring_active': monitoring_active,
                'irrigation_mode': irrigation_mode
            }
            
            # Convert dictionary to JSON string
            data_json_str = json.dumps(data)
            
            # Print to console
            print(data_json_str)
            
            # Publish data to MQTT topic
            client.publish("smartfarm/sensor_data", data_json_str)
        
        # Wait for 3 seconds before sending the next message
        time.sleep(3)
