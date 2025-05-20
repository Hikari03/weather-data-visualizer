"""
Visualizes temperature data for selected towns
"""
# @generated "partial" github-copilot-gpt-4o

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.utils import (
    smooth_out_data, render_smooth_func_ui_and_get, group_by_day,
    display_date_slider, get_connection,
    render_stats_day, get_dataframe_for_towns_and_range, get_cropped_and_uncropped_selected_towns_from_user
)

st.set_page_config( layout="wide" )


# disabling pylint's "too-many-locals" because this function just needs these variables and making class for them would be less readable
def town_visualize():  # pylint: disable=too-many-locals
    """
    Visualizes temperature data for selected towns.
    """
    st.title( "Visualize Towns" )
    st.write( "Select towns to visualize data for:" )

    # pylint: disable=R0801
    # We need all these variables and making a class for them would be less readable
    selected_towns, selected_towns_cropped = get_cropped_and_uncropped_selected_towns_from_user()

    date_range = display_date_slider()

    st.sidebar.divider()

    method, window_size, window_length, polyorder = render_smooth_func_ui_and_get()

    smoothing = method != "None"  # are we smoothing the data?
    # pylint: enable=R0801

    if len( selected_towns ) > 0:
        conn = get_connection()
        tabs = st.tabs( selected_towns_cropped )
        for idx, tab in enumerate( tabs ):

            local_method = method

            df = get_dataframe_for_towns_and_range( selected_towns[idx], date_range, conn )

            fig = prepare_graph(
                df, date_range, smoothing, method, window_size, window_length, local_method, polyorder
            )

            col1, col2 = tab.columns( [0.75, 0.25], border=True )
            with col1:
                st.plotly_chart( fig, use_container_width=True, key=f"plot_{selected_towns_cropped[idx]}" )

            with col2:
                render_stats_day( df )
            tab.divider()

            if tab.button(
                    "Visualize Global Warming Over the Years", key=f"stacked_{selected_towns_cropped[idx]}",
                    icon=":material/thermometer_gain:"
            ):
                fig = generate_global_warming_graph( conn, idx, selected_towns )

                tab.plotly_chart( fig, use_container_width=True )


# disable pylint's "too-many-arguments" because this function just needs these arguments and making class for them would be less readable
@st.cache_data( show_spinner=True )
def prepare_graph(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        df: pd.DataFrame, date_range: tuple, smoothing: bool, method: str, window_size: int, window_length: int,
        local_method: str, polyorder: int
) -> go.Figure:
    """
    Prepares the graph for the given data.
    :param df: DataFrame containing the data to plot.
    :param date_range: Tuple containing the start and end date for the data.
    :param smoothing: Boolean indicating whether to smooth the data.
    :param method: Smoothing method to use.
    :param window_size: Size of the smoothing window.
    :param window_length: Length of the smoothing window.
    :param local_method: Local method to use for smoothing.
    :param polyorder: Polynomial order for smoothing.
    """
    if df.empty:
        st.warning( "No data found for the selected time range." )
        st.stop()

    fig = go.Figure()
    if not smoothing:
        # pylint: disable=R0801
        # This is because there really is no need to create a function just for this when this code is only on two places
        fig.add_trace(
            go.Scatter(
                x=df["date_time"],
                y=df["avg_temp"],
                mode="lines",
                name="Original Data",
                line={
                    "color": 'lightblue',
                    "width": 2
                },
            )
        )
        # pylint: enable=R0801
    else:
        smoothed_avg = smooth_out_data(
            df, "avg_temp", method, window_size=window_size, window_length=window_length, polyorder=polyorder
        )
        smoothed_min = smooth_out_data(
            df, "min_temp", method, window_size=window_size, window_length=window_length, polyorder=polyorder
        )
        smoothed_max = smooth_out_data(
            df, "max_temp", method, window_size=window_size, window_length=window_length, polyorder=polyorder
        )

        fig.add_trace(
            go.Scatter(
                x=df["date_time"],
                y=smoothed_max,
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
                x=df["date_time"],
                y=smoothed_avg,
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
                x=df["date_time"],
                y=smoothed_min,
                mode="lines",
                name="Minimal Temperature",
                line={
                    "color": 'yellow',
                    "width": 3
                },
            )
        )

    if local_method == "None":
        local_method = "- displaying raw data"
    else:
        local_method = f"- displaying smoothed data ({local_method})"

    fig.update_layout(
        title=f"Data in range {date_range[0].strftime( "%Y-%m-%d" )} to {date_range[1].strftime( "%Y-%m-%d" )} {local_method}",
        xaxis_title="Date",
        yaxis_title="Temperature (°C)",
        xaxis_rangeslider_visible=True,
        hovermode="x unified"  # Shows info for all traces at the given x position
    )
    return fig


def generate_global_warming_graph( conn, idx, selected_towns ) -> go.Figure:
    """
    Generates a global warming graph for the given town.
    :param conn: Database connection.
    :param idx: Index of the selected town.
    :param selected_towns: List of selected towns.
    """
    window_size_years_stacked = 25
    query = ""

    # plot all years on top of each other
    if selected_towns[idx].startswith( "france-" ):
        query = f"""SELECT * FROM \"{selected_towns[idx]}\"
                                WHERE date_time >= \'1993-01-01\' ORDER BY date_time;"""
    else:
        query = f"""SELECT * FROM \"{selected_towns[idx]}\" ORDER BY date_time;"""

    df = conn.query( query, ttl=5 * 60 )

    df["date_time"] = pd.to_datetime( df["date_time"] )

    # if data is from France, convert all data from one day as one datapoint
    if selected_towns[idx].startswith( "france-" ):
        # Convert to datetime if not already
        df = group_by_day( df )

    # Convert day to datetime and extract useful parts
    df["year"] = df["date_time"].dt.year
    df["dayofyear"] = df["date_time"].dt.dayofyear  # will be our x-axis

    historic = df[df["year"] < 2000].copy()
    historic_grouped = historic.groupby( "dayofyear", as_index=False )["avg_temp"].mean()

    historic_grouped["smoothed_avg"] = smooth_out_data(
        historic_grouped, "avg_temp", "Moving Average", window_size=window_size_years_stacked
    )

    recent = df[df["year"] >= 2000].copy()
    unique_years = sorted( recent["year"].unique() )

    # separate all years
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=historic_grouped["dayofyear"],
            y=historic_grouped["smoothed_avg"],
            name="Avg (Pre-2000)",
            mode="lines",
            line={
                "width": 8,
                "color": 'red',
                "dash": 'dash'
            },
        )
    )

    for _, year in enumerate( unique_years ):
        year_df = recent[recent["year"] == year].copy()
        # Sort by dayofyear (important for producing a line plot)
        year_df.sort_values( "dayofyear", inplace=True )
        smoothed_avg = smooth_out_data(
            year_df, "avg_temp", "Moving Average", window_size=window_size_years_stacked
        )
        fig.add_trace(
            go.Scatter(
                x=year_df["dayofyear"],
                y=smoothed_avg,
                name=str( year ),
                mode="lines",
                opacity=0.5,
            )
        )

    # plot all years on top of each other
    fig.update_layout(
        title="Historic (averaged) data vs. recent years",
        xaxis_title="Day of Year",
        yaxis_title="Average Temperature",
        height=800,
        legend_title="Year",
        xaxis_rangeslider_visible=True,
        hovermode="x unified"
    )

    return fig


town_visualize()
