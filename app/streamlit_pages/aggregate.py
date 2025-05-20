"""
This page is used to aggregate data from multiple stations.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.utils import (
    get_connection, group_by_day, render_smooth_func_ui_and_get, render_stats_day,
    get_cropped_and_uncropped_selected_towns_from_user
)
from app.utils import (
    smooth_out_data, display_date_slider
)

st.set_page_config( layout="wide" )
st.title( "Aggregate Data" )
st.write( "Select towns to aggregate data for:" )

# pylint: disable=R0801
# We need all these variables and making a class for them would be less readable
selected_towns, selected_towns_cropped = get_cropped_and_uncropped_selected_towns_from_user()

date_range = display_date_slider()
st.sidebar.divider()
method, window_size, window_length, polyorder = render_smooth_func_ui_and_get()
smoothing = method != "None"  # are we smoothing the data?
# pylint: enable=R0801

if len( selected_towns ) == 0:
    st.warning( "Please select at least one town to aggregate data." )
    st.stop()

df_aggregated = pd.DataFrame()

conn = get_connection()

for town in selected_towns:
    query = f"""
        SELECT date_time, avg_temp, min_temp, max_temp, precipitation, snow_height
        FROM \"{town}\"
        WHERE date_time BETWEEN '{date_range[0]}' AND '{date_range[1]}'
    """

    df = conn.query( query )
    df["date_time"] = pd.to_datetime( df["date_time"] )
    if town.startswith( "france-" ):
        df = group_by_day( df )

    # Add the data to the aggregated DataFrame
    df_aggregated = pd.concat( [df_aggregated, df], ignore_index=True )

df_aggregated = df_aggregated.groupby( "date_time" ).agg(
    {
        "avg_temp": "mean",
        "min_temp": "min",
        "max_temp": "max"
    }
).reset_index()

if smoothing:
    for col in ["avg_temp", "min_temp", "max_temp"]:
        df_aggregated[col] = smooth_out_data(
            df_aggregated, col, method, window_size=window_size, window_length=window_length, polyorder=polyorder
        )

# Create a figure with two subplots
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df_aggregated["date_time"],
        y=df_aggregated["max_temp"],
        mode="lines",
        name="Maximal Temperature",
        line={
            "color": 'red',
            "width": 3
        },
    )
)

fig.add_trace(
    go.Scatter(
        x=df_aggregated["date_time"],
        y=df_aggregated["avg_temp"],
        mode="lines",
        name="Average Temperature",
        line={
            "color": 'orange',
            "width": 3
        },
    )
)

fig.add_trace(
    go.Scatter(
        x=df_aggregated["date_time"],
        y=df_aggregated["min_temp"],
        mode="lines",
        name="Minimal Temperature",
        line={
            "color": 'yellow',
            "width": 3
        },
    )
)

fig.update_layout(
    title="Aggregated Data: Average, Maximal and Minimal Temperature",
    xaxis_title="Date",
    yaxis_title="Temperature (°C)",
    xaxis_rangeslider_visible=True,
    hovermode="x unified"
)

col1, col2 = st.columns( [0.75, 0.25], border=True )

with col1:
    st.plotly_chart( fig, use_container_width=True )

with col2:
    render_stats_day( df_aggregated )
