"""
Enhanced Sunburst Chart (Themes-Codes-Quotes Hierarchy) Generator

This module creates an interactive Sunburst chart visualization of themes, codes, and quotes
from a qualitative data analysis project. It allows users to add or remove levels, adjust text size,
and filter data based on themes or reduced codes.

Dependencies:
- streamlit
- pandas
- plotly
- project_utils (custom module)
- api_key_management (custom module)
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Custom modules
from project_utils import get_projects, get_user_project_dir, get_processed_files

def load_data(project_name):
    """
    Load the latest theme and code data for a given project.

    Args:
        project_name (str): Name of the project to load data for.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the hierarchical data.
                      Returns None if no data is available.
    """
    base_dir = get_user_project_dir()
    themes_folder = os.path.join(base_dir, project_name, 'theme_books')
    codes_folder = os.path.join(base_dir, project_name, 'expanded_pairwise_reduced_codes')
    
    # Load themes data
    themes_files = get_processed_files(project_name, 'theme_books')
    expanded_themes_files = [f for f in themes_files if 'expanded' in f]
    if not expanded_themes_files:
        return None
    latest_themes_file = max(expanded_themes_files, key=lambda f: os.path.getmtime(os.path.join(themes_folder, f)))
    themes_df = pd.read_csv(os.path.join(themes_folder, latest_themes_file))
    
    # Load codes data
    codes_files = get_processed_files(project_name, 'expanded_pairwise_reduced_codes')
    if not codes_files:
        return None
    latest_codes_file = max(codes_files, key=lambda f: os.path.getmtime(os.path.join(codes_folder, f)))
    codes_df = pd.read_csv(os.path.join(codes_folder, latest_codes_file))
    
    # Merge dataframes to create a hierarchical structure
    merged_df = themes_df.merge(codes_df, left_on='Code', right_on='code', how='left')
    
    # Create a DataFrame suitable for Sunburst chart
    data = pd.DataFrame({
        'Theme': merged_df['Theme'],
        'Theme Description': merged_df['Theme Description'],
        'Reduced Code': merged_df['Code'],
        'Reduced Code Description': merged_df['Code Description'],
        'Initial Code': merged_df['original_code'],
        'Quote': merged_df['quote']
    })
    
    return data

def create_sunburst_chart(data, levels, color_scheme, text_size):
    """
    Create an interactive Sunburst chart using Plotly.

    Args:
        data (pd.DataFrame): DataFrame containing the hierarchical data.
        levels (list): List of levels to include in the chart.
        color_scheme (list): List of colors for the chart.
        text_size (int): Font size for the text in the chart.

    Returns:
        plotly.graph_objects.Figure: The Sunburst chart figure.
    """
    fig = px.sunburst(
        data,
        path=levels,
        maxdepth=-1,
        color=levels[0] if levels else None,
        color_discrete_sequence=color_scheme,
        hover_data={'Quote': True},
        branchvalues='total'
    )
    fig.update_traces(textinfo='label') # use fig.update_traces(textinfo='label+percent entry') for percentages in slices
    fig.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        font=dict(size=text_size)
    )
    return fig

def main():
    """
    Main function to run the Streamlit app.

    This function sets up the user interface, handles project selection,
    loads data, creates the Sunburst chart, and displays it in the Streamlit app.
    """
    st.header(":orange[Enhanced Themes-Codes-Quotes Sunburst Chart]")

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
        data = load_data(selected_project)

        if data is None or data.empty:
            st.error("No data available for the selected project.")
            return

        # Advanced settings in an expander
        with st.expander("Advanced Settings"):
            # Let users choose which levels to display
            available_levels = ['Theme', 'Reduced Code', 'Initial Code', 'Quote']
            default_levels = ['Theme', 'Reduced Code', 'Initial Code', 'Quote']
            selected_levels = st.multiselect(
                "Select levels to display in the Sunburst chart",
                available_levels,
                default=default_levels,
                key="level_selector"
            )

            if not selected_levels:
                st.warning("Please select at least one level to display.")
                return

            # Filtering options
            filter_theme = st.multiselect("Filter by Theme", options=data['Theme'].unique())
            filter_reduced_code = st.multiselect("Filter by Reduced Code", options=data['Reduced Code'].unique())

            # Accessibility options
            text_size = st.slider("Adjust text size", min_value=10, max_value=24, value=14, step=1)

        # Apply filters
        df_filtered = data.copy()
        if filter_theme:
            df_filtered = df_filtered[df_filtered['Theme'].isin(filter_theme)]
        if filter_reduced_code:
            df_filtered = df_filtered[df_filtered['Reduced Code'].isin(filter_reduced_code)]

        # Define color scheme
        color_scheme = px.colors.qualitative.Plotly

        # Create and display the Sunburst chart
        fig = create_sunburst_chart(df_filtered, selected_levels, color_scheme, text_size)
        st.plotly_chart(fig, use_container_width=True)

        st.write("Hover over segments to see details. Click on segments to drill down or back up the hierarchy.")

        # Option to display data as a table
        with st.expander("Show Data Table"):
            st.dataframe(df_filtered)


if __name__ == "__main__":
    main()
