"""
This module handles the connection to the MQTT broker.
"""

import logging
from os import path

from paho.mqtt import client as mqtt_client

if path.exists( path.join( "app", "mosquito_handler", "config.py" ) ):
    from app.mosquito_handler import config
else:
    from app.mosquito_handler import config_template as config

    config.enable = False

logger = logging.getLogger( "streamlit_app" )


def __on_connect( client, userdata, flags, rc ):
    """
    Callback function for when the client connects to the broker.
    :param client: The client instance for this callback
    :param userdata: The user data
    :param flags: Response flags sent by the broker
    :param rc: The connection result
    """
    logger.info( "mqtt: Connected with result code %s", rc )
    if rc == 0:
        logger.info(
            "mqtt: Connected successfully with client: %s, userdata: %s flags: %s",
            client.username, userdata, flags
        )
    else:
        logger.error( "mqtt: Connection failed" )
        raise IOError( "mqtt: Connection failed" )


def __on_message( client, userdata, msg ):
    """
    Callback function for when a message is received from the broker.
    :param client: The client instance for this callback
    :param userdata: The user data
    :param msg: The message instance

    """
    logger.info( "mqtt: Message received from client: %s, userdata: %s", client.username, userdata )
    config.callback( msg.payload.decode() )


def __run():
    """
    Connects to the MQTT broker and subscribes to the topic.
    :return: None
    """
    client = mqtt_client.Client(  # pylint: disable=unexpected-keyword-arg
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1, client_id=config.client_id # pylint: disable=no-member
    )  # pylint doesnt see the correct constructor
    client.username_pw_set( config.username, config.password )
    client.on_connect = __on_connect
    client.on_message = __on_message
    client.connect( config.broker, config.port )
    client.subscribe( config.topic )
    config.mqtt_client = client
    client.loop_forever()
    logger.info( "mqtt: MQTT connection closed" )


def run_mqtt( callback: callable ):
    """
    Connects to the MQTT broker, subscribes and on receive calls the callback function.
    :param callback: Function to call on a message with str as parameter.
    """

    if not config.enable:
        return

    config.callback = callback

    __run()
