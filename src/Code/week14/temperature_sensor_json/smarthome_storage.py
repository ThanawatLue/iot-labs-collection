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
MQTT_TOPIC = "smarthome/sensor_data"

# Define the SQLite database file path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "smarthome_data.db")

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
        indoor_temperature = data.get('indoor_temperature_celsius')
        indoor_humidity = data.get('indoor_humidity_percent')
        light_level = data.get('light_level_lux')
        motion_detected = data.get('motion_detected')
        door_window_open = data.get('door_window_open')
        air_quality = data.get('air_quality_index')
        energy_consumption = data.get('energy_consumption_kw')
        home_status = data.get('home_status')
        monitoring_active = data.get('monitoring_active')
        security_mode = data.get('security_mode')
        
        # Insert data into SQLite database
        db_conn = userdata['db_conn']
        cursor = db_conn.cursor()
        
        # SQL command to insert a new record
        sql = '''
        INSERT INTO smarthome_data
        (timestamp, indoor_temperature_celsius, indoor_humidity_percent, light_level_lux, 
         motion_detected, door_window_open, air_quality_index, energy_consumption_kw, 
         home_status, monitoring_active, security_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(sql, (
            timestamp,
            indoor_temperature,
            indoor_humidity,
            light_level,
            motion_detected,
            door_window_open,
            air_quality,
            energy_consumption,
            home_status,
            monitoring_active,
            security_mode
        ))
        
        db_conn.commit()
        print(f"Smart home data inserted: {timestamp} - Status: {home_status}")
        
        # Check for security alerts
        if home_status == "INTRUSION":
            print(f"🚨 SECURITY INTRUSION ALERT at {timestamp}!")
            print(f"   Motion: {'Detected' if motion_detected else 'None'}")
            print(f"   Door/Window: {'Open' if door_window_open else 'Closed'}")
        elif home_status == "ALERT" and security_mode:
            print(f"⚠️  SECURITY ALERT at {timestamp}!")
        elif home_status == "WARNING":
            print(f"⚠️  HOME WARNING at {timestamp}!")
            if air_quality > 100:
                print("   Recommendation: Check air quality - Poor air detected!")
            if energy_consumption > 4.0:
                print("   Recommendation: Check energy usage - Unusual spike detected!")
            
    except Exception as e:
        print(f"Error occurred while processing smart home data: {e}")

# Initialize the SQLite database and create tables
def setup_database():
    print(f"Smart Home database location: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create main data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS smarthome_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        indoor_temperature_celsius REAL,
        indoor_humidity_percent INTEGER,
        light_level_lux INTEGER,
        motion_detected INTEGER,
        door_window_open INTEGER,
        air_quality_index INTEGER,
        energy_consumption_kw REAL,
        home_status TEXT,
        monitoring_active BOOLEAN,
        security_mode BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_timestamp ON smarthome_data(timestamp)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_home_status ON smarthome_data(home_status)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_security_mode ON smarthome_data(security_mode)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_motion ON smarthome_data(motion_detected)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_door_window ON smarthome_data(door_window_open)
    ''')
    
    conn.commit()
    print("Smart Home database table and indexes initialized.")
    return conn

