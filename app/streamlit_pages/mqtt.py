"""
Visualizes mqtt data for selected towns
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.utils import smooth_out_data, render_smooth_func_ui_and_get, group_by_hour, group_by_day, get_connection

st.set_page_config( layout="wide" )
st.title( "Visualize MQTT Data" )
st.write( "Select towns to visualize data for:" )

# Get the list of tables in the database
conn = get_connection()

tables = conn.query( "SELECT table_name FROM information_schema.tables WHERE table_schema='public';", ttl=5 ).iloc[:,
         0].tolist()

mqtt_tables = [table for table in tables if table.startswith( "mqtt-" )]
mqtt_tables = sorted( mqtt_tables )

if len( mqtt_tables ) == 0:
    st.info( "No MQTT data found in the database. Please import data first." )
    st.info( "If you want to use MQTT, you have to define info in `app/mosquito_handler/config.py` and use run.sh." )
    st.stop()

# strip the prefix "mqtt-" from the table names
for idx, table in enumerate( mqtt_tables ):
    mqtt_tables[idx] = table[5:]

selected_towns: list = st.multiselect( "Towns", mqtt_tables )

method, window_size, window_length, polyorder = render_smooth_func_ui_and_get()

st.sidebar.divider()

grouping_by = st.sidebar.radio( "Group by", ["None", "Hour", "Day"], index=2 )

if len( selected_towns ) > 0:
    tabs = st.tabs( selected_towns )
    for idx, tab in enumerate( tabs ):
        local_method = method
        query = f"""SELECT * FROM \"mqtt-{selected_towns[idx]}\" ORDER BY date_time;"""

        df = conn.query( query )
        df["date_time"] = pd.to_datetime( df["date_time"] )
        if grouping_by == "Hour":
            df_grouped = group_by_hour( df )
        elif grouping_by == "Day":
            df_grouped = group_by_day( df )
        else:
            df_grouped = df

        fig = go.Figure()

        if local_method == "None":
            fig.add_trace(
                go.Scatter(
                    x=df_grouped["date_time"],
                    y=df_grouped["avg_temp"],
                    mode="lines",
                    name="Original Data",
                    line={
                        "color": 'lightblue',
                        "width": 2
                    },
                )
            )

        else:
            smoothed_temp = smooth_out_data(
                df_grouped, "avg_temp", local_method, window_size=window_size, window_length=window_length,
                polyorder=polyorder
            )
            fig.add_trace(
                go.Scatter(
                    x=df_grouped["date_time"],
                    y=smoothed_temp,
                    mode="lines",
                    name="Smoothed Data",
                    line={
                        "color": 'red',
                        "width": 2
                    },
                )
            )

        fig.update_layout(
            title=f"Temperature Data for {selected_towns[idx]}",
            xaxis_title="Time",
            yaxis_title="Temperature",
            xaxis_rangeslider_visible=True,
            hovermode="x unified",
            height=600,
        )
        col1, col2 = tab.columns( [0.75, 0.25], border=True )
        with col1:
            st.plotly_chart( fig, use_container_width=True )

        with col2:

            grouping_by_text = ""
            if grouping_by == "Hour":
                grouping_by_text = "Hours"
            elif grouping_by == "Day":
                grouping_by_text = "Days"
            else:
                grouping_by_text = "Data points"

            st.info(
                f"""
                ### Summary
                - **Maximal Temperature**: :red[{df["avg_temp"].max():.2f}°C]
                - **Average Temperature**: :orange[{df["avg_temp"].mean():.2f}°C]
                - **Minimal Temperature**: :blue[{df["avg_temp"].min():.2f}°C]
                - **{grouping_by_text} displayed**: :green[{len( df_grouped["date_time"] )}]
                """
            )
