"""
This act as a main entry point for the Streamlit application.
It shows data about the application and provides a link to the GitHub repository.
"""

import streamlit as st

from app.utils import get_connection, insert_logged_in_user, create_user_table_if_not_exists

st.set_page_config( layout="wide" )
st.title( "Welcome to the Weather Data Visualizer!" )

if not st.user.is_logged_in:
    logged_in_text = "You are not logged in. To access import, please log in under the admin email."
else:
    logged_in_text = f"You are logged in as :violet[{st.user.to_dict()['name']}]."
    create_user_table_if_not_exists()
    insert_logged_in_user()

st.markdown(
    """
    
    ## Stats
    
    :rainbow-background[{}]
    
    :violet-badge[You currently have :rainbow[{}] stations in the database,
     from which :rainbow[{}] are from the **Czech CHMU** database,
      :rainbow[{}] are from the **France Aeris** database
      and :rainbow[{}] are from your own **MQTT** sensors.]
    
    """.format(
        logged_in_text,
        get_connection().query(
            """SELECT COUNT(*) AS total_tables
               FROM information_schema.tables
               where table_schema = 'public';"""
        ).iloc[0, 0],
        get_connection().query(
            """SELECT COUNT(*) AS total_tables
               FROM information_schema.tables
               where table_schema = 'public'
                 and table_name like 'czechia-%';"""
        ).iloc[0, 0],
        get_connection().query(
            """SELECT COUNT(*) AS total_tables
               FROM information_schema.tables
               where table_schema = 'public'
                 and table_name like 'france-%';"""
        ).iloc[0, 0],
        get_connection().query(
            """SELECT COUNT(*) AS total_tables
               FROM information_schema.tables
               where table_schema = 'public'
                 and table_name like 'mqtt-%';"""
        ).iloc[0, 0],
    )
)

st.markdown(
    """
    ---
    
    ### Data Sources
    
    ##### Built-in Automatic Import Datasets
    - **[Czech CHMU database](https://www.chmi.cz/historicka-data/pocasi/denni-data/data-ze-stanic-site-RBCN)**:  
        This dataset contains weather data from 11 towns in the Czech Republic.
      
    - **[France Aeris database](https://www.aeris-data.fr/en/welcome-2/)**:  
        This dataset contains weather data from ~1500 stations in France.  
        Unfortunately, the data is not as clean as the Czech one, but it is still usable.
        
    ##### Built-in Manual Import Datasets
    - You can also upload your own datasets in file with format `YYYY-MM-DD hh:mm;num°C`, where in `num` the decimal is `.` separated.
    
    ##### MQTT Datasets
    - You can also use MQTT to import data on the fly from your own sensors.
    - To do this, you need to define the configuration in `app/mosquito_handler/config.py` and run the `run.sh` script.
    - Received messages have to be in format `YYYY-MM-DD hh:mm;num°C`, where the decimal in `num` is `.` separated.
    
    
    ---
    
    #### Administration
    - The application is designed to be used by everyone, but only the administrator can import data.
    - To access the administration page, you need to log in with the google account email defined in `secrets.toml` file.
    
    #### Source Code
    
    You can find the source code on [GitHub](https://github.com/Hikari03/weather-data-visualizer).
    """
)
