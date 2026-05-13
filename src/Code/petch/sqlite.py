import paho.mqtt.client as mqtt
import sqlite3
import json
import datetime

MQTT_BROKER_IP = "172.20.10.12"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "sensor/status"

DATABASE_NAME = "mqtt_data.db"
TABLE_NAME = "mqtt_messages"

column_names = set()

def create_table(conn):
    cursor = conn.cursor()
    columns_str = "timestamp TEXT"
    for col in column_names:
        columns_str += f", {col} TEXT"
    sql_create_table = f""" CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        {columns_str}
                                    ); """
    try:
        cursor.execute(sql_create_table)
        conn.commit()
        print(f"สร้าง Table '{TABLE_NAME}' สำเร็จ")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def insert_data(conn, data):
    cursor = conn.cursor()
    placeholders = ', '.join(['?'] * len(data))
    columns = ', '.join(data.keys())
    values = tuple(data.values())
    sql_insert = f""" INSERT INTO {TABLE_NAME}({columns})
                      VALUES({placeholders}) """
    try:
        cursor.execute(sql_insert, values)
        conn.commit()
        print(f"Insert ข้อมูล: {data}")
    except sqlite3.Error as e:
        print(f"Error inserting data: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"เชื่อมต่อกับ MQTT Broker สำเร็จ ({MQTT_BROKER_IP}:{MQTT_BROKER_PORT})")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribe หัวข้อ: {MQTT_TOPIC}")
    else:
        print(f"การเชื่อมต่อล้มเหลว รหัส: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)

        global column_names
        column_names.update(data.keys())

        conn = sqlite3.connect(DATABASE_NAME)
        create_table(conn)

        data_with_timestamp = data.copy()
        data_with_timestamp['timestamp'] = datetime.datetime.now().isoformat()

        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
        table_columns = [info[1] for info in cursor.fetchall()]
        insert_data_filtered = {k: v for k, v in data_with_timestamp.items() if k in table_columns}

        insert_data(conn, insert_data_filtered)
        conn.close()

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Payload ที่มีปัญหา: {payload}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการประมวลผลข้อความ: {e}")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)
    client.loop_forever()