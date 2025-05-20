"""
This page allows users to compare two different towns in specified time ranges.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.utils import (
    group_by_day, display_date_slider,
    render_smooth_func_ui_and_get, smooth_out_data, get_connection, get_cropped_and_uncropped_selected_towns_from_user
)

st.set_page_config( layout="wide" )
st.title( "Compare Towns" )
st.write( "Select two towns to compare:" )

selected_towns, selected_towns_cropped = get_cropped_and_uncropped_selected_towns_from_user()

date_range = display_date_slider()
st.sidebar.divider()
method, window_size, window_length, polyorder = render_smooth_func_ui_and_get()

if len( selected_towns ) != 2:
    st.warning( "Please select exactly two towns to compare." )
    st.stop()

conn = get_connection()
query = f"""SELECT * FROM \"{selected_towns[0]}\"
WHERE date_time BETWEEN \'{date_range[0].strftime( "%Y-%m-%d" )}\' AND \'{date_range[1].strftime( "%Y-%m-%d" )}\'
ORDER BY date_time;"""

query1 = f"""SELECT * FROM \"{selected_towns[1]}\"
WHERE date_time BETWEEN \'{date_range[0].strftime( "%Y-%m-%d" )}\' AND \'{date_range[1].strftime( "%Y-%m-%d" )}\'
ORDER BY date_time;"""

df1 = conn.query( query )
df1["date_time"] = pd.to_datetime( df1["date_time"] )

df2 = conn.query( query1 )
df2["date_time"] = pd.to_datetime( df2["date_time"] )

# if selected_towns[0].startswith("france-"):
df1 = group_by_day( df1 )
# if selected_towns[1].startswith("france-"):
df2 = group_by_day( df2 )

# Smooth the data if required
if method != "None":
    df1_smoothed = smooth_out_data(
        df1, "avg_temp", method, window_size=window_size, window_length=window_length, polyorder=polyorder
    )
    df2_smoothed = smooth_out_data(
        df2, "avg_temp", method, window_size=window_size, window_length=window_length, polyorder=polyorder
    )
else:
    df1_smoothed = df1["avg_temp"]
    df2_smoothed = df2["avg_temp"]

# Create a figure with two subplots
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df1["date_time"],
        y=df1_smoothed,
        mode="lines",
        name=f"{selected_towns_cropped[0]}",
        line={'color': "#9AE600"},
        opacity=0.8
    )
)
fig.add_trace(
    go.Scatter(
        x=df2["date_time"],
        y=df2_smoothed,
        mode="lines",
        name=f"{selected_towns_cropped[1]}",
        line={'color': "#FB2C36"},
        opacity=0.8
    )
)

fig.update_layout(
    title=f"Temperature Comparison between {selected_towns_cropped[0]} and {selected_towns_cropped[1]}",
    xaxis_title="Date",
    yaxis_title="Average Temperature (°C)",
    legend_title="Towns",
    xaxis_rangeslider_visible=True,
    xaxis_rangeslider_thickness=0.05,
    hovermode="x unified",
    height=500,
)

col1, col2 = st.columns( [0.75, 0.25], border=True )
with col1:
    st.plotly_chart( fig )

with col2:
    sum1 = df1["avg_temp"].sum()
    sum2 = df2["avg_temp"].sum()
    total_days1 = len( df1 )
    total_days2 = len( df2 )

    if total_days1 == 0 or total_days2 == 0:
        st.error( "No data available for the selected date range." )
        st.stop()

    avg1 = sum1 / total_days1
    avg2 = sum2 / total_days2
    diff = avg2 - avg1

    st.info(
        f"""
        ### Summary
        - **Average Temperature**:
            - **{selected_towns_cropped[0]}**: {avg1:.2f}°C
            - **{selected_towns_cropped[1]}**: {avg2:.2f}°C
        - **Total Days**:
            - **{selected_towns_cropped[0]}**: {total_days1}
            - **{selected_towns_cropped[1]}**: {total_days2}
        """
    )

    if diff > 0:
        st.error( f"***{selected_towns_cropped[1]} is warmer by {diff:.2f}°C***", icon=":material/arrow_downward:" )
    elif diff < 0:
        st.success(
            f"***{selected_towns_cropped[0]} is warmer by {abs( diff ):.2f}°C***", icon=":material/arrow_upward:"
        )
