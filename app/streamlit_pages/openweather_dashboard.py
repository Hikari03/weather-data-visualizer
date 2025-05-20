"""
Interactive OpenWeather Dashboard
"""

import plotly.graph_objects as go
import streamlit as st

from app.importer.import_data_openweather import get_geo_for_city, fetch_forecast_data, WeatherData
from app.utils import (
    get_openweather_api_key, get_openweather_selected_town,
    save_openweather_api_key, save_openweather_selected_town, get_openweather_selected_town_lon_lat
)

st.set_page_config( layout="wide" )


def run():
    """
    Function to run the OpenWeather dashboard.
    """
    st.title( "OpenWeather Dashboard" )

    if not st.user.is_logged_in:
        st.warning( "Please log in to access this page." )
        st.stop()

    try:
        api_key = get_openweather_api_key()
    except ValueError:
        api_key = "None"

    if api_key == "None":
        enter_api_key()
        st.rerun()

    try:
        selected_town = get_openweather_selected_town()
    except ValueError:
        selected_town = "None"

    if selected_town == "None":
        select_town( api_key )
        st.rerun()

    if st.sidebar.button( "Refresh Data" ):
        st.rerun()

    if st.sidebar.button( "Update API Key" ):
        save_openweather_api_key( None )
        api_key = "None"
        st.rerun()

    if st.sidebar.button( "Select Town" ):
        save_openweather_selected_town( None )
        selected_town = "None"
        st.rerun()

    try:
        weather_data = fetch_forecast_data( api_key, *get_openweather_selected_town_lon_lat() )
    except ConnectionError as e:
        st.error( f"Error fetching data: {e}" )
        st.stop()

    st.markdown(
        f"""
        #### Current Weather Data for :rainbow[{selected_town}]
        """
    )

    st.markdown(
        f"""
        :rainbow-background[<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M17.65 6.35A7.96 7.96 0 0 0 12 4a8 8 0 0 0-8 8a8 8 0 0 0 8 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18a6 6 0 0 1-6-6a6 6 0 0 1 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4z"/></svg> Last refresh: {weather_data.dt.strftime( "%H:%M:%S" )}]
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    render_dashboard( weather_data )


def render_dashboard( weather_data: WeatherData ) -> None:
    """
    Renders the dashboard itself
    :param weather_data: WeatherData object containing the weather data.
    """
    col1, col_2, col_3, col_4, col_5 = st.columns( [0.3, 0.14, 0.14, 0.14, 0.14], border=True )
    with col1:

        col1_1, col1_2 = st.columns( 2, vertical_alignment="bottom" )
        with col1_1:
            st.markdown(
                """
                ## Now  
                """
            )
            if weather_data.weather.icon:
                st.image(
                    f"https://openweathermap.org/img/wn/{weather_data.weather.icon}@2x.png",
                    caption=f"{weather_data.weather.description.capitalize()}",
                    output_format="auto",
                )
            display_temperature( weather_data.temperature.temp, weather_data.temperature.feels_like )

        with col1_2:
            display_sunrise_sunset( weather_data.times.sunrise, weather_data.times.sunset )
            display_pressure_humidity( weather_data.pressure, weather_data.humidity )

        st.divider()

        display_wind_speed( weather_data.wind.speed, weather_data.wind.deg )

        for idx, col in enumerate( [col_2, col_3, col_4, col_5] ):
            with col:
                if weather_data.hourly_data[idx].weather.icon:
                    st.image(
                        f"http://openweathermap.org/img/wn/{weather_data.hourly_data[idx].weather.icon}@4x.png",
                        caption=f"{weather_data.hourly_data[idx].weather.description.capitalize()}",
                        output_format="auto",
                    )

                    st.markdown(
                        f"""
                        ## {weather_data.hourly_data[idx].dt.strftime( "%H:%M" )}
                        """
                    )

                    display_temperature(
                        weather_data.hourly_data[idx].temperature.temp,
                        weather_data.hourly_data[idx].temperature.feels_like
                    )
                    display_pressure_humidity(
                        weather_data.hourly_data[idx].pressure,
                        weather_data.hourly_data[idx].humidity,
                    )
                    display_wind_speed(
                        weather_data.hourly_data[idx].wind.speed,
                        weather_data.hourly_data[idx].wind.deg,
                        height=300,
                    )


def display_temperature( temp, feels_like ):
    """
    Function to display temperature and feels like temperature.
    """

    st.markdown(
        f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M15 13V5a3 3 0 0 0-6 0v8a5 5 0 1 0 6 0m-3-9a1 1 0 0 1 1 1v3h-2V5a1 1 0 0 1 1-1"/></svg> 
        :primary-badge[Temperature: {temp} °C]
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24px" height="24px" viewBox="0 0 24 24" version="1.1"><g id="surface1"><path fill="currentColor" d="M 19.5 22.5 L 16.5 22.5 C 15.671875 22.496094 15.003906 21.828125 15 21 L 15 15.75 C 14.171875 15.746094 13.503906 15.078125 13.5 14.25 L 13.5 9.75 C 13.488281 9.148438 13.722656 8.570312 14.148438 8.148438 C 14.570312 7.722656 15.148438 7.488281 15.75 7.5 L 20.25 7.5 C 20.851562 7.488281 21.429688 7.722656 21.851562 8.148438 C 22.277344 8.570312 22.511719 9.148438 22.5 9.75 L 22.5 14.25 C 22.496094 15.078125 21.828125 15.746094 21 15.75 L 21 21 C 20.996094 21.828125 20.328125 22.496094 19.5 22.5 Z M 15.75 9 C 15.546875 8.988281 15.351562 9.0625 15.207031 9.207031 C 15.0625 9.351562 14.988281 9.546875 15 9.75 L 15 14.25 L 16.5 14.25 L 16.5 21 L 19.5 21 L 19.5 14.25 L 21 14.25 L 21 9.75 C 21.011719 9.546875 20.9375 9.351562 20.792969 9.207031 C 20.648438 9.0625 20.453125 8.988281 20.25 9 Z M 15.75 9 "/><path fill="currentColor" d="M 18 6.75 C 16.34375 6.75 15 5.40625 15 3.75 C 15 2.09375 16.34375 0.75 18 0.75 C 19.65625 0.75 21 2.09375 21 3.75 C 20.996094 5.40625 19.65625 6.746094 18 6.75 Z M 18 2.25 C 17.171875 2.25 16.5 2.921875 16.5 3.75 C 16.5 4.578125 17.171875 5.25 18 5.25 C 18.828125 5.25 19.5 4.578125 19.5 3.75 C 19.496094 2.921875 18.828125 2.253906 18 2.25 Z M 18 2.25 "/><path fill="currentColor" d="M 7.5 15.136719 L 7.5 9 L 6 9 L 6 15.136719 C 4.96875 15.503906 4.347656 16.558594 4.53125 17.640625 C 4.71875 18.71875 5.652344 19.507812 6.75 19.507812 C 7.847656 19.507812 8.78125 18.71875 8.96875 17.640625 C 9.152344 16.558594 8.53125 15.503906 7.5 15.136719 Z M 7.5 15.136719 "/><path fill="currentColor" d="M 6.75 22.5 C 4.636719 22.503906 2.730469 21.234375 1.910156 19.289062 C 1.089844 17.339844 1.519531 15.089844 3 13.582031 L 3 5.25 C 3 3.179688 4.679688 1.5 6.75 1.5 C 8.820312 1.5 10.5 3.179688 10.5 5.25 L 10.5 13.582031 C 11.980469 15.089844 12.410156 17.339844 11.589844 19.289062 C 10.769531 21.234375 8.863281 22.503906 6.75 22.5 Z M 6.75 3 C 5.507812 3 4.5 4.007812 4.5 5.25 L 4.5 14.238281 L 4.25 14.460938 C 3.089844 15.496094 2.691406 17.140625 3.246094 18.59375 C 3.800781 20.046875 5.195312 21.007812 6.75 21.007812 C 8.304688 21.007812 9.699219 20.046875 10.253906 18.59375 C 10.808594 17.140625 10.410156 15.496094 9.25 14.460938 L 9 14.238281 L 9 5.25 C 9 4.007812 7.992188 3 6.75 3 Z M 6.75 3 "/></g></svg>
        :green-badge[Feels like: {feels_like} °C]
        """,
        unsafe_allow_html=True,
    )


