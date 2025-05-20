#!/usr/bin/bash
# This script is used to run the app as we need to run main app and mosquito receiver in separate processes

# start mosquitto
python3 mqtt_process.py & disown
# start the main app
streamlit run main.py --server.port=8502 --browser.gatherUsageStats=false