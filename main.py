"""
Main file for the Streamlit application.
"""
import logging

import streamlit as st

from app.utils import init_logger

init_logger()

logger = logging.getLogger( "streamlit_app" )

login_page = st.Page( "app/streamlit_pages/login.py", title="Login", icon=":material/login:" )

import_page = st.Page( "app/streamlit_pages/import_page.py", title="Import", icon=":material/cloud_download:" )
delete_page = st.Page( "app/streamlit_pages/delete_location.py", title="Delete Data", icon=":material/delete:" )

main_page = st.Page( "app/streamlit_pages/main.py", title="Main Page", icon=":material/home:" )
visualize_page = st.Page(
    "app/streamlit_pages/town_visualize.py", title="Visualize", icon=":material/stacked_line_chart:"
)
openweather_page = st.Page(
    "app/streamlit_pages/openweather_dashboard.py", title="OpenWeather", icon=":material/thermostat:"
)
mqtt_page = st.Page( "app/streamlit_pages/mqtt.py", title="Visualize MQTT", icon=":material/podcasts:" )
compare_page = st.Page( "app/streamlit_pages/compare.py", title="Compare Towns", icon=":material/compare_arrows:" )
aggregate_page = st.Page( "app/streamlit_pages/aggregate.py", title="Aggregate", icon=":material/mediation:" )
precipitation_snow_page = st.Page(
    "app/streamlit_pages/precipitation_snow.py", title="Precipitation and Snow", icon=":material/weather_mix:"
)

pages = {}
pages["Visualize Data"] = [main_page, openweather_page, visualize_page, mqtt_page, compare_page, aggregate_page,
                           precipitation_snow_page]
pages["Login"] = [login_page]

if st.user.is_logged_in and st.user.to_dict()["email"] == st.secrets["admin_email"]:
    pages["Administration"] = [import_page, delete_page]

st.logo( "assets/icons/logo.png", size="large" )

pg = st.navigation( pages )
logger.info( "Starting Streamlit app" )
pg.run()
