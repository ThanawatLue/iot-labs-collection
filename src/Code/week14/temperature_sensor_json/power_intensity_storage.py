import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import sqlite3
import json
import os
import datetime

# MQTT Configuration
MQTT_HOST = "localhost"
MQTT_PORT = 8883
MQTT_USER = "pk"
MQTT_PASSWORD = "YOUR_MQTT_PASSWORD"
MQTT_TOPIC = "sensor/sensor_value"

# Define the SQLite database file path (same directory as this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "solar_power_data.db")

# Called when the client successfully connects to the MQTT broker
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected to MQTT Broker (code: {reason_code})")
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed to topic: {MQTT_TOPIC}")

# Called whenever a message is received from the subscribed topic
def on_message(client, userdata, msg):
    try:
        # Decode the JSON payload
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        # Extract data from the JSON
        timestamp = data.get('timestamp')
        solar_power = data.get('solar_panel_power_watt')
        generator_power = data.get('generator_power_watt')
        total_power = data.get('total_power_watt')
        light_intensity = data.get('light_intensity_lux')
        generator_status = data.get('generator_status')
        
        # Insert data into SQLite database
        db_conn = userdata['db_conn']
        cursor = db_conn.cursor()
        
        # SQL command to insert a new record
        sql = '''
        INSERT INTO solar_power_data 
        (timestamp, solar_power, generator_power, total_power, light_intensity, generator_status) 
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(sql, (
            timestamp,
            solar_power,
            generator_power,
            total_power,
            light_intensity,
            generator_status
        ))
        
        db_conn.commit()
        print(f"Data inserted successfully: {timestamp}")
        
    except Exception as e:
        print(f"Error occurred: {e}")

# Initializes the SQLite database and creates the table if it does not exist
def setup_database():
    print(f"Database location: {DB_FILE}")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS solar_power_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        solar_power REAL,
        generator_power REAL,
        total_power REAL,
        light_intensity REAL,
        generator_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    print("Database table initialized.")
    
    return conn

# Main entry point of the script
def main():
    # Prepare the database
    db_conn = setup_database()
    
    # Define the path for the TLS certificate files
    parent_dir = r"."
    ca_file = os.path.join(parent_dir, "ca.crt")
    cert_file = os.path.join(parent_dir, "client.crt")
    key_file = os.path.join(parent_dir, "client.key")
    
    # Create MQTT client with appropriate callback API version
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set user data (used in message callback for DB access)
    client.user_data_set({'db_conn': db_conn})
    
    # Set username and password for MQTT authentication
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Configure TLS/SSL connection using certificates
    client.tls_set(
        ca_certs=ca_file,
        certfile=cert_file,
        keyfile=key_file
    )
    
    try:
        # Connect to the MQTT broker
        print(f"Connecting to MQTT Broker at {MQTT_HOST}:{MQTT_PORT}...")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        
        # Start listening for messages (blocking loop)
        print("Listening for incoming messages... (Press Ctrl+C to stop)")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Disconnect MQTT and close database connection
        print("Shutting down...")
        client.disconnect()
        db_conn.close()
        print("Disconnected and closed database.")

if __name__ == "__main__":
    main()
