"""
    Tools for internal use
"""

import logging
import sys
import time
from datetime import datetime

import pandas as pd
import streamlit as st
from psycopg2 import connect
from scipy.signal import savgol_filter

import app.mosquito_handler.config
from app.db_config import psycopg2_db_name, psycopg2_user, psycopg2_password, psycopg2_host, streamlit_db_name

mqtt_tables = []
logger = logging.getLogger( "streamlit_app" )


def get_connection() -> st.connection:
    """
    Connect to the database
    :return: connection to the database from streamlit
    """
    return st.connection( streamlit_db_name, "sql", ttl=5 * 60 )


def get_connection_headless():
    """
    Connect to the database
    :return: connection to the database from psycopg2
    """
    return connect(
        dbname=psycopg2_db_name,
        user=psycopg2_user,
        password=psycopg2_password,
        host=psycopg2_host,
    )


def __create_town_table_if_not_exists( town: str ):
    """
    Create a table if it does not exist.
    :param town: name of the town.
    """

    conn = get_connection_headless()
    cursor = conn.cursor()
    create_table_query = f"""CREATE TABLE IF NOT EXISTS \"{town}\" (
            date_time timestamp PRIMARY KEY,
            avg_temp FLOAT,
            max_temp FLOAT,
            min_temp FLOAT,
            precipitation FLOAT,
            snow_height FLOAT
        );
    """

    cursor.execute( create_table_query )
    conn.commit()
    cursor.close()
    conn.close()


def mqtt_callback( msg: str ):
    """
    Callback function for MQTT messages.
    :param msg: message received.
    """
    mess = msg.split( ":" )
    if len( mess ) != 2:
        logger.error( "mqtt_callback: Invalid message format" )
        return

    location, data = mess

    try:
        temp = float( data.strip( "°C" ) )
    except ValueError:
        logger.error( "mqtt_callback: Temperature is not a number: %s", data )
        return

    if location == "":
        logger.error( "mqtt_callback: Location is empty" )
        return

    if temp == "":
        logger.error( "mqtt_callback: Temperature is empty" )
        return

    logger.info( "Location: %s, Temperature: %s", location, temp )

    if location not in mqtt_tables:
        mqtt_tables.append( location )
        __create_town_table_if_not_exists( "mqtt-" + location )

    conn = get_connection_headless()
    cursor = conn.cursor()

    sql = f"""INSERT INTO \"mqtt-{location}\" (date_time, avg_temp)
    VALUES (NOW(), {temp})"""

    cursor.execute( sql )
    conn.commit()
    cursor.close()
    conn.close()


def mqtt_disconnect():
    """
    Disconnect from MQTT broker
    :return: None
    """

    if not app.mosquito_handler.config.enable:
        return

    app.mosquito_handler.config.running = False
    app.mosquito_handler.config.mqtt_client.disconnect()


def smooth_out_data(
        df: pd.DataFrame, y_name: str, method: str, **varargs
):
    """
    Smooth out data using different methods.
    :param df: dataframe with the data.
    :param y_name: name of the y-axis.
    :param method: method to use for smoothing.
    :param window_size: size of the window for moving average.
    :param window_length: length of the window for Savitzky-Golay filter.
    :param polyorder: order of the polynomial for Savitzky-Golay filter.
    :return: smoothed data.
    """
    smoothed = None
    window_size = varargs.get( "window_size", None )
    window_length = varargs.get( "window_length", None )
    polyorder = varargs.get( "polyorder", None )

    if method == "Moving Average" and window_size is not None:
        # Using pandas rolling to smooth data
        smoothed = df[y_name].rolling( window=window_size, center=True ).mean()

    elif method == "Savitzky-Golay" and window_length is not None and polyorder is not None:
        try:
            smoothed = savgol_filter( df[y_name], window_length=window_length, polyorder=polyorder )
        except Exception as e:
            logger.error( "Error in smoothing: %s", e )
            raise ValueError( f'Error in smoothing: {e}' ) from e

    return smoothed


