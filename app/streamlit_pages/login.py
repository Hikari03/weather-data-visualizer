"""
Page for logging in to the app.
"""

import streamlit as st

st.set_page_config( layout="wide" )
st.title( "Login" )
if not st.user.is_logged_in:
    if st.button( "Log in with Google" ):
        st.login()
    st.stop()

if st.button( "Log out" ):
    st.logout()

st.success( f"Welcome! {st.user.to_dict()["name"]}" )
