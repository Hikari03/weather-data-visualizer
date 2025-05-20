"""
Import data from a file in format YYYY-MM-DD hh:mm;num°C.
"""

import pandas as pd
import streamlit as st

from app.utils import __create_town_table_if_not_exists, get_connection_headless


def import_data_from_file( file, table_name: str, headless: bool = False ):
    """
    Import data from a file in format YYYY-MM-DD hh:mm;num°C.
    :param file: file to import.
    :param table_name: name of the table to import data into.
    :param headless: if True, don't use streamlit connection.
    """

    df = pd.read_csv( file, sep=";", header=None )
    df.columns = ["date_time", "avg_temp"]
    df["date_time"] = pd.to_datetime( df["date_time"], format="%Y-%m-%d %H:%M" )
    try:
        df["avg_temp"] = df["avg_temp"].str.replace( ",", "." )
    except AttributeError as e:
        raise ValueError( "The file is not in the correct format. Expected format: YYYY-MM-DD hh:mm;num°C" ) from e

    df["avg_temp"] = df["avg_temp"].str[:-2]
    df["avg_temp"] = df["avg_temp"].astype( float )

    # Check if the file has exactly two columns
    if df.shape[1] != 2:
        raise ValueError( "The file should contain exactly two columns: date_time;avg_temp" )

    df = df.dropna()

    __create_town_table_if_not_exists( table_name )

    if not headless:
        len_df = len( df )
        fraction = 1 / len_df

        progress_bar = st.progress( 0 )
    line = 0

    conn = get_connection_headless()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        line += 1
        date_time = row["date_time"]
        avg_temp = row["avg_temp"]

        if not headless:
            progress_bar.progress( fraction * line, text=f"Importing {table_name} data... line {line} of {len_df}" )

        insert_query = f"""
                INSERT INTO \"{table_name}\" (date_time, avg_temp)
                VALUES ('{date_time}', {avg_temp})
                ON CONFLICT (date_time) DO UPDATE SET
                    avg_temp = EXCLUDED.avg_temp;
            """
        cursor.execute( insert_query )

    conn.commit()
    cursor.close()
    conn.close()
