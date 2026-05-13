# subscriber.py
from paho.mqtt import client as mqtt

broker = "localhost"
port = 1883
topic = "test/topic"

def on_message(client, userdata, msg):
    print(f"Recieved Message: '{msg.payload.decode()}' Topic: {msg.topic}")

client = mqtt.Client()
client.connect(broker, port)
client.subscribe(topic)
client.on_message = on_message
client.loop_forever()