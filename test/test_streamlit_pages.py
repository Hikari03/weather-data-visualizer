from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest


def test_login_page():
    at = AppTest.from_file( "app/streamlit_pages/login.py" )

    at.run()
    success = at.success
    assert not success, "Should not be logged in"

    # Check if the login button is present
    login_button = at.get( "button" )[0]
    assert login_button is not None, "Login button not found"


def test_import_page():
    at = AppTest.from_file( "app/streamlit_pages/import_page.py" )

    at.run()

    assert at.title
    assert len( at.button ) == 2
    assert at.markdown
    assert at.text_input
    at.text_input[0].set_value( "test" )
    assert at.text_input[0].value == "test"

    assert at.toggle
    at.toggle[0].set_value( True )
    assert at.toggle[0].value is True


def test_main_page():
    with patch( 'app.utils.get_connection' ) as mock_conn:
        mock_conn.return_value.query.return_value = pd.DataFrame( {'0'} )
        at = AppTest.from_file( "app/streamlit_pages/main.py" )

        at.run()

        assert at.title
        markdowns = at.markdown
        assert len( markdowns ) == 2
        assert markdowns[0].value.find( "You are logged in" )
        assert markdowns[1].value.find( "Data Sources" )


def test_mqtt_page():
    # We need to mock the database connection and the data returned by the query
    with patch( 'app.utils.get_connection' ) as mock_conn:
        mock_conn.return_value.query.return_value = pd.DataFrame( {'table_name': []} )

        at = AppTest.from_file( "app/streamlit_pages/mqtt.py" )
        at.run()
        assert at.title

        assert len( at.info ) == 2
        assert at.info[0].value == "No MQTT data found in the database. Please import data first."
