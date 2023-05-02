import logging
import os
import django
# The first parameter is fixed, the second parameter is the project name.settings
os.environ.setdefault('DJANGO_SETTING_MODULE', 'brewing_notes.settings')
django.setup()

from django.conf import settings

# Introduce mqtt package
import paho.mqtt.client as mqtt
from threading import Thread

# from brewing_notes.celery import app

from .views import module_record


logger = logging.getLogger(__name__)


#Create mqtt connection
def on_connect(client, userdata, flag, rc):
    if rc != 0:
        logger.error(f'MQTT Connection returned result: {mqtt.connack_string(rc)}')
    client.subscribe('BNCmodule/+/state')

# Receive, process mqtt messages
def on_message(client, userdata, msg):
    # out = str(msg.payload.decode('utf-8'))
    # print(msg.topic)
    # print(out)
    # out = json.loads(out)
    #
    # # Execute the task after receiving the message
    # if msg.topic == 'test/newdata':
    #     print(out)
    try:
        # logger.debug(f'Topic: {msg.topic} - Payload: {str(msg.payload)}')
        module_record(msg.payload)
    except Exception as err:
        logger.error(f'*BNC-module* Error record log Module: {err}')


def mqttfunction():
    global client
    client.loop_start()


client = mqtt.Client(client_id="bnc", clean_session=False)


def mqtt_run():
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(settings.MQTT_LOGIN, password=settings.MQTT_PASSWORD)
    client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 62)
    client.reconnect_delay_set(min_delay=1, max_delay=2000)
    # start up
    #mqttthread = Thread(target=mqttfunction)
    #mqttthread.start()
    mqttfunction()


# if __name__ == "__main__":
#     mqtt_run()


