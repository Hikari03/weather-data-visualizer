"""
Fetches weather data from OpenWeather API and stores it in a database.
"""
import datetime
from dataclasses import dataclass
from datetime import timezone

import requests
import streamlit as st


@dataclass
class GeoData:
    """
    Represents geographical data for a city.
    """
    lat: float
    lon: float
    name: str
    country: str
    state: str


@dataclass
class TemperatureData:
    """
    Represents temperature data.
    """
    temp: float
    feels_like: float


@dataclass
class WindData:
    """
    Represents wind data.
    """
    speed: float
    deg: int


@dataclass
class WeatherCondition:
    """
    Represents weather conditions.
    """
    description: str
    icon: str


@dataclass
class HourlyWeatherData:
    """
    Represents hourly weather data.
    """
    dt: datetime.datetime
    temperature: TemperatureData
    pressure: int
    humidity: int
    wind: WindData
    weather: WeatherCondition


@dataclass
class DayNightTimes:
    """
    Represents sunrise and sunset times.
    """
    sunrise: datetime.datetime
    sunset: datetime.datetime


@dataclass  # no way of making this smaller without losing readability
class WeatherData:  # pylint: disable=too-many-instance-attributes
    """
    Represents weather data for a city.
    """
    dt: datetime.datetime
    times: DayNightTimes
    temperature: TemperatureData
    pressure: int
    humidity: int
    wind: WindData
    weather: WeatherCondition
    hourly_data: list[HourlyWeatherData]


def parse_geo_response( json_response ) -> dict[str, GeoData]:
    """
    Parses the JSON response from OpenWeather API to extract geographical data.
    :param json_response: The JSON response from OpenWeather API.
    :return: A dictionary with city names as keys and GeoData objects as values.
    """

    geo_data = {}
    for item in json_response:
        lat = item.get( "lat" )
        lon = item.get( "lon" )
        name = item.get( "name" )
        country = item.get( "country" )
        state = item.get( "state" )
        if lat and lon and name and country and state:
            geo_data[name] = GeoData( lat, lon, name, country, state )
    return geo_data


@st.cache_data( ttl=60 * 5 )
def get_geo_for_city( api_key, city_name ):
    """
    Fetches geographical data for a given city from OpenWeather API.
    :param api_key: The API key for OpenWeather.
    :param city_name: The name of the city.
    """

    url = f"https://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=5&appid={api_key}"
    response = requests.get( url, timeout=5 )

    if response.status_code == 200:
        return parse_geo_response( response.json() )

    raise ConnectionError( f"Error fetching data: {response.status_code} - {response.text}" )


def parse_forecast_response(  # pylint: disable=too-many-locals # The variables are needed for readability
        json_response
) -> WeatherData:
    """
    Parses the JSON response from OpenWeather API to extract weather data.
    :param json_response: The JSON response from OpenWeather API.
    :return: A WeatherData object containing the parsed data.
    """

    time_zone_offset = json_response.get( "timezone_offset" )
    tz = timezone( datetime.timedelta( seconds=time_zone_offset ) )
    current = json_response.get( "current" )
    dt = datetime.datetime.fromtimestamp( current.get( "dt" ), tz=tz )
    sunrise = datetime.datetime.fromtimestamp( current.get( "sunrise" ), tz=tz )
    sunset = datetime.datetime.fromtimestamp( current.get( "sunset" ), tz=tz )
    temp = current.get( "temp" )
    feels_like = current.get( "feels_like" )
    pressure = current.get( "pressure" )
    humidity = current.get( "humidity" )
    wind_speed = current.get( "wind_speed" )
    wind_deg = current.get( "wind_deg" )
    weather_description = current["weather"][0].get( "description" )
    weather_icon = current["weather"][0].get( "icon" )

    # Extracting hourly weather data
    hourly_data = []
    for hour in json_response.get( "hourly", [] ):
        hourly_dt = datetime.datetime.fromtimestamp( hour.get( "dt" ), tz=tz )
        hourly_temp = hour.get( "temp" )
        hourly_feels_like = hour.get( "feels_like" )
        hourly_pressure = hour.get( "pressure" )
        hourly_humidity = hour.get( "humidity" )
        hourly_wind_speed = hour.get( "wind_speed" )
        hourly_wind_deg = hour.get( "wind_deg" )
        hourly_weather_description = hour["weather"][0].get( "description" )
        hourly_weather_icon = hour["weather"][0].get( "icon" )

        hourly_data.append(
            HourlyWeatherData(
                hourly_dt,
                TemperatureData( hourly_temp, hourly_feels_like ),
                hourly_pressure,
                hourly_humidity,
                WindData( hourly_wind_speed, hourly_wind_deg ),
                WeatherCondition( hourly_weather_description, hourly_weather_icon ),
            )
        )

    return WeatherData(
        dt,
        DayNightTimes( sunrise, sunset ),
        TemperatureData( temp, feels_like ),
        pressure,
        humidity,
        WindData( wind_speed, wind_deg ),
        WeatherCondition( weather_description, weather_icon ),
        hourly_data,
    )


@st.cache_data( ttl=60 * 5 )
def fetch_forecast_data( api_key, lat, lon, units='metric' ):
    """
    Fetches weather forecast data from OpenWeather API for a given city ID.
    :param api_key: The API key for OpenWeather.
    :param lat: The latitude of the city.
    :param lon: The longitude of the city.
    :param units: The unit system to use (metric, imperial, or standard).
    """

    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=alerts&appid={api_key}&units={units}"
    response = requests.get( url, timeout=5 )

    if response.status_code == 200:
        return parse_forecast_response( response.json() )

    raise ConnectionError( f"Error fetching data: {response.status_code} - {response.text}" )
