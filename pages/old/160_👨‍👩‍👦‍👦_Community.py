# Import necessary libraries
import os
import streamlit as st
import json
from api_key_management import manage_api_keys
import shutil

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

def main():

    # Just some placeholder for now until public

    # Display logo
    logo = "pages/static/tmeshlogo.png"
    st.image(logo)

    st.header(("Community Details Coming Soon!!"))

    manage_api_keys()


if __name__ == "__main__":
    main()