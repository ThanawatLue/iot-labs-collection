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
MQTT_TOPIC = "healthcare/sensor_data"

# Define the SQLite database file path (same directory as this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "healthcare_data.db")

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
        heart_rate = data.get('heart_rate_bpm')
        systolic_pressure = data.get('blood_pressure_systolic')
        diastolic_pressure = data.get('blood_pressure_diastolic')
        glucose_level = data.get('blood_glucose_mg_dl')
        body_temperature = data.get('body_temperature_celsius')
        spo2_level = data.get('blood_oxygen_spo2')
        health_status = data.get('health_status')
        monitoring_active = data.get('monitoring_active')
        emergency_mode = data.get('emergency_mode')
        
        # Insert data into SQLite database
        db_conn = userdata['db_conn']
        cursor = db_conn.cursor()
        
        # SQL command to insert a new record
        sql = '''
        INSERT INTO healthcare_data
        (timestamp, heart_rate_bpm, systolic_pressure, diastolic_pressure, 
         glucose_level_mg_dl, body_temperature_celsius, spo2_percentage, 
         health_status, monitoring_active, emergency_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(sql, (
            timestamp,
            heart_rate,
            systolic_pressure,
            diastolic_pressure,
            glucose_level,
            body_temperature,
            spo2_level,
            health_status,
            monitoring_active,
            emergency_mode
        ))
        
        db_conn.commit()
        print(f"Healthcare data inserted successfully: {timestamp} - Status: {health_status}")
        
        # Check for emergency alerts
        if health_status == "EMERGENCY":
            print(f"⚠️  EMERGENCY ALERT at {timestamp}!")
            # Here you could add additional emergency response logic
            # such as sending notifications, alerts, etc.
            
    except Exception as e:
        print(f"Error occurred while processing healthcare data: {e}")

# Initializes the SQLite database and creates the table if it does not exist
def setup_database():
    print(f"Healthcare database location: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS healthcare_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        heart_rate_bpm INTEGER,
        systolic_pressure INTEGER,
        diastolic_pressure INTEGER,
        glucose_level_mg_dl INTEGER,
        body_temperature_celsius REAL,
        spo2_percentage INTEGER,
        health_status TEXT,
        monitoring_active BOOLEAN,
        emergency_mode BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create index for faster queries on timestamp and health_status
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_timestamp ON healthcare_data(timestamp)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_health_status ON healthcare_data(health_status)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_emergency ON healthcare_data(emergency_mode)
    ''')
    
    conn.commit()
    print("Healthcare database table and indexes initialized.")
    return conn

# Function to create a summary view for easy data analysis
def create_summary_view(db_conn):
    cursor = db_conn.cursor()
    
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS daily_health_summary AS
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as total_readings,
        AVG(heart_rate_bpm) as avg_heart_rate,
        AVG(systolic_pressure) as avg_systolic,
        AVG(diastolic_pressure) as avg_diastolic,
        AVG(glucose_level_mg_dl) as avg_glucose,
        AVG(body_temperature_celsius) as avg_temperature,
        AVG(spo2_percentage) as avg_spo2,
        SUM(CASE WHEN health_status = 'EMERGENCY' THEN 1 ELSE 0 END) as emergency_count,
        SUM(CASE WHEN health_status = 'ABNORMAL' THEN 1 ELSE 0 END) as abnormal_count,
        SUM(CASE WHEN health_status = 'NORMAL' THEN 1 ELSE 0 END) as normal_count
    FROM healthcare_data
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    ''')
    
    db_conn.commit()
    print("Daily health summary view created.")

# Function to display recent data summary
def display_recent_data(db_conn):
    cursor = db_conn.cursor()
    
    # Get latest 5 records
    cursor.execute('''
    SELECT timestamp, heart_rate_bpm, systolic_pressure, diastolic_pressure, 
           glucose_level_mg_dl, body_temperature_celsius, spo2_percentage, health_status
    FROM healthcare_data 
    ORDER BY created_at DESC 
    LIMIT 5
    ''')
    
    records = cursor.fetchall()
    if records:
        print("\n📊 Recent Healthcare Data:")
        print("-" * 100)
        print(f"{'Timestamp':<20} {'HR':<4} {'BP':<8} {'Glucose':<8} {'Temp':<6} {'SpO2':<5} {'Status':<10}")
        print("-" * 100)
        for record in records:
            timestamp, hr, sys_bp, dia_bp, glucose, temp, spo2, status = record
            bp_str = f"{sys_bp}/{dia_bp}"
            print(f"{timestamp:<20} {hr:<4} {bp_str:<8} {glucose:<8} {temp:<6} {spo2:<5} {status:<10}")
        print("-" * 100)

# Main entry point of the script
def main():
    # Prepare the database
    db_conn = setup_database()
    create_summary_view(db_conn)
    
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
        
        # Display recent data before starting
        display_recent_data(db_conn)
        
        # Start listening for messages (blocking loop)
        print("🏥 Listening for healthcare data... (Press Ctrl+C to stop)")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n👋 Stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Disconnect MQTT and close database connection
        print("Shutting down healthcare monitoring...")
        display_recent_data(db_conn)  # Show final summary
        client.disconnect()
        db_conn.close()
        print("Disconnected and closed healthcare database.")

if __name__ == "__main__":
    main()
