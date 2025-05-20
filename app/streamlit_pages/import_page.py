"""
This is a Streamlit page for importing weather data from the CHMU RBCM database.
"""

import streamlit as st

from app.importer import import_france, import_rbcm_all, import_data_from_file
from app.importer.constants import FRANCE_YEAR_RANGE

st.set_page_config( layout="wide" )
st.title( "Weather Data Importer" )
with st.expander( "Import Czechia", icon="🇨🇿" ):
    st.markdown(
        """
        This will import all data from the CHMU RBCM database for available towns in Czechia.  
        Source: https://www.chmi.cz/historicka-data/pocasi/denni-data/data-ze-stanic-site-RBCN
        """
    )
    st.warning(
        """
        This service is discontinued from the side of CHMI. If you want the data, follow instructions in README.md.
        """,
        icon=":material/priority_high:",
    )
    if st.button( "Start Import", key="start-import-czechia" ):
        import_rbcm_all( want_progress_bar=True )
        st.balloons()

        st.success( "Data import completed!" )

with st.expander( "Import France", icon="🇫🇷" ):
    st.markdown(
        """This will import all data from the France database for all available towns.  
        Source: https://thredds-su.ipsl.fr/thredds/catalog/aeris_thredds/actrisfr_data/665029c8-82b8-4754-9ff4-d558e640b0ba/catalog.html"""
    )

    france_year_range = st.slider(
        "Year Range", min_value=FRANCE_YEAR_RANGE["start"], max_value=FRANCE_YEAR_RANGE["end"],
        value=(FRANCE_YEAR_RANGE["start"], FRANCE_YEAR_RANGE["end"]), )

    if st.button( "Start Import", key="start-import-france" ):
        with st.spinner( "Importing data...", show_time=True ):
            import_france( france_year_range, True )
        st.success( "Data import completed!" )

with st.expander( "Import File", icon=":material/upload:" ):
    st.markdown(
        "##### The file has to be in format `YYYY-MM-DD hh:mm;num°C`, where the decimal in `num` is `.` separated"
    )
    table_name = st.text_input( "Input database table name, where the data will be imported" )
    st.warning(
        "You should know what you are doing. If you input wrong table name, you may not be able to access the data."
    )
    st.info(
        "The table name should be in format `czechia-<town>`, `france-<town>` or `mqtt-<town>`, where `<town>` is the name of the town.",
        icon=":material/priority_high:",
    )

    if st.toggle( "Are you comfortable with this?" ):
        uploaded_file = st.file_uploader( "Upload TXT/CSV file" )

        if st.button( "Import", type="primary" ):
            if uploaded_file and table_name:
                with st.spinner( "Importing data...", show_time=True ):
                    import_data_from_file( uploaded_file, table_name )

                st.success( "Data import completed!" )
