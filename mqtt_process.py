"""
Meant to be run as a separate process to handle MQTT connections.
"""

import atexit

from filelock import FileLock

from app.mosquito_handler.connection import run_mqtt
from app.utils import mqtt_callback, mqtt_disconnect, init_logger

init_logger()

if __name__ == '__main__':
    # Set up a file lock to prevent multiple instances from running
    lock_file = "mqtt.lock"
    lock = FileLock( lock_file, timeout=10 )

    with lock.acquire():
        # Register the cleanup function to be called on exit
        atexit.register( mqtt_disconnect )

        # Start the MQTT client in a separate process
        run_mqtt( mqtt_callback )
