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
MQTT_TOPIC = "smartfarm/sensor_data"

# Define the SQLite database file path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "smartfarm_data.db")

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
        soil_moisture = data.get('soil_moisture_percent')
        soil_temperature = data.get('soil_temperature_celsius')
        air_temperature = data.get('air_temperature_celsius')
        air_humidity = data.get('air_humidity_percent')
        light_intensity = data.get('light_intensity_lux')
        ph_level = data.get('ph_level')
        nutrient_level = data.get('nutrient_level_ppm')
        farm_status = data.get('farm_status')
        monitoring_active = data.get('monitoring_active')
        irrigation_mode = data.get('irrigation_mode')
        
        # Insert data into SQLite database
        db_conn = userdata['db_conn']
        cursor = db_conn.cursor()
        
        # SQL command to insert a new record
        sql = '''
        INSERT INTO smartfarm_data
        (timestamp, soil_moisture_percent, soil_temperature_celsius, air_temperature_celsius, 
         air_humidity_percent, light_intensity_lux, ph_level, nutrient_level_ppm, 
         farm_status, monitoring_active, irrigation_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(sql, (
            timestamp,
            soil_moisture,
            soil_temperature,
            air_temperature,
            air_humidity,
            light_intensity,
            ph_level,
            nutrient_level,
            farm_status,
            monitoring_active,
            irrigation_mode
        ))
        
        db_conn.commit()
        print(f"Farm data inserted successfully: {timestamp} - Status: {farm_status}")
        
        # Check for critical farm alerts
        if farm_status == "CRITICAL":
            print(f"🚨 FARM CRITICAL ALERT at {timestamp}!")
            # Add irrigation recommendations
            if soil_moisture < 30:
                print("💧 Recommendation: Activate irrigation system - Low soil moisture detected!")
            if ph_level < 5.5 or ph_level > 8.0:
                print("⚗️  Recommendation: Adjust soil pH level - Critical pH detected!")
            
    except Exception as e:
        print(f"Error occurred while processing farm data: {e}")

# Initialize the SQLite database and create tables
def setup_database():
    print(f"Smart Farm database location: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create main data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS smartfarm_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        soil_moisture_percent INTEGER,
        soil_temperature_celsius REAL,
        air_temperature_celsius REAL,
        air_humidity_percent INTEGER,
        light_intensity_lux INTEGER,
        ph_level REAL,
        nutrient_level_ppm INTEGER,
        farm_status TEXT,
        monitoring_active BOOLEAN,
        irrigation_mode BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_timestamp ON smartfarm_data(timestamp)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_farm_status ON smartfarm_data(farm_status)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_irrigation ON smartfarm_data(irrigation_mode)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_soil_moisture ON smartfarm_data(soil_moisture_percent)
    ''')
    
    conn.commit()
    print("Smart Farm database table and indexes initialized.")
    return conn

# Create summary views for data analysis
def create_summary_views(db_conn):
    cursor = db_conn.cursor()
    
    # Daily farm summary
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS daily_farm_summary AS
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as total_readings,
        AVG(soil_moisture_percent) as avg_soil_moisture,
        AVG(soil_temperature_celsius) as avg_soil_temp,
        AVG(air_temperature_celsius) as avg_air_temp,
        AVG(air_humidity_percent) as avg_air_humidity,
        AVG(light_intensity_lux) as avg_light_intensity,
        AVG(ph_level) as avg_ph_level,
        AVG(nutrient_level_ppm) as avg_nutrient_level,
        SUM(CASE WHEN farm_status = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
        SUM(CASE WHEN farm_status = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
        SUM(CASE WHEN farm_status = 'OPTIMAL' THEN 1 ELSE 0 END) as optimal_count,
        SUM(CASE WHEN irrigation_mode = 1 THEN 1 ELSE 0 END) as irrigation_time_hours
    FROM smartfarm_data
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    ''')
    
    # Irrigation efficiency view
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS irrigation_efficiency AS
    SELECT 
        DATE(timestamp) as date,
        AVG(CASE WHEN irrigation_mode = 1 THEN soil_moisture_percent ELSE NULL END) as moisture_during_irrigation,
        AVG(CASE WHEN irrigation_mode = 0 THEN soil_moisture_percent ELSE NULL END) as moisture_without_irrigation,
        COUNT(CASE WHEN irrigation_mode = 1 THEN 1 ELSE NULL END) as irrigation_duration_readings
    FROM smartfarm_data
    GROUP BY DATE(timestamp)
    HAVING irrigation_duration_readings > 0
    ORDER BY date DESC
    ''')
    
    db_conn.commit()
    print("Farm summary views created.")

# Display recent farm data
def display_recent_data(db_conn):
    cursor = db_conn.cursor()
    
    # Get latest 5 records
    cursor.execute('''
    SELECT timestamp, soil_moisture_percent, soil_temperature_celsius, air_temperature_celsius,
           ph_level, nutrient_level_ppm, farm_status, irrigation_mode
    FROM smartfarm_data 
    ORDER BY created_at DESC 
    LIMIT 5
    ''')
    
    records = cursor.fetchall()
    if records:
        print("\n🌱 Recent Smart Farm Data:")
        print("-" * 110)
        print(f"{'Timestamp':<20} {'Soil%':<6} {'SoilT':<6} {'AirT':<6} {'pH':<5} {'NPK':<6} {'Status':<8} {'Irrigation':<10}")
        print("-" * 110)
        for record in records:
            timestamp, soil_moisture, soil_temp, air_temp, ph, nutrients, status, irrigation = record
            irrigation_status = "ON" if irrigation else "OFF"
            print(f"{timestamp:<20} {soil_moisture:<6} {soil_temp:<6.1f} {air_temp:<6.1f} {ph:<5.1f} {nutrients:<6} {status:<8} {irrigation_status:<10}")
        print("-" * 110)

# Display farm analytics
def display_farm_analytics(db_conn):
    cursor = db_conn.cursor()
    
    # Get today's summary
    cursor.execute('''
    SELECT 
        avg_soil_moisture, avg_soil_temp, avg_air_temp, avg_ph_level, 
        critical_count, warning_count, optimal_count, irrigation_time_hours
    FROM daily_farm_summary 
    WHERE date = DATE('now')
    ''')
    
    today_data = cursor.fetchone()
    if today_data:
        avg_moisture, avg_soil_temp, avg_air_temp, avg_ph, critical, warning, optimal, irrigation_time = today_data
        print(f"\n📊 Today's Farm Analytics:")
        print(f"Average Soil Moisture: {avg_moisture:.1f}%")
        print(f"Average Soil Temperature: {avg_soil_temp:.1f}°C")
        print(f"Average Air Temperature: {avg_air_temp:.1f}°C")
        print(f"Average pH Level: {avg_ph:.1f}")
        print(f"Status Distribution - Critical: {critical}, Warning: {warning}, Optimal: {optimal}")
        print(f"Irrigation Active Time: {irrigation_time} readings")

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
        display_farm_analytics(db_conn)
        
        # Start listening for messages
        print("🚜 Listening for smart farm data... (Press Ctrl+C to stop)")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n👋 Stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Cleanup
        print("Shutting down smart farm monitoring...")
        display_recent_data(db_conn)
        display_farm_analytics(db_conn)
        client.disconnect()
        db_conn.close()
        print("Disconnected and closed smart farm database.")

if __name__ == "__main__":
    main()