def display_sunrise_sunset( sunrise, sunset ):
    """
    Function to display sunrise and sunset times.
    """

    st.markdown(
        f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M3 12h4a5 5 0 0 1 5-5a5 5 0 0 1 5 5h4a1 1 0 0 1 1 1a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1a1 1 0 0 1 1-1m12 0a3 3 0 0 0-3-3a3 3 0 0 0-3 3zM12 2l2.39 3.42C13.65 5.15 12.84 5 12 5s-1.65.15-2.39.42zM3.34 7l4.16-.35A7.2 7.2 0 0 0 5.94 8.5c-.44.74-.69 1.5-.83 2.29zm17.31 0l-1.77 3.79a7.02 7.02 0 0 0-2.38-4.15zm-7.94 9.3l3.11 3.11a.996.996 0 1 1-1.41 1.41L12 18.41l-2.41 2.41a.996.996 0 1 1-1.41-1.41l3.11-3.11c.21-.2.45-.3.71-.3s.5.1.71.3"/></svg>
         :orange-badge[Sunrise: {sunrise.strftime( "%H:%M" )}]
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M3 12h4a5 5 0 0 1 5-5a5 5 0 0 1 5 5h4a1 1 0 0 1 1 1a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1a1 1 0 0 1 1-1m12 0a3 3 0 0 0-3-3a3 3 0 0 0-3 3zM12 2l2.39 3.42C13.65 5.15 12.84 5 12 5s-1.65.15-2.39.42zM3.34 7l4.16-.35A7.2 7.2 0 0 0 5.94 8.5c-.44.74-.69 1.5-.83 2.29zm17.31 0l-1.77 3.79a7.02 7.02 0 0 0-2.38-4.15zm-7.94 13.71l3.11-3.11c.39-.39.39-1.03 0-1.42a.996.996 0 0 0-1.41 0L12 18.59l-2.41-2.41a.996.996 0 0 0-1.41 0c-.39.39-.39 1.03 0 1.42l3.11 3.11c.21.19.45.29.71.29s.5-.1.71-.29"/></svg>
         :red-badge[Sunset: {sunset.strftime( "%H:%M" )}]
        """,
        unsafe_allow_html=True,
    )


def display_pressure_humidity( pressure, humidity ):
    """
    Function to display pressure and humidity.
    """

    st.markdown(
        f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M19.5 3.09L15 7.59V4h-2v7h7V9h-3.59l4.5-4.5zM4 13v2h3.59l-4.5 4.5l1.41 1.41l4.5-4.5V20h2v-7z"/></svg>
        :violet-badge[Pressure: {pressure} hPa]
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="m12 3.77l-.75.84S9.97 6.06 8.68 7.94S6 12.07 6 14.23a6 6 0 0 0 6 6a6 6 0 0 0 6-6c0-2.16-1.39-4.41-2.68-6.29s-2.57-3.33-2.57-3.33zm0 3.13c.44.52.84.95 1.68 2.17c1.21 1.76 2.32 4 2.32 5.16c0 2.22-1.78 4-4 4s-4-1.78-4-4c0-1.16 1.11-3.4 2.32-5.16c.84-1.22 1.24-1.65 1.68-2.17"/></svg>
        :blue-badge[Humidity: {humidity} %]
        """,
        unsafe_allow_html=True,
    )