def render_smooth_func_ui_and_get():
    """
    Render getter for smoothing function info and return the values.
    :return: method, window_size, window_length, polyorder.
    """
    method = st.sidebar.radio(
        "Smoothing Method", ["None", "Moving Average", "Savitzky-Golay"], index=1,
        help="Method to use for smoothing the data in graph."
    )
    window_size = window_length = polyorder = None

    if method == "Moving Average":
        window_size = st.sidebar.slider(
            "Window Size", min_value=3, max_value=101, step=2, value=11,
            help="Size of the moving average window (odd numbers work best)."
        )

    elif method == "Savitzky-Golay":
        window_length = st.sidebar.slider(
            "Window Length", min_value=5, max_value=71, step=2, value=11,
            help="Length of the filter window (must be odd)."
        )
        polyorder = st.sidebar.slider(
            "Polynomial Order", min_value=2, max_value=5, value=3,
            help="Order of the polynomial used to fit the samples."
        )

    return method, window_size, window_length, polyorder


def get_database_town_names() -> list[str]:
    """
    Get the names of the towns in the database.
    :return: List of town names.
    """
    conn = get_connection()

    tables = conn.query( "SELECT table_name FROM information_schema.tables WHERE table_schema='public';", ttl=3 )

    # transform the pd.DataFrame to a list of strings
    tables = tables.iloc[:, 0].tolist()

    return tables


def group_by_day( df: pd.DataFrame ) -> pd.DataFrame:
    """
    Group data by day and calculate the mean for each day.
    :param df: Dataframe with the data.
    :return: Grouped dataframe.
    """
    df = df.groupby( pd.Grouper( key='date_time', freq='D' ) ).agg(
        {
            "avg_temp": "mean",
            "min_temp": "min",
            "max_temp": "max",
            "precipitation": "sum",
            "snow_height": "sum"
        }
    ).reset_index()
    return df


def group_by_hour( df: pd.DataFrame ) -> pd.DataFrame:
    """
    Group data by day and calculate the mean for each day.
    :param df: Dataframe with the data.
    :return: Grouped dataframe.
    """
    df = df.groupby( pd.Grouper( key='date_time', freq='h' ) ).agg(
        {
            "avg_temp": "mean",
            "min_temp": "min",
            "max_temp": "max",
            "precipitation": "sum",
            "snow_height": "sum"
        }
    ).reset_index()
    return df


@st.cache_data( show_spinner=True )
def sort_cached_towns( towns: list[str] ) -> list[str]:
    """
    Sorts the towns in the list.
    :param towns: List of towns to sort.
    :return: Sorted list of towns.
    """
    return sorted( towns )


@st.cache_data( show_spinner=True )
def get_cropped_czechia_towns( towns: list[str] ) -> list[str]:
    """
    Crops the town names to remove the "czechia-" prefix.
    :param towns: List of towns to crop.
    :return: List of cropped towns.
    """
    return [town[8:] for town in towns if town.startswith( "czechia-" )]


@st.cache_data( show_spinner=True )
def get_cropped_france_towns( towns: list[str] ) -> list[str]:
    """
    Crops the town names to remove the "france-" prefix.
    :param towns: List of towns to crop.
    :return: List of cropped towns.
    """
    return [town[7:] for town in towns if town.startswith( "france-" )]


def display_multiselect_for_czechia_and_france_towns( towns: list[str] ) -> tuple[list[str], list[str]]:
    """
    Displays a multiselect for Czechia and France towns.
    :param towns: List of towns to display.
    :return: List of selected towns and their cropped names.
    """
    czechia_towns = get_cropped_czechia_towns( towns )
    france_towns = get_cropped_france_towns( towns )

    selected_towns_cropped: list = st.multiselect( "Czechia towns:", czechia_towns )
    selected_towns_cropped += st.multiselect( "France towns:", france_towns )

    # find selected towns in the original list
    selected_towns = [town for town in towns if
                      town[8:] in selected_towns_cropped or town[7:] in selected_towns_cropped]

    return selected_towns, selected_towns_cropped


