"""
This file contains the configuration for the MQTT client.
"""
# This file is a template. You need to rename it to config.py and fill in the values.
# !!!! RENAME THIS FILE TO config.py !!!!

import random

from paho.mqtt import client

# Make this true if you want to run the mqtt client.
enable = False

broker = ''
port = 1883
topic = ""

client_id = "weather_data_" + str( random.randint( 0, 1000 ) )  # You dont need to change this
username = ''
password = ''

##### DO NOT CHANGE #####
callback: callable = None
mqtt_client: client = None
