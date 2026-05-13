# publisher.py
import time
from paho.mqtt import client as mqtt

broker = "localhost"
port = 1883
topic = "test/topic"

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Broker connected successfully")
        else:
            print(f"Broker failed to connect, return code: {rc}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client):
    msg_count = 0
    while True:
        time.sleep(1)
        msg = f"Message number {msg_count}"
        result = client.publish(topic, msg)
        print(f"Sent '{msg}' to {topic}")
        msg_count += 1

client = connect_mqtt()
client.loop_start()
publish(client)