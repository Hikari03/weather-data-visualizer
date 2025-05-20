"""
For downloading files and checking if we already have them on disk
"""

import logging
import os

import wget

from app.importer.constants import DOWNLOAD_PATH, CHMU_RBCM_TOWN_FILE_NAMES, CHMU_RBCM_TOWN_URLS

logger = logging.getLogger( "streamlit_app" )


def __download_file( filename: str, url: str ):
    """
    Download file from url.
    :param filename: how the file should be named.
    :param url: url of the file.
    """
    filepath = str( os.path.join( DOWNLOAD_PATH, filename ) )
    os.makedirs( DOWNLOAD_PATH, exist_ok=True )

    logger.info( "Downloading %s from %s to %s", filename, url, filepath )

    wget.download( url, out=filepath, bar=None )


def __check_offline_file( filepath: str ) -> bool:
    """
    Check if we already have the file on disk in the dedicated folder.
    :param filepath: name of the file.
    :return: if the file is already downloaded.
    """
    return os.path.isfile( filepath ) and os.path.getsize( filepath ) > 0


def get_file_from_town( town: str ) -> str:
    """
    Get a file path for town.
    :param town: name of the town.
    :return: file path.

    """
    os.makedirs( DOWNLOAD_PATH, exist_ok=True )

    filepath = str( os.path.join( DOWNLOAD_PATH, CHMU_RBCM_TOWN_FILE_NAMES[town] ) )

    if __check_offline_file( filepath ):
        return filepath

    __download_file( CHMU_RBCM_TOWN_FILE_NAMES[town], CHMU_RBCM_TOWN_URLS[town] )

    return filepath
