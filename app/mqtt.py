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
SEND_TOPIC = "kart/telemetry"
RECEIVE_TOPIC = "kart/flags"


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with reason code", reason_code)
    result, mid = client.subscribe(RECEIVE_TOPIC, qos=1)
    print("Subscribed:", result)

def on_message(client, userdata, msg):
    try:
        message = msg.payload.decode(errors="replace")
        data = json.loads(message)
        with state_lock:
            vehicle_state["Pit"] = data.get("Pit",0)
            vehicle_state["Exit"] = data.get("Exit",0)
        print(f"[MQTT] Received on {msg.topic}: {message}")
    except json.JSONDecodeError:
        print(f"[MQTT] Bad JSON on {msg.topic}: {msg.payload}")

def mqtt_loop():
    client = mqtt.Client(
        client_id="kart_client",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    try:
        while True:
            with state_lock:
                payload = json.dumps(vehicle_state)

            client.publish(SEND_TOPIC, payload)
            time.sleep(0.2)  # 5 Hz

    finally:
        client.loop_stop()
        client.disconnect()
        
# Old code incase update is wrong lol
# client = mqtt.Client(
#     client_id="kart_client",
#     callback_api_version=mqtt.CallbackAPIVersion.VERSION2
# )

# client.connect(BROKER, PORT, 60)
# client.loop_start()
# 
# def mqtt_loop():
#     client = mqtt.Client()
#     client.connect(BROKER, 1883, 60)
#     client.loop_start()

#     while True:
#         with state_lock:
#             payload = json.dumps(vehicle_state)
#         client.publish(send_topic, payload)
#         time.sleep(0.2)  # 5 Hz