def display_date_slider():
    """
    Displays a date slider for selecting the date range.
    """
    date_range = st.sidebar.slider(
        "Date Range",
        min_value=datetime( 1845, 1, 1 ),
        max_value=datetime( time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday ),
        value=(datetime( 2000, 1, 1 ), datetime( 2023, 12, 31 )),
        help="Select a date range to display data for."
    )

    if date_range[0] == date_range[1]:
        st.sidebar.error( "Please select a valid range." )
        st.stop()

    return date_range


def render_stats_day( df: pd.DataFrame ):
    """
    Render statistics where the data is grouped by day.
    """
    st.info(
        f"""
        ### Summary
        - **Maximal Temperature**: :red[{df["max_temp"].max():.2f}°C]
        - **Average Temperature**: :orange[{df["avg_temp"].mean():.2f}°C]
        - **Minimal Temperature**: :blue[{df["min_temp"].min():.2f}°C]
        - **Days Displayed**: :green[{len( df["date_time"] )}]
        """
    )


def create_user_table_if_not_exists():
    """
    Create a table for the user if it does not exist.
    :return: None
    """
    conn = get_connection_headless()
    cursor = conn.cursor()
    create_table_query = """CREATE TABLE IF NOT EXISTS users
                            (
                                user_mail                           VARCHAR PRIMARY KEY,
                                openweather_api_key                 VARCHAR,
                                openweather_selected_town           VARCHAR,
                                openweather_selected_town_longitude FLOAT,
                                openweather_selected_town_latitude  FLOAT
                            ); \
                         """

    cursor.execute( create_table_query )
    conn.commit()
    cursor.close()
    conn.close()


def get_openweather_api_key( headless: bool = False ) -> str:
    """
    Get the OpenWeather API key from a database for currently logged-in user.
    :return: OpenWeather API key.
    """
    if not st.user.is_logged_in:
        raise ValueError( "User is not logged in" )

    mail = st.user.to_dict()["email"]
    query = f"SELECT openweather_api_key FROM users WHERE user_mail = \'{mail}\'"
    api_key: str = ""

    if headless:
        conn = get_connection_headless()
        cursor = conn.cursor()
        cursor.execute( query )
        api_key = cursor.fetchone()[0]
        cursor.close()
        conn.close()
    else:
        conn = get_connection()
        api_key = conn.query( query, ttl=0 ).iloc[0, 0]

    if api_key is None:
        raise ValueError( "API key is not set" )

    return api_key


def get_openweather_selected_town() -> str:
    """
    Get the selected town from the database for currently logged-in user.
    :return: OpenWeather selected town.
    """
    if not st.user.is_logged_in:
        raise ValueError( "User is not logged in" )

    mail = st.user.to_dict()["email"]
    query = f"SELECT openweather_selected_town FROM users WHERE user_mail = \'{mail}\'"
    selected_town: str = ""

    conn = get_connection()
    selected_town = conn.query( query, ttl=0 ).iloc[0, 0]

    if selected_town is None:
        raise ValueError( "Selected town is not set" )

    logger.info( "Selected town: %s", selected_town )

    return selected_town


def insert_logged_in_user():
    """
    Insert the logged-in user into the database.
    :return: None
    """
    conn = get_connection_headless()
    cursor = conn.cursor()

    insert_user_query = f"""
    INSERT INTO users (user_mail) VALUES (\'{st.user.to_dict()["email"]}\')
    ON CONFLICT (user_mail) DO NOTHING
    """
    cursor.execute( insert_user_query )
    conn.commit()
    cursor.close()
    conn.close()


