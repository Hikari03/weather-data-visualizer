"""
Stores constants used in the importer package
"""
import os
import time

__url_template = "https://www.chmi.cz/files/portal/docs/meteo/ok/denni_data/Denni_data_ze_stanic/files/"

CHMU_RBCM_ALL_TOWNS = [
    'Liberec',
    'Milešovka',
    'Praha-Ruzyně',
    'Praha-Libuš',
    'Přimda',
    'Kocelovice',
    'Košetice',
    'Přibyslav',
    'Brno-Tuřany',
    'Mošnov',
    'Lysá-Hora'
]

CHMU_RBCM_TOWN_FILE_NAMES = {
    CHMU_RBCM_ALL_TOWNS[0]: "U2LIBC01.xlsx",
    CHMU_RBCM_ALL_TOWNS[1]: "U1MILE01.xlsx",
    CHMU_RBCM_ALL_TOWNS[2]: "P1PRUZ01.xlsx",
    CHMU_RBCM_ALL_TOWNS[3]: "P1PLIB01.xlsx",
    CHMU_RBCM_ALL_TOWNS[4]: "L2PRIM01.xlsx",
    CHMU_RBCM_ALL_TOWNS[5]: "C1KOCE01.xlsx",
    CHMU_RBCM_ALL_TOWNS[6]: "P3KOSE01.xlsx",
    CHMU_RBCM_ALL_TOWNS[7]: "P3PRIB01.xlsx",
    CHMU_RBCM_ALL_TOWNS[8]: "B2BTUR01.xlsx",
    CHMU_RBCM_ALL_TOWNS[9]: "O1MOSN01.xlsx",
    CHMU_RBCM_ALL_TOWNS[10]: "O1LYSA01.xlsx"
}

FRANCE_YEAR_RANGE = {
    "start": 1845,
    "end": time.localtime().tm_year
}

CHMU_RBCM_TOWN_URLS = {town: __url_template + CHMU_RBCM_TOWN_FILE_NAMES[town] for town in CHMU_RBCM_ALL_TOWNS}

CHMU_RBCM_COLUMN_NAMES = ["date_time", "avg_temp", "max_temp", "min_temp", "precipitation", "snow_height"]

DOWNLOAD_PATH = os.path.join( "data", "downloaded" )
