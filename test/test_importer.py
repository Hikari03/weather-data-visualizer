"""
Tests importer package functions
"""

import logging
import os
import sys

import pytest

from app.importer.constants import DOWNLOAD_PATH, CHMU_RBCM_TOWN_FILE_NAMES, CHMU_RBCM_ALL_TOWNS
from app.importer.file_downloader import __download_file, __check_offline_file, get_file_from_town
from app.importer.import_data_aeris import import_france
from app.importer.import_data_file import import_data_from_file
from app.utils import get_connection_headless

logging.basicConfig(
    force=True,
    level=logging.CRITICAL,  # Sets the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Specify the log message format
    datefmt="%Y-%m-%d %H:%M:%S",  # Optional: Specify how the timestamp should be formatted
    handlers=[
        logging.StreamHandler( sys.stdout ),  # Log to the console (default)
    ]
)


def test_file_exists_valid():
    # Test with a valid file path
    filepath = os.path.join( DOWNLOAD_PATH, "test_valid.download" )
    os.makedirs( DOWNLOAD_PATH, exist_ok=True )
    with open( filepath, "w" ) as f:
        f.write( "Test content" )

    assert __check_offline_file( filepath ) == True

    # Clean up the test file
    os.remove( filepath )


def test_file_not_exists():
    # Test with a non-existing file path
    filepath = os.path.join( DOWNLOAD_PATH, "test_invalid.download" )
    assert __check_offline_file( filepath ) == False

    # Clean up the test file if it exists
    if os.path.isfile( filepath ):
        os.remove( filepath )

# @generated "partially" gpt-4.1-nano
def test_download_valid_file():
    __download_file(
        "test_valid.download",
        "https://freetestdata.com/wp-content/uploads/2024/01/sample2zip.rar"
    )
    # Check if the file was downloaded successfully
    filepath = os.path.join( DOWNLOAD_PATH, "test_valid.download" )
    assert os.path.isfile( filepath )

    # Check sha256 hash of the file
    import hashlib
    sha256_hash = hashlib.sha256()
    with open( filepath, "rb" ) as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter( lambda: f.read( 4096 ), b"" ):
            sha256_hash.update( byte_block )

    expected_hash = "5619c609ddca16ecccb6f1d78487919e7f26acbbc887d50fe278a0c1d6402827"
    os.remove( filepath )
    assert sha256_hash.hexdigest() == expected_hash


def test_download_invalid_file():
    # Test with an invalid URL
    with pytest.raises( Exception ):
        __download_file( "test_invalid.download", "https://link.testfile.org/invalid" )

    # Check if the file was not downloaded
    file_exists = os.path.isfile( "test_invalid.download" )
    # Clean up the downloaded file if it exists
    if os.path.isfile( "test_invalid.download" ):
        os.remove( "test_invalid.download" )

    assert not file_exists


def test_get_file_from_town():
    # Test with a valid town name
    town = CHMU_RBCM_ALL_TOWNS[0]
    get_file_from_town( town )

    # Clean up the test file
    os.remove( os.path.join( DOWNLOAD_PATH, CHMU_RBCM_TOWN_FILE_NAMES[town] ) )

@pytest.mark.real_database_connection
def test_database_connection():
    conn = get_connection_headless()
    assert conn is not None

    # Check if the connection is valid
    cursor = conn.cursor()
    cursor.execute( "SELECT 1" )
    result = cursor.fetchone()
    assert result[0] == 1
    # Clean up the connection
    cursor.close()
    conn.close()

@pytest.mark.real_database_connection
def test_rbcm_import_individual():
    # Test with a valid town name
    from app.importer.import_data_rbcm import import_rbcm

    import_rbcm( "Brno-Tuřany" )


def test_aeris_get_urls_in_range():
    from app.importer.import_data_aeris import __get_france_catalogue_urls

    # Test with a valid year range
    year_range = (2020, 2021)
    urls = __get_france_catalogue_urls( year_range )
    assert len( urls ) == 2

    # Check the URLs
    assert (urls[0] ==
            "https://thredds-su.ipsl.fr/thredds/catalog/aeris_thredds/actrisfr_data/665029c8-82b8-4754-9ff4-d558e640b0ba/2020/catalog.xml")
    assert (urls[1] ==
            "https://thredds-su.ipsl.fr/thredds/catalog/aeris_thredds/actrisfr_data/665029c8-82b8-4754-9ff4-d558e640b0ba/2021/catalog.xml")

    # Test with an invalid year range
    year_range = (2025, 2023)
    with pytest.raises( ValueError ):
        __get_france_catalogue_urls( year_range )


@pytest.mark.filterwarnings( "ignore::RuntimeWarning" )
@pytest.mark.filterwarnings( "ignore::DeprecationWarning" )
@pytest.mark.real_database_connection
def test_aeris_import():
    # Test with a valid year range

    year_range = (1960, 1960)
    import_france( year_range, headless=True, sleep_time=(0.5, 0.5) )

    # Check if the data was imported successfully
    conn = get_connection_headless()
    cursor = conn.cursor()
    cursor.execute( "SELECT COUNT(*) FROM \"france-Nice\" WHERE \"date_time\" BETWEEN '1960-01-01' AND '1960-12-31'" )
    count = cursor.fetchone()[0]
    assert count > 0

    # Clean up the connection
    cursor.close()
    conn.close()


@pytest.mark.real_database_connection
def test_file_import_valid():
    with open( "test_valid.import", "w" ) as f:
        f.write( "2024-05-02 22:22;5.5°C" )

    import_data_from_file( "test_valid.import", "test_table", headless=True )

    # Check if the data was imported successfully
    conn = get_connection_headless()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT avg_temp FROM \"test_table\" WHERE \"date_time\" BETWEEN '2024-05-02 22:22:00' AND '2024-05-02 22:22:00'"
    )
    temp = cursor.fetchone()[0]
    # Clean up
    cursor.execute( "DROP TABLE IF EXISTS \"test_table\"" )
    cursor.close()
    conn.close()
    os.remove( "test_valid.import" )
    assert temp == 5.5


def test_file_import_invalid_date_time():
    with open( "test_invalid.import", "w" ) as f:
        f.write( "2024-13-02 22:22;5.5°C" )

    with pytest.raises( ValueError ):
        import_data_from_file( "test_invalid.import", "test_table", headless=True )

    # Clean up
    os.remove( "test_invalid.import" )


def test_file_import_invalid_file():
    with open( "test_invalid_file.import", "w" ) as f:
        f.write( "2024-05-02 22:22;5.5" )

    with pytest.raises( ValueError ):
        import_data_from_file( "test_invalid_file.import", "test_table", headless=True )

    # Clean up
    os.remove( "test_invalid_file.import" )
