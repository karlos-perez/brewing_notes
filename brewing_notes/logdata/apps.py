import logging
import paho.mqtt.client as mqtt
from threading import Thread

from django.apps import AppConfig
from django.conf import settings


logger = logging.getLogger(__name__)


class MqttClient(Thread):
# class MqttClient(object):
    def __init__(self, broker, port, timeout, topics):
        super(MqttClient, self).__init__()
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.timeout = timeout
        self.topics = topics
        # self.total_messages = 0

    #  run method override from Thread class
    def run(self):
        self.connect_to_broker()

    def connect_to_broker(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(settings.MQTT_LOGIN, password=settings.MQTT_PASSWORD)
        self.client.connect(self.broker, self.port, self.timeout)
        # self.client.username_pw_set(settings.MQTT_LOGIN, password=settings.MQTT_PASSWORD)
        self.client.loop_forever()

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        try:
            # logger.debug(f'Topic: {msg.topic} - Payload: {str(msg.payload)}')
            from .views import module_record
            module_record(msg.payload)
        except Exception as err:
            logger.error(f'Error record log Module: {err}')

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        #  Subscribe to a list of topics using a lock to guarantee that a topic is only subscribed once
        for topic in self.topics:
            client.subscribe(topic)
        if rc != 0:
            logger.error(f'MQTT Connection returned result: {mqtt.connack_string(rc)}')


class LogdataConfig(AppConfig):
    name = 'logdata'
#     default_auto_field = 'django.db.models.BigAutoField'
#
#     def ready(self):
#         logger.debug(f'Connect MQTT....')
#         MqttClient(settings.MQTT_HOST, settings.MQTT_PORT, 60, ["BNCmodule/+/state",]).start()
        # MqttClient(settings.MQTT_HOST, settings.MQTT_PORT, 60, ["BNCmodule/+/state",]).run()


