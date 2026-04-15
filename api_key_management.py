import streamlit as st
import json
import os

# File to store API keys
API_KEYS_FILE = 'api_keys.json'

# List of LLM providers
providers = ['GRAPHIA_LLM']

def load_api_keys():
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_api_keys(api_keys):
    with open(API_KEYS_FILE, 'w') as f:
        json.dump(api_keys, f)

def manage_api_keys():
    st.sidebar.header("API Key Management")

    # Load existing API keys
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = load_api_keys()

    # Add new API key
    new_provider = st.sidebar.selectbox("Provider", providers)
    new_key = st.sidebar.text_input("API Key", type="password")
    
    if st.sidebar.button("Add API Key"):
        if new_provider and new_key:
            st.session_state.api_keys[new_provider] = new_key
            save_api_keys(st.session_state.api_keys)
            st.sidebar.success(f"API Key for {new_provider} added successfully!")
        else:
            st.sidebar.error("Please enter both provider and key.")

    # Display and manage existing API keys
    st.sidebar.subheader("Saved API Keys")
    for provider, value in st.session_state.api_keys.items():
        col1, col2 = st.sidebar.columns([3, 1])
        masked_key = '*' * (len(value) - 3) + value[-3:]
        col1.text(f"{provider}: {masked_key[-7:]}")
        
        if col2.button("❌", key=f"delete_{provider}"):
            del st.session_state.api_keys[provider]
            save_api_keys(st.session_state.api_keys)
            st.sidebar.success(f"API Key for {provider} deleted.")
            st.rerun()
