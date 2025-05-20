"""
Tests utils.py functions
"""

from unittest.mock import patch

import numpy as np
import pandas as pd

from app.utils import get_database_town_names
from app.utils import smooth_out_data


# @generated "all" gpt-4.1-nano
def generate_sample_data():
    np.random.seed( 0 )
    data = np.linspace( 0, 10, 100 ) + np.random.normal( 0, 1, 100 )
    df = pd.DataFrame( {'Y': data} )
    return df


# @generated "all" gpt-4.1-nano
def test_smooth_out_data_moving_average():
    df = generate_sample_data()
    smoothed = smooth_out_data( df, 'Y', method='Moving Average', window_size=5 )
    # Should return a pandas Series of the same length.
    assert isinstance( smoothed, pd.Series )
    assert len( smoothed ) == len( df )
    # Moving average smooths data: mean of a window
    assert not smoothed.isnull().all()
    assert not np.allclose( smoothed, df['Y'] )


# @generated "all" gpt-4.1-nano
def test_smooth_out_data_savgol_filter():
    df = generate_sample_data()
    smoothed = smooth_out_data( df, 'Y', method='Savitzky-Golay', window_length=7, polyorder=2 )
    # Should return a numpy array
    assert isinstance( smoothed, np.ndarray )
    assert len( smoothed ) == len( df )
    # Check that smoothed data is not identical to the original (smoothing effect)
    assert not np.allclose( smoothed, df['Y'] )


# @generated "all" gpt-4.1-nano
def test_smooth_out_data_missing_params():
    df = generate_sample_data()
    # Missing window_size for Moving Average
    result = smooth_out_data( df, 'Y', method='Moving Average' )
    assert result is None  # or whatever your function returns when params missing

    # Missing window_length or polyorder for Savitzky-Golay
    result2 = smooth_out_data( df, 'Y', method='Savitzky-Golay', window_length=7 )
    assert result2 is None


# @generated "all" gpt-4.1-nano
def test_smooth_out_data_invalid_method():
    df = generate_sample_data()
    result = smooth_out_data( df, 'Y', method='InvalidMethod' )
    assert result is None


def test_get_database_town_names():
    # Mock the get_connection function to return a DataFrame
    with patch( 'app.utils.get_connection' ) as mock_conn:
        mock_conn.return_value.query.return_value = pd.DataFrame( {'table_name': ['town1', 'town2']} )

        with mock_conn:
            result = get_database_town_names()
            assert result == ['town1', 'town2']
