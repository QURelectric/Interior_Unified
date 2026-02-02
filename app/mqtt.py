import json
import time
import paho.mqtt.client as mqtt
from app.state import vehicle_state, state_lock


#### mqtt.py ####
# This file sends telemetry data to the pit, and recieves warning flags

BROKER = "test.mosquitto.org"
#BROKER = "test.test.test"
PORT = 1883
#USERNAME = "m07p6t1s7@mozmail.com"
#PASSWORD = "Db9aTJ~3'^dGf~8"
send_topic = "kart/telemetry"
recieve_topic = "kart/flags"


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with reason code", reason_code)
    result, mid = client.subscribe(receive_topic, qos=1)
    print("Subscribed:", result)

def on_message(client, userdata, msg):
#PLACEHOLDER
    print(message + "\n")


client = mqtt.Client(
    client_id="kart_client",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

client.connect(BROKER, PORT, 60)
client.loop_start()

def mqtt_loop():
    client = mqtt.Client()
    client.connect(BROKER, 1883, 60)
    client.loop_start()

    while True:
        with state_lock:
            payload = json.dumps(vehicle_state)
        client.publish(send_topic, payload)
        time.sleep(0.2)  # 5 Hz

