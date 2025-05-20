"""
This page shows the precipitation and snow height data for the selected towns in bar charts.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.utils import (
    display_date_slider
)
from app.utils import (
    get_connection, get_dataframe_for_towns_and_range, get_cropped_and_uncropped_selected_towns_from_user
)

st.set_page_config( layout="wide" )


def precipitation_snow():
    """
    This function displays the precipitation and snow height data for the selected towns in bar charts.
    """
    st.title( "Precipitation and Snow Height" )
    st.write( "Select towns to visualize precipitation and snow height data for:" )

    selected_towns, selected_towns_cropped = get_cropped_and_uncropped_selected_towns_from_user()
    date_range = display_date_slider()
    st.sidebar.divider()

    if len( selected_towns ) > 0:
        conn = get_connection()
        tabs = st.tabs( selected_towns_cropped )
        for idx, tab in enumerate( tabs ):
            with tab:
                df = get_dataframe_for_towns_and_range( selected_towns[idx], date_range, conn )

                fig = prepare_graph( df, selected_towns_cropped[idx] )

                st.plotly_chart( fig, use_container_width=True )


@st.cache_data( show_spinner=True )
def prepare_graph( df: pd.DataFrame, town: str ) -> go.Figure:
    """
    Prepare the graph for the precipitation and snow height data.
    :param df: DataFrame containing the data.
    :param town: Name of the town.
    :return: Graph to be displayed.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["date_time"],
            y=df["precipitation"],
            name="Precipitation",
            marker_color='#1447E6',
        )
    )
    fig.add_trace(
        go.Line(
            x=df["date_time"],
            y=df["snow_height"],
            name="Snow Height",
            marker_color='#00D3F2',
        )
    )
    fig.update_layout(
        title=f"Precipitation and Snow Height in {town}",
        xaxis_title="Date",
        yaxis_title="mm/day (rain) or cm (snow)",
        xaxis_tickformat="%Y-%m-%d",
        barmode='group',
        height=600,
        xaxis_rangeslider_visible=True,
        hovermode="x unified"
    )
    return fig


precipitation_snow()
