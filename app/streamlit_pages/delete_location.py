"""
This page is used to delete data from the database.
"""
import streamlit as st

from app.utils import (
    get_database_town_names, sort_cached_towns,
    display_multiselect_for_czechia_and_france_towns, get_connection_headless
)

st.set_page_config( layout="wide" )
st.title( "Delete Data" )
st.write( "Select stations to delete data for:" )

towns = get_database_town_names()
towns = sort_cached_towns( towns )
selected_towns, selected_towns_cropped = display_multiselect_for_czechia_and_france_towns( towns )
st.sidebar.divider()

with st.expander( "Delete data for whole dataset" ):
    st.markdown(
        "This will delete all data for the selected dataset. This action is irreversible."
    )
    delete_czechia = st.checkbox( "Delete Czechia" )
    delete_france = st.checkbox( "Delete France" )
    delete_mqtt = st.checkbox( "Delete MQTT" )

    if delete_czechia:
        selected_towns += [town for town in towns if town.startswith( "czechia-" )]
    if delete_france:
        selected_towns += [town for town in towns if town.startswith( "france-" )]
    if delete_mqtt:
        selected_towns += [town for town in towns if town.startswith( "mqtt-" )]

if len( selected_towns ) == 0:
    st.warning( "Please select at least one town to delete data." )
    st.stop()
conn = get_connection_headless()
cursor = conn.cursor()

confirm = st.checkbox(
    "I understand that this action is irreversible and will delete all data for the selected stations."
)

if st.button( "Delete Data", type="primary" ) and confirm:
    for town in selected_towns:
        query = f"""DROP TABLE IF EXISTS \"{town}\";"""
        cursor.execute( query )
        st.success( f"Deleted data for {town}." )

conn.commit()
cursor.close()
conn.close()
