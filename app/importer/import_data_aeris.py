"""
Responsible for importing data from the Aeris database.
"""

import logging
from multiprocessing import Process
from time import sleep

import numpy as np
import pandas as pd
import streamlit as st
from pandas import Series
from requests.exceptions import HTTPError
from siphon.catalog import TDSCatalog

from app.importer.import_data_rbcm import __create_town_table_if_not_exists
from app.utils import get_connection_headless

logger = logging.getLogger( "streamlit_app" )


def __get_france_catalogue_urls( year_range: tuple[int, int] ) -> list[str]:
    if year_range[0] > year_range[1]:
        logger.error( "Year range is invalid." )
        raise ValueError( "Year range is invalid." )

    cat_urls = []
    for year in range( year_range[0], year_range[1] + 1 ):
        url = f"https://thredds-su.ipsl.fr/thredds/catalog/aeris_thredds/actrisfr_data/665029c8-82b8-4754-9ff4-d558e640b0ba/{year}/catalog.xml"
        cat_urls += [url]
    return cat_urls


def __get_france_catalogues( year_range: tuple[int, int], headless: bool = False ) -> list[TDSCatalog]:
    """
    Get the catalogue from the France data source
    :param year_range: year range to get
    :param headless: if True, run the import without streamlit dependencies
    :return: catalogue
    """

    cat_urls = __get_france_catalogue_urls( year_range )

    catalogues = []
    for url in cat_urls:
        try:
            catalogues.append( TDSCatalog( url ) )
        except HTTPError as e:
            logger.error( "Error fetching catalogue from %s: %s", url, e )
            if not headless:
                st.error(
                    f"Error fetching catalogue from {url}:\n some years dont have catalogues in range or the site is down."
                )
            else:
                raise e

    if not catalogues:
        logger.error( "No catalogues found." )
        return []

    return catalogues


def to_slice( l: int ) -> slice:
    """
    Convert an integer to a slice.
    :param l: Integer to convert.
    :return: Slice.
    """
    return slice( None, l, None )


def __extract_france_time( data, year ) -> Series:
    """
    Extract the time from the data.
    :param data: Data to extract.
    :param year: Year of the data.
    :return: Time.
    """

    shape = np.array( data.shape )

    indices = [to_slice( s ) for s in shape]

    disp_var = data[indices]
    x = np.squeeze( np.array( [range( len( np.squeeze( disp_var[:] ) ) )] ) )

    # x is time in seconds in a given year
    # convert it to date
    x = pd.to_datetime( x, unit='h', origin=pd.Timestamp( year=year, month=1, day=1, hour=0, minute=0, second=0 ) )

    return x


def __extract_france_values( dataset, what: str, is_temp: bool = True ) -> Series:
    """
    Extract the values from the data.
    :param dataset: Data to extract.
    :param what: What to extract.
    :return: values
    """

    data = dataset.variables[what]

    shape = np.array( data.shape )
    indices = [to_slice( s ) for s in shape]

    disp_var = data[indices]

    # y is the temperature in Kelvin
    # convert it to Celsius
    if is_temp:
        y = np.squeeze( np.array( [disp_var[:]] ) ) - 273.15

    else:
        y = np.squeeze( np.array( [disp_var[:]] ) )
        y = np.where( y < 0, 0, y )
    y = pd.Series( y )

    if what == "snow_height":
        y = y * 100  # Convert to cm

    return y


def __insert_france_data(
        town: str, time: Series, data: tuple[Series, Series, Series, Series, Series]
):
    """
    Insert data into the database.
    :param town: Name of the town.
    :param time: Time of the data.
    :param data: Data to insert (avg_temp, max_temp, min_temp, precipitation, snow_height).
    """

    conn = get_connection_headless()
    cursor = conn.cursor()

    logger.info( "import_data: Inserting data for %s", town )

    # Create the table if it does not exist
    __create_town_table_if_not_exists( "france-" + town )

    for i, time_ in enumerate( time ):
        insert_query = f"""
                INSERT INTO \"france-{town}\" (date_time, avg_temp, max_temp, min_temp, precipitation, snow_height)
                VALUES (
                    '{time_}',
                    {"null" if pd.isna( data[0][i] ) else data[0][i]},
                    {"null" if pd.isna( data[1][i] ) else data[1][i]},
                    {"null" if pd.isna( data[2][i] ) else data[2][i]},
                    {"null" if pd.isna( data[3][i] ) else data[3][i]},
                    {"null" if pd.isna( data[4][i] ) else data[4][i]}
                )
                ON CONFLICT (date_time) DO UPDATE SET
                    avg_temp = EXCLUDED.avg_temp,
                    max_temp = EXCLUDED.max_temp,
                    min_temp = EXCLUDED.min_temp,
                    precipitation = EXCLUDED.precipitation,
                    snow_height = EXCLUDED.snow_height;
            """

        cursor.execute( insert_query )
    conn.commit()
    cursor.close()
    conn.close()

    logger.info( "import_data: Data for %s inserted", town )


def __import_individual_france_catalogue(
        catalogue: TDSCatalog, want_progress_bar: bool = False, sleep_time: float = 1
):
    """
    Import data from a single catalogue.
    :param catalogue: Catalogue to import.
    :param want_progress_bar: If True, show a progress bar in streamlit.
    """
    datasets = catalogue.datasets
    data_len = len( datasets.items() )
    logger.info( "import_data: Found %s datasets", data_len )
    current_dataset = 0

    if data_len == 0:
        logger.error( "No datasets found in the catalogue." )
        return

    fraction = 1 / data_len
    if want_progress_bar:
        progress_bar = st.progress( 0 )

    for dataset_name, dataset in datasets.items():
        # Get the dataset
        dataset = dataset.remote_access()
        current_dataset += 1

        year = int( dataset_name.split( "_" )[-1].split( "." )[0] )

        # Get the time
        try:
            time = __extract_france_time( dataset.variables["ta"], year )
        except KeyError:
            logger.error( "KeyError: 'ta' variable not found in dataset %s", dataset_name )
            continue

        data = (
            __extract_france_values( dataset, "ta" ),
            __extract_france_values( dataset, "ta_max" ),
            __extract_france_values( dataset, "ta_min" ),
            __extract_france_values( dataset, "cumul_precip", is_temp=False ),
            __extract_france_values( dataset, "snow_height", is_temp=False )
        )

        town = dataset_name.split( "_" )[1].lower().capitalize()

        if current_dataset != data_len:
            Process(
                target=__insert_france_data,
                args=(town, time, data),
            ).start()
        else:
            __insert_france_data( town, time, data )

        if want_progress_bar:
            progress_bar.progress( fraction * current_dataset, text=f"{year}: Importing {town} data..." )
        sleep( sleep_time )  # Sleep for 2 seconds to avoid overloading the server

    if want_progress_bar:
        progress_bar.empty()


def import_france(
        year_range: tuple[int, int], want_progress_bar: bool = False, sleep_time: tuple[float, float] = (3, 1),
        headless: bool = False
):
    """
    Import data from France.
    :param year_range: year range to import.
    :param want_progress_bar: if True, show a streamlit progress bar.
    :param sleep_time: time to sleep between imports (default is 5 seconds for catalogue and 2 seconds for datasets).
    :param headless: if True, run the import without streamlit dependencies.

    """

    catalogues = __get_france_catalogues( year_range, headless )

    for cat in catalogues:
        __import_individual_france_catalogue( cat, want_progress_bar, sleep_time[1] )
        sleep( sleep_time[0] )  # Sleep for 5 seconds to avoid overloading the server