def save_openweather_api_key( api_key: str | None ):
    """
    Save the OpenWeather API key to the database for currently logged-in user.
    :param api_key: OpenWeather API key.
    :return: None
    """
    if not st.user.is_logged_in:
        raise ValueError( "User is not logged in" )

    if api_key is None:
        api_key = "null"
    else:
        api_key = f"\'{api_key}\'"

    mail = st.user.to_dict()["email"]
    query = f"UPDATE users SET openweather_api_key = {api_key} WHERE user_mail = \'{mail}\'"

    conn = get_connection_headless()
    cursor = conn.cursor()
    cursor.execute( query )
    conn.commit()
    cursor.close()
    conn.close()


def save_openweather_selected_town(
        selected_town: str | None, longitude: float | None = None, latitude: float | None = None
):
    """
    Save the selected town to the database for currently logged-in user.
    :param selected_town: OpenWeather selected town.
    :param longitude: Longitude of the selected town.
    :param latitude: Latitude of the selected town.
    :return: None
    """
    if not st.user.is_logged_in:
        raise ValueError( "User is not logged in" )

    if selected_town is None:
        selected_town = "null"
    else:
        selected_town = f"\'{selected_town}\'"

    mail = st.user.to_dict()["email"]
    query = f"UPDATE users SET openweather_selected_town = {selected_town} WHERE user_mail = \'{mail}\'"
    if longitude is not None and latitude is not None:
        query = f"UPDATE users SET openweather_selected_town = {selected_town}, openweather_selected_town_longitude = \'{longitude}\', openweather_selected_town_latitude = \'{latitude}\' WHERE user_mail = \'{mail}\'"

    conn = get_connection_headless()
    cursor = conn.cursor()
    cursor.execute( query )
    conn.commit()
    cursor.close()
    conn.close()


def get_openweather_selected_town_lon_lat():
    """
    Get the selected town longitude and latitude from the database for currently logged-in user.
    :return: Longitude and latitude of the selected town.
    """
    if not st.user.is_logged_in:
        raise ValueError( "User is not logged in" )

    mail = st.user.to_dict()["email"]
    query = f"SELECT openweather_selected_town_longitude, openweather_selected_town_latitude FROM users WHERE user_mail = \'{mail}\'"
    lon_lat: tuple[float, float] = (0.0, 0.0)

    conn = get_connection()
    lon_lat = conn.query( query, ttl=0 ).iloc[0]

    if lon_lat is None:
        raise ValueError( "Selected town is not set" )

    return lon_lat


def get_dataframe_for_towns_and_range( town: str, date_range: tuple[datetime, datetime], conn ) -> pd.DataFrame:
    """
    Get the dataframe for the selected towns and date range.
    :param town: Town name to get data for.
    :param date_range: Date range to get data for.
    :param conn: Database connection.
    :return: Dataframe with the data.
    """
    query = f"""SELECT * FROM \"{town}\"
            WHERE date_time BETWEEN \'{date_range[0].strftime( "%Y-%m-%d" )}\' AND \'{date_range[1].strftime( "%Y-%m-%d" )}\'
            ORDER BY date_time;"""

    df = conn.query( query, ttl=5 * 60 )
    df["date_time"] = pd.to_datetime( df["date_time"] )

    if town.startswith( "france-" ):
        df = group_by_day( df )

    return df


def get_cropped_and_uncropped_selected_towns_from_user() -> tuple[list[str], list[str]]:
    """
    Fetch existing towns from the database and display a multiselect for Czechia and France towns.
    :return: List of selected towns and their cropped names.
    """
    towns = get_database_town_names()

    if len( towns ) == 0:
        st.warning( "No towns found in the database. Please import data first." )
        st.stop()

    towns = sort_cached_towns( towns )

    return display_multiselect_for_czechia_and_france_towns( towns )


def init_logger():
    """
    Initialize the logger for the application.
    """
    logging.basicConfig(
        force=True,
        level=logging.INFO,  # Sets the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format="%(asctime)s - %(levelname)s - %(message)s",  # Specify the log message format
        datefmt="%Y-%m-%d %H:%M:%S",  # Optional: Specify how the timestamp should be formatted
        handlers=[
            logging.StreamHandler( sys.stdout ),  # Log to the console (default)
        ]
    )
