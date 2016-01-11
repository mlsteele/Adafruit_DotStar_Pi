import paho.mqtt.client as mqtt
import re, sys
import json
import logging
import mqtt_config

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('messages')

Messages = []

def on_connect(client, userdata, flags, rc):
    logger.info("connected result code=%s", str(rc))
    logger.info("subscribe topic=%s", mqtt_config.TOPIC)
    client.subscribe(mqtt_config.TOPIC, 0)

def on_log(client, userdata, level, string):
    logger.info("log %s %s", level, string)

def on_message(client, userdata, msg):
    logger.info("message topic=%s payload=%s", msg.topic, msg.payload)
    Messages.append(msg)

def on_publish(client, userdata, rc):
    logger.info("published result code=%s", rc)

def on_disconnect(client, userdata, other):
    logger.info("disconnected result code=%s", other)

client = mqtt.Client("xmas-lights", clean_session=False)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.on_publish = on_publish

if mqtt_config.hostname:
    if mqtt_config.username:
        client.username_pw_set(mqtt_config.username, mqtt_config.password)
    client.connect(mqtt_config.hostname, 1883, 60)
    client.loop_start()

def get_message():
    if not Messages: return None
    message = Messages.pop(0)
    logger.info("receive %s", message.payload)
    return json.loads(message.payload)

if __name__ == '__main__':
    print 'Waiting for messages'
    logger.setLevel(logging.INFO)
    while True:
        message = get_message()
        if message:
            print message