# Create summary views for data analysis
def create_summary_views(db_conn):
    cursor = db_conn.cursor()
    
    # Daily home summary
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS daily_home_summary AS
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as total_readings,
        AVG(indoor_temperature_celsius) as avg_indoor_temp,
        AVG(indoor_humidity_percent) as avg_indoor_humidity,
        AVG(light_level_lux) as avg_light_level,
        AVG(air_quality_index) as avg_air_quality,
        SUM(energy_consumption_kw) as total_energy_consumption,
        SUM(motion_detected) as total_motion_events,
        SUM(door_window_open) as total_door_window_open_events,
        SUM(CASE WHEN home_status = 'INTRUSION' THEN 1 ELSE 0 END) as intrusion_count,
        SUM(CASE WHEN home_status = 'ALERT' THEN 1 ELSE 0 END) as alert_count,
        SUM(CASE WHEN home_status = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
        SUM(CASE WHEN home_status = 'NORMAL' THEN 1 ELSE 0 END) as normal_count,
        SUM(CASE WHEN home_status = 'SECURE' THEN 1 ELSE 0 END) as secure_count,
        SUM(CASE WHEN security_mode = 1 THEN 1 ELSE 0 END) as security_mode_duration
    FROM smarthome_data
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    ''')
    
    # Security incidents view
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS security_incidents AS
    SELECT 
        timestamp,
        home_status,
        motion_detected,
        door_window_open,
        security_mode,
        indoor_temperature_celsius,
        energy_consumption_kw
    FROM smarthome_data
    WHERE home_status IN ('INTRUSION', 'ALERT') OR motion_detected = 1
    ORDER BY timestamp DESC
    ''')
    
    # Energy usage patterns
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS energy_patterns AS
    SELECT 
        strftime('%H', timestamp) as hour_of_day,
        AVG(energy_consumption_kw) as avg_energy_consumption,
        AVG(indoor_temperature_celsius) as avg_temperature,
        AVG(light_level_lux) as avg_light_level,
        COUNT(*) as readings_count
    FROM smarthome_data
    GROUP BY strftime('%H', timestamp)
    ORDER BY hour_of_day
    ''')
    
    db_conn.commit()
    print("Smart Home summary views created.")

# Display recent home data
def display_recent_data(db_conn):
    cursor = db_conn.cursor()
    
    # Get latest 5 records
    cursor.execute('''
    SELECT timestamp, indoor_temperature_celsius, indoor_humidity_percent, light_level_lux,
           motion_detected, door_window_open, air_quality_index, energy_consumption_kw, home_status
    FROM smarthome_data 
    ORDER BY created_at DESC 
    LIMIT 5
    ''')
    
    records = cursor.fetchall()
    if records:
        print("\n🏠 Recent Smart Home Data:")
        print("-" * 120)
        print(f"{'Timestamp':<20} {'Temp':<5} {'Hum%':<4} {'Light':<6} {'Motion':<6} {'Door':<5} {'AQI':<4} {'Energy':<7} {'Status':<10}")
        print("-" * 120)
        for record in records:
            timestamp, temp, humidity, light, motion, door, aqi, energy, status = record
            motion_str = "Yes" if motion else "No"
            door_str = "Open" if door else "Closed"
            print(f"{timestamp:<20} {temp:<5.1f} {humidity:<4} {light:<6} {motion_str:<6} {door_str:<5} {aqi:<4} {energy:<7.2f} {status:<10}")
        print("-" * 120)

# Display home analytics
def display_home_analytics(db_conn):
    cursor = db_conn.cursor()
    
    # Get today's summary
    cursor.execute('''
    SELECT 
        avg_indoor_temp, avg_indoor_humidity, avg_air_quality, total_energy_consumption,
        total_motion_events, intrusion_count, alert_count, warning_count, normal_count, secure_count
    FROM daily_home_summary 
    WHERE date = DATE('now')
    ''')
    
    today_data = cursor.fetchone()
    if today_data:
        avg_temp, avg_humidity, avg_aqi, total_energy, motion_events, intrusions, alerts, warnings, normal, secure = today_data
        print(f"\n📊 Today's Home Analytics:")
        print(f"Average Indoor Temperature: {avg_temp:.1f}°C")
        print(f"Average Indoor Humidity: {avg_humidity:.1f}%")
        print(f"Average Air Quality: {avg_aqi:.1f}")
        print(f"Total Energy Consumption: {total_energy:.2f} kWh")
        print(f"Motion Events: {motion_events}")
        print(f"Status Distribution - Intrusions: {intrusions}, Alerts: {alerts}, Warnings: {warnings}")
        print(f"Normal/Secure Status: {normal + secure} readings")
    
    # Get recent security incidents
    cursor.execute('''
    SELECT timestamp, home_status, motion_detected, door_window_open
    FROM security_incidents
    WHERE DATE(timestamp) = DATE('now')
    LIMIT 3
    ''')
    
    incidents = cursor.fetchall()
    if incidents:
        print(f"\n🔒 Today's Security Incidents:")
        for incident in incidents:
            timestamp, status, motion, door = incident
            motion_str = "Motion detected" if motion else "No motion"
            door_str = "Door/Window open" if door else "Doors/Windows closed"
            print(f"  {timestamp}: {status} - {motion_str}, {door_str}")

# Main entry point
def main():
    # Prepare the database
    db_conn = setup_database()
    create_summary_views(db_conn)
    
    # Define the path for TLS certificate files
    parent_dir = r"."
    ca_file = os.path.join(parent_dir, "ca.crt")
    cert_file = os.path.join(parent_dir, "client.crt")
    key_file = os.path.join(parent_dir, "client.key")
    
    # Create MQTT client
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set user data for DB access
    client.user_data_set({'db_conn': db_conn})
    
    # Set MQTT authentication
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    
    # Configure TLS/SSL connection
    client.tls_set(
        ca_certs=ca_file,
        certfile=cert_file,
        keyfile=key_file
    )
    
    try:
        # Connect to MQTT broker
        print(f"Connecting to MQTT Broker at {MQTT_HOST}:{MQTT_PORT}...")
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        
        # Display recent data and analytics
        display_recent_data(db_conn)
        display_home_analytics(db_conn)
        
        # Start listening for messages
        print("🏠 Listening for smart home data... (Press Ctrl+C to stop)")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n👋 Stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Cleanup
        print("Shutting down smart home monitoring...")
        display_recent_data(db_conn)
        display_home_analytics(db_conn)
        client.disconnect()
        db_conn.close()
        print("Disconnected and closed smart home database.")

if __name__ == "__main__":
    main()
