"""
This module imports data from the CHMU RBCM (Regional Base Climate Model) database.
"""

from app.importer.constants import CHMU_RBCM_ALL_TOWNS, CHMU_RBCM_COLUMN_NAMES
from app.importer.import_data_aeris import import_france
from app.importer.import_data_file import import_data_from_file
from app.importer.import_data_rbcm import import_rbcm, import_rbcm_all