def display_wind_speed( wind_speed, wind_deg, height=500 ):
    """
    Function to display wind speed and direction in a polar graph.
    :param wind_speed: Wind speed in m/s.
    :param wind_deg: Wind direction in degrees.
    :param height: Height of the polar graph.
    """
    st.markdown(
        f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M4 10a1 1 0 0 1-1-1a1 1 0 0 1 1-1h8a2 2 0 0 0 2-2a2 2 0 0 0-2-2c-.55 0-1.05.22-1.41.59a.973.973 0 0 1-1.42 0c-.39-.39-.39-1.03 0-1.42C9.9 2.45 10.9 2 12 2a4 4 0 0 1 4 4a4 4 0 0 1-4 4zm15 2a1 1 0 0 0 1-1a1 1 0 0 0-1-1c-.28 0-.53.11-.71.29a.996.996 0 0 1-1.41 0c-.38-.39-.38-1.02 0-1.41C17.42 8.34 18.17 8 19 8a3 3 0 0 1 3 3a3 3 0 0 1-3 3H5a1 1 0 0 1-1-1a1 1 0 0 1 1-1zm-1 6H4a1 1 0 0 1-1-1a1 1 0 0 1 1-1h14a3 3 0 0 1 3 3a3 3 0 0 1-3 3c-.83 0-1.58-.34-2.12-.88c-.38-.39-.38-1.02 0-1.41a.996.996 0 0 1 1.41 0c.18.18.43.29.71.29a1 1 0 0 0 1-1a1 1 0 0 0-1-1"/></svg>
        :gray-badge[Wind Speed: {wind_speed} m/s]
        """,
        unsafe_allow_html=True,
    )

    wind_deg = (wind_deg + 270) % 360

    # Create a polar plot
    fig = go.Figure()
    fig.add_trace(
        go.Barpolar(
            r=[wind_speed],
            theta=[wind_deg],
            name="Wind Speed",
            hovertemplate="Wind Speed: %{r:.2f} m/s<br>Direction: %{theta:.2f}°<extra></extra>",
            text=[f"{wind_speed:.2f} m/s"],
            opacity=0.8,
            hoverlabel={
                'bgcolor': "white",
                'font': {
                    'size': 14,
                    'color': "black"
                }
            },
        )
    )

    max_wind_speed = 20 if wind_speed > 20 / 2 else wind_speed + 5

    fig.update_layout(
        template="plotly_dark",
        polar={
            'radialaxis': {
                'visible': True,
                'range': [0, max_wind_speed]  # Adjust the range as needed
            },
            'angularaxis': {
                'tickmode': 'array',
                'tickvals': [0, 90, 180, 270],
                'ticktext': ['E', 'N', 'W', 'S'],
            }
        },
        showlegend=False,
        height=height,
    )

    st.plotly_chart( fig, use_container_width=True )


def select_town( api_key ):
    """
    Function to select a town from a user input.
    """

    st.subheader( "Select a Town" )
    town = st.text_input( "Enter the name of the town:" )

    if town:
        try:
            geo_data = get_geo_for_city( api_key, town )
            town_list: list[str] = []
            for _, value in geo_data.items():
                town_list.append( f"{value.name}, {value.state}, {value.country}" )
            selected = st.selectbox(
                "Select a town",
                options=town_list,
            )
            if st.button( "Confirm " ):
                selected_town = selected.split( "," )[0].strip()
                save_openweather_selected_town(
                    selected_town, geo_data[selected_town].lat, geo_data[selected_town].lon
                )
                st.success( f"Weather data for {selected_town} fetched successfully!" )

        except ConnectionError as e:
            st.error( f"Error fetching data: {e}" )


def enter_api_key():
    """
    Function to enter the OpenWeather API key.
    """

    st.subheader( "Enter OpenWeather API Key" )
    api_key = st.text_input( "API Key", type="password", value="", icon=":material/key_vertical:" )

    if st.button( "Save API Key" ):
        if api_key:
            try:
                save_openweather_api_key( api_key )
                st.success( "API Key saved successfully!" )
            except ValueError as e:
                st.error( f"Error saving API Key: {e}" )
        else:
            st.error( "Please enter a valid API Key." )


run()
