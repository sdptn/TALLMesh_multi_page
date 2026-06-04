"""
Azure Settings Management Module

This module provides functionality for managing Azure API settings and deployments
within a Streamlit application. It allows users to input and save their Azure API credentials,
manage Azure deployments, and view current settings.

The module includes functions for loading and saving Azure settings, managing deployments,
and creating a user interface for interacting with these settings.

Dependencies:
- streamlit: For creating the web application interface
- json: For reading and writing Azure settings to a JSON file
- os: For file path operations
"""

import streamlit as st
import json
import os

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Constants
AZURE_SETTINGS_FILE = 'azure_settings.json'

def load_azure_settings():
    """
    Load Azure settings from a JSON file.

    Returns:
        dict: A dictionary containing the Azure settings. If the file doesn't exist or is empty,
              an empty dictionary is returned.
    """
    if os.path.exists(AZURE_SETTINGS_FILE):
        with open(AZURE_SETTINGS_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    st.warning("Azure settings file is corrupted. Starting with empty settings.")
            else:
                st.info("Azure settings file is empty. You can add new settings below.")
    return {}

def save_azure_settings(settings):
    """
    Save Azure settings to a JSON file.

    Args:
        settings (dict): A dictionary containing the Azure settings to be saved.
    """
    with open(AZURE_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def get_azure_models():
    """
    Retrieve a list of available Azure models based on the saved deployments.

    Returns:
        list: A list of Azure model names, prefixed with 'azure_'.
    """
    azure_settings = load_azure_settings()
    return [f"azure_{deployment}" for deployment in azure_settings.get('deployments', [])]

def azure_settings():
    """
    Create a Streamlit interface for managing Azure API settings and deployments.

    This function sets up the user interface for inputting Azure API credentials,
    managing deployments, and displaying current settings.
    """
    st.header("Azure API Settings")

    # Display instructions for setting up Azure OpenAI
    with st.expander("Instructions"):
        display_instructions()

    # Load existing Azure settings
    azure_settings = load_azure_settings()

    # Input fields for Azure API credentials
    api_key = st.text_input("Azure API Key", value=azure_settings.get('api_key', ''), type="password")
    endpoint = st.text_input("Azure Endpoint", value=azure_settings.get('endpoint', ''))

    # Save Azure settings button
    if st.button("Save Azure Settings", key="save_azure_settings"):
        if api_key and endpoint:
            azure_settings['api_key'] = api_key
            azure_settings['endpoint'] = endpoint
            save_azure_settings(azure_settings)
            st.success("Azure settings saved successfully!")
        else:
            st.error("Please fill in both API Key and Endpoint.")

    st.divider()

    # Manage Azure deployments
    manage_azure_deployments(azure_settings)

    st.divider()

    # Display current Azure settings
    display_current_settings(azure_settings)

def display_instructions():
    """
    Display instructions for setting up Azure OpenAI in the Streamlit interface.
    """
    st.header("Setting Up Azure OpenAI")

    st.write("""
    To use Azure OpenAI with our application, you'll need to configure your Azure settings. Follow these steps:

    1. Enter your :orange[Azure API Key] and :orange[Azure Endpoint]. These can be found in your Azure portal.

    2. Click 'Save Azure Settings' to store your credentials securely.

    3. To add an Azure deployment (after completing steps 1 and 2):
    - Enter the :orange[Deployment Name] in the provided field.
    - Click 'Add Deployment' to save it.

    4. You can add multiple deployments if needed.

    5. To remove a deployment, click the 'Delete' button next to its name.
             
    6. To update your Azure API Key or Endpoint, simply modify them in the available text fields and click :orange[Save Azure Settings].

    Once set up, your Azure deployments will appear as options in the model selection dropdowns throughout the application, prefixed with :orange['azure_'].

    :warning: Remember to keep your API key confidential and never share it publicly.
    """)

    st.info("""
    **Note:** The Deployment Name is the identifier you chose when deploying a model in Azure. It's not the same as the model name (e.g., GPT-4). Make sure to use the correct Deployment Name for each of your Azure OpenAI deployments.
    """)

    st.success("""
    With your Azure settings configured, you're ready to use Azure OpenAI models in your analysis!
    """)

    st.subheader(":orange[3. Azure API Setup]")
    st.write("""
    To set up Azure API credentials, follow this video guide:
    """)
    st.video("https://www.youtube.com/watch?v=jQyYeYWD97I")
    st.write("For more information, check out: [How to Get an Azure OpneAI API Key](https://docs.mindmac.app/how-to.../add-api-key/create-azure-openai-api-key)")
    

def manage_azure_deployments(azure_settings):
    """
    Manage Azure deployments through a Streamlit interface.

    This function allows users to add new deployments and delete existing ones.

    Args:
        azure_settings (dict): The current Azure settings.
    """
    st.subheader("Manage Azure Deployments")

    # Initialize deployments list if it doesn't exist
    if 'deployments' not in azure_settings:
        azure_settings['deployments'] = []

    # Input field for new deployment
    deployment_name = st.text_input("Deployment Name")

    # Add new deployment
    if st.button("Add Deployment", key="add_deployment"):
        if deployment_name:
            if deployment_name not in azure_settings['deployments']:
                azure_settings['deployments'].append(deployment_name)
                save_azure_settings(azure_settings)
                st.success(f"Deployment '{deployment_name}' added successfully!")
            else:
                st.error(f"Deployment '{deployment_name}' already exists.")
        else:
            st.error("Please enter a Deployment Name.")

    # Display and manage existing deployments
    if azure_settings['deployments']:
        st.subheader("Current Azure Deployments")
        for i, deployment in enumerate(azure_settings['deployments']):
            col1, col2 = st.columns([3, 1])
            col1.text(f"Deployment: {deployment}")
            if col2.button("Delete", key=f"delete_deployment_{i}"):
                azure_settings['deployments'].remove(deployment)
                save_azure_settings(azure_settings)
                st.success(f"Deployment '{deployment}' deleted.")
                st.rerun()

def display_current_settings(azure_settings):
    """
    Display the current Azure settings in the Streamlit interface.

    Args:
        azure_settings (dict): The current Azure settings.
    """
    st.subheader("Current Azure Settings")
    if azure_settings.get('api_key'):
        st.text(f"API Key: {'*' * len(azure_settings['api_key'])}")
    if azure_settings.get('endpoint'):
        st.text(f"Endpoint: {azure_settings['endpoint']}")

if __name__ == "__main__":
    azure_settings()
