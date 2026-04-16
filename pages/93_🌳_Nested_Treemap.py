"""
11_🌳_Nested_Treemap.py

This module creates a nested treemap visualization for qualitative data analysis projects.
It allows users to explore themes, reduced codes, initial codes, and quotes in a hierarchical structure.

The treemap provides an interactive way to visualize the relationships between different levels of coding
in a qualitative analysis project, from broad themes down to specific quotes.

Dependencies:
- streamlit: For creating the web application interface
- pandas: For data manipulation and analysis
- plotly.express: For creating the interactive treemap visualization
- project_utils: Custom module for project-related utility functions
- os: For file and directory operations
- api_key_management: Custom module for managing API keys

"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from project_utils import get_projects, PROJECTS_DIR, get_processed_files

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

def load_data(project_name):
    """
    Load the latest theme and code data for a given project.

    Args:
        project_name (str): The name of the project to load data for.

    Returns:
        tuple: A tuple containing two pandas DataFrames (themes_df, codes_df).
               Returns (None, None) if no data is available.

    This function searches for the most recent 'expanded' themes file and the latest codes file
    in the project's directory structure. It then loads these files into pandas DataFrames.
    """
    # Define paths for themes and codes folders
    themes_folder = os.path.join(PROJECTS_DIR, project_name, 'theme_books')
    codes_folder = os.path.join(PROJECTS_DIR, project_name, 'expanded_pairwise_reduced_codes')
    
    # Get list of theme files and filter for 'expanded' themes
    themes_files = get_processed_files(project_name, 'theme_books')
    expanded_themes_files = [f for f in themes_files if 'expanded' in f]
    if not expanded_themes_files:
        return None, None
    
    # Get the most recent expanded themes file
    latest_themes_file = max(expanded_themes_files, key=lambda f: os.path.getmtime(os.path.join(themes_folder, f)))
    themes_df = pd.read_csv(os.path.join(themes_folder, latest_themes_file))
    
    # Get list of codes files
    codes_files = get_processed_files(project_name, 'expanded_pairwise_reduced_codes')
    if not codes_files:
        return None, None
    
    # Get the most recent codes file
    latest_codes_file = max(codes_files, key=lambda f: os.path.getmtime(os.path.join(codes_folder, f)))
    codes_df = pd.read_csv(os.path.join(codes_folder, latest_codes_file))

    return themes_df, codes_df 

def prepare_treemap_data(themes_df, codes_df):
    """
    Prepare data for the treemap visualization by combining theme and code information.

    Args:
        themes_df (pd.DataFrame): DataFrame containing theme information.
        codes_df (pd.DataFrame): DataFrame containing code information.

    Returns:
        pd.DataFrame: A DataFrame structured for use in creating a nested treemap.

    This function creates a hierarchical structure of themes, reduced codes, initial codes, and quotes,
    which can be used to generate a nested treemap visualization.
    """
    treemap_data = []
    
    # Iterate through each theme
    for _, theme_row in themes_df.iterrows():
        theme = theme_row['Theme']
        theme_description = theme_row['Theme Description']
        reduced_code = theme_row['Code']
        reduced_code_description = theme_row['Code Description']
        
        # Filter codes_df for the current reduced code
        relevant_codes = codes_df[codes_df['code'] == reduced_code]
        
        # Iterate through each relevant code
        for _, code_row in relevant_codes.iterrows():
            initial_code = code_row['original_code']
            quote = code_row['quote']
            # Note: 'source' is commented out as it's not currently used
            # source = code_row['source']
            
            # Append data for each level of the hierarchy
            treemap_data.append({
                'Theme': theme,
                'Theme Description': theme_description,
                'Reduced Code': reduced_code,
                'Reduced Code Description': reduced_code_description,
                'Initial Code': initial_code,
                'Quote': quote,
                'Value': 1  # Each entry has a value of 1 for equal weighting in the treemap
            })
    
    return pd.DataFrame(treemap_data)

def main():
    """
    Main function to run the Streamlit app for the Nested Treemap visualization.

    This function sets up the Streamlit interface, handles project selection,
    loads and prepares data, and creates the interactive treemap visualization.
    """
    st.header(":orange[Nested Treemap Visualization]")
    st.subheader(":orange[Structure: Theme > Reduced Codes > Initial Code > Quote]")

    # Get list of projects and set up project selection
    projects = get_projects()
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = "Select a project..."

    project_options = ["Select a project..."] + projects
    index = project_options.index(st.session_state.selected_project) if st.session_state.selected_project in project_options else 0

    selected_project = st.selectbox(
        "Select a project:", 
        project_options,
        index=index,
        key="project_selector"
    )

    # Rerun the app if a new project is selected
    if selected_project != st.session_state.selected_project:
        st.session_state.selected_project = selected_project
        st.rerun()

    if selected_project != "Select a project...":
        # Load data for the selected project
        themes_df, codes_df = load_data(selected_project)

        if themes_df is None or codes_df is None:
            st.error("No data available for the selected project.")
            return

        # Prepare data for the treemap
        treemap_data = prepare_treemap_data(themes_df, codes_df)

        # Create the treemap visualization
        fig = px.treemap(
            treemap_data,
            path=['Theme', 'Reduced Code', 'Initial Code', 'Quote'],
            values='Value',
            hover_data=['Theme Description', 'Reduced Code Description'],
            color='Theme',
            color_continuous_scale='RdBu',
        )

        # Customize the appearance and behavior of the treemap
        fig.update_traces(
            textinfo="label",
            textfont=dict(size=20),  
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Description: %{customdata[0]}<extra></extra>'
        )

        fig.update_layout(
            margin=dict(t=50, l=25, r=25, b=25),
            height=800,
            title="Nested Treemap of Themes, Codes, and Quotes"
        )

        # Display the treemap
        st.plotly_chart(fig, use_container_width=True)

        # Provide instructions for interacting with the treemap
        st.write("Click on the rectangles to zoom in. Double-click to zoom out. Hover for descriptions.")
        st.write("To return to the original view, click in the top left of the visualization or refresh the page.")



if __name__ == "__main__":
    main()