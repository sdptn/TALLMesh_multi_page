# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 15:16:46 2024

@author: Stefano De Paoli - s.depaoli@abertay.ac.uk

This script implements a Streamlit page for measuring and visualizing the saturation
of qualitative coding in a research project. It calculates and displays the ITS
(Incremental Theme Saturation) Metric, which is a measure of coding saturation.

The script uses data from initial coding (total codes) and the reduction of codes
(unique codes) stored in the project folder to generate these metrics and visualizations.
"""

import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from project_utils import get_projects
from instructions import saturation_metric_instructions

# Constants
from project_utils import get_user_project_dir

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

def count_total_initial_codes(project_name):
    """Count total rows across all initial coding CSV files."""
    base_dir = get_user_project_dir()
    folder = os.path.join(base_dir, project_name, 'initial_codes')
    if not os.path.exists(folder):
        return 0

    total = 0
    for filename in os.listdir(folder):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder, filename)
            df = pd.read_csv(file_path)
            total += len(df)
    return total

def get_latest_pairwise_reduced_count(project_name):
    """Get row count from the most recent pairwise reduced codes file."""
    base_dir = get_user_project_dir()
    folder = os.path.join(base_dir, project_name, 'pairwise_reduced_codes')
    if not os.path.exists(folder):
        return 0, None

    csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]
    if not csv_files:
        return 0, None

    latest_file = max(csv_files, key=lambda f: os.path.getmtime(os.path.join(folder, f)))
    latest_path = os.path.join(folder, latest_file)
    df = pd.read_csv(latest_path)
    return len(df), latest_file

def main():
    """
    Main function to run the Streamlit app for measuring saturation.
    """
    saturation_metric_instructions()
    
    st.write("See our paper on saturation and LLMs (https://arxiv.org/pdf/2401.03239) for more information.")
    
    st.subheader("This metric reflects the degree of code consolidation following pairwise reduction, and serves as a proxy for saturation.")

    # Project selection
    projects = get_projects()
    
    # Initialize session state for selected project if it doesn't exist
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = "Select a project..."

    # Calculate the index for the selectbox
    project_options = ["Select a project..."] + projects
    index = project_options.index(st.session_state.selected_project) if st.session_state.selected_project in project_options else 0

    # Use selectbox with the session state as the default value
    selected_project = st.selectbox(
        "Select a project:", 
        project_options,
        index=index,
        key="project_selector"
    )

    # Update session state when a new project is selected
    if selected_project != st.session_state.selected_project:
        st.session_state.selected_project = selected_project
        st.rerun()

    if selected_project != "Select a project...":
        with st.spinner("Processing..."):
            total_codes = count_total_initial_codes(selected_project)
            unique_codes, latest_pairwise_file = get_latest_pairwise_reduced_count(selected_project)

            if total_codes == 0:
                st.error("No initial coding files found. Please run initial coding first.")
            elif unique_codes == 0:
                st.error("No pairwise reduced codes file found. Please run pairwise reduction first.")
            else:
                its_metric = round(unique_codes / total_codes, 3)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(":orange[ITS Metric (Saturation):]")
                with col2:
                    st.subheader(f":green[{its_metric}]")

                st.write(f"Latest pairwise reduced file used: {latest_pairwise_file}")
                st.success("Files processed successfully!")

                # Create plot
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=["Total Initial Codes", "Unique Pairwise Reduced Codes"],
                    y=[total_codes, unique_codes]
                ))
                fig.update_layout(
                    title="Initial vs Pairwise Reduced Code Counts",
                    xaxis_title="Code Type",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig)

                # Display data in two columns
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Initial Codes", total_codes)
                with col2:
                    st.metric("Unique Pairwise Reduced Codes", unique_codes)
        



if __name__ == "__main__":
    main()