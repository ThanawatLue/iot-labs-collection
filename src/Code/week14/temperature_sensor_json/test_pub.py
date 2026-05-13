import numpy as np
import time
import datetime
import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import os
import sys

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code "+str(rc))
    client.subscribe("sensor/sensor_value")
    client.subscribe("control/generator")

def on_message(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode('utf-8')
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"[{timestamp}] Topic: {topic}")
    print(f"Message: {payload}")
    print("-" * 40)

if __name__ == '__main__':
    parent_dir = r"../"
    
    ca_file = os.path.join(parent_dir, "ca.crt")
    cert_file = os.path.join(parent_dir, "client.crt")
    key_file = os.path.join(parent_dir, "client.key")
    
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set('pk', 'YOUR_MQTT_PASSWORD')

    # Set TLS for secure connection
    client.tls_set(
        ca_certs=ca_file,
        certfile=cert_file,
        keyfile=key_file
    )

    # Connect to MQTT broker
    client.connect("localhost", 1883, 60)
    client.loop_start()

    # Infinite loop to send data every second
    while True:
        time.sleep(1)
