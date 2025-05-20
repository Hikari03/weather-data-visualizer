"""
Deals with importing data from the CHMU RBCM (Czech Hydrometeorological Institute - Regional Base Climate Model).
"""

import calendar
import logging
import os.path
from multiprocessing import Process
from typing import Any

import pandas as pd
import streamlit as st

from app.importer.constants import (
    CHMU_RBCM_ALL_TOWNS, DOWNLOAD_PATH, CHMU_RBCM_TOWN_FILE_NAMES,
)
from app.importer.file_downloader import get_file_from_town
from app.utils import get_connection_headless, __create_town_table_if_not_exists

# Set up logging
logger = logging.getLogger( "streamlit_app" )


# @generated "partial" github-copilot-gpt-4o
def __insert_rcbm_data_temp_loop(
        df: dict[Any, pd.DataFrame], measure_mapping: dict, town: str
):
    conn = get_connection_headless()
    cursor = conn.cursor()

    for sheet_name, data in df.items():
        if data.empty:
            continue

        if sheet_name not in measure_mapping:
            logger.info( "import_info: Sheet '%s' does not have a defined mapping, skipping.", sheet_name )
            continue

        for _, row in data.iterrows():
            year = row["rok"]
            month = row["měsíc"]

            last_day = calendar.monthrange( int( year ), int( month ) )[1]

            for day in range( 2, last_day + 1 ):
                measurement = row.iloc[day]
                if pd.notna( measurement ):
                    date_str = f"{int( year )}-{int( month ):02d}-{day:02d} 00:00:00"

                    # Use INSERT...ON CONFLICT DO UPDATE so that if a row exists for that day,
                    # we update only the appropriate measurement field.
                    cursor.execute(
                        f"""
                        INSERT INTO \"czechia-{town}\" (date_time, {measure_mapping[sheet_name]})
                        VALUES ('{date_str}', {measurement})
                        ON CONFLICT (date_time) DO UPDATE SET
                            {measure_mapping[sheet_name]} = EXCLUDED.{measure_mapping[sheet_name]};
                        """
                    )

    conn.commit()
    cursor.close()
    conn.close()


# @generated "partial" github-copilot-gpt-4o
def __insert_rcbm_data_temp( town: str ):
    """
    Insert data into the database with the average temperature.
    Format of the data is:

    | rok | měsíc | 1 | 2 | 3 | ... | 31 |
    data

    :param town: Name of the town
    """

    measure_mapping = {
        "teplota průměrná": "avg_temp",
        "teplota maximální": "max_temp",
        "teplota minimální": "min_temp",
        "úhrn srážek": "precipitation",
        "celková výška sněhu": "snow_height",
    }

    # Read the data from the file
    filepath = os.path.join( DOWNLOAD_PATH, CHMU_RBCM_TOWN_FILE_NAMES[town] )
    logger.info( "import_data: Reading data from %s", filepath )
    if not os.path.isfile( filepath ):
        logger.error( "import_data: File %s not found", filepath )
        return
    data = pd.read_excel( filepath, sheet_name=None, skiprows=3 )

    if not data:
        return

    __insert_rcbm_data_temp_loop( data, measure_mapping, town )


def import_rbcm( town: str ):
    """
    Import data from the CHMU RBCM
    :param town: name of the town or "all"
    """

    if town not in CHMU_RBCM_ALL_TOWNS and town != "all":
        logger.error( "import_data: Town %s not found in the list of towns", town )
        return

    if town == "all":
        for town_ in CHMU_RBCM_ALL_TOWNS:
            Process( target=import_rbcm, args=(town_,) ).start()
            if town_ == CHMU_RBCM_ALL_TOWNS[-1]:
                town = town_
                break

    filepath = get_file_from_town( town )

    # Create the table if it does not exist
    __create_town_table_if_not_exists( "czechia-" + town )

    # Insert the data into the database
    __insert_rcbm_data_temp( town )
    logger.info( "import_data: Data from %s imported into %s table", filepath, town )


def import_rbcm_all( want_progress_bar: bool = False ):
    """
    Import data from all towns
    """

    if want_progress_bar:
        progress_bar = st.progress( 0 )
        fraction = 1 / len( CHMU_RBCM_ALL_TOWNS )
        for idx, town in enumerate( CHMU_RBCM_ALL_TOWNS ):
            progress_bar.progress( fraction * (idx + 1), text=f"Importing {town} data..." )
            import_rbcm( town )
    else:
        for town in CHMU_RBCM_ALL_TOWNS:
            import_rbcm( town )
