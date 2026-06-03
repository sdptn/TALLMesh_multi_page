"""
Spider Diagram (Theme-Codes Mind Map) Generator

This module creates an interactive mind map visualization of themes, codes, and quotes
from a qualitative data analysis project. It uses Streamlit for the web interface,
NetworkX for graph creation, and Pyvis for interactive network visualization.

The mind map displays the hierarchical relationship between:
1. The project
2. Themes
3. Reduced codes
4. Initial codes
5. Quotes

Dependencies:
- streamlit
- pandas
- networkx
- pyvis
- project_utils (custom module)
- api_key_management (custom module)
"""

import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import os
import tempfile

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Custom modules
from project_utils import get_projects, PROJECTS_DIR, get_processed_files
from api_key_management import manage_api_keys, load_api_keys

def load_data(project_name):
    """
    Load the latest theme and code data for a given project.

    Args:
        project_name (str): Name of the project to load data for.

    Returns:
        tuple: A tuple containing two pandas DataFrames (themes_df, codes_df).
               Returns (None, None) if no data is available.
    """
    themes_folder = os.path.join(PROJECTS_DIR, project_name, 'theme_books')
    codes_folder = os.path.join(PROJECTS_DIR, project_name, 'expanded_pairwise_reduced_codes')
    
    # Load themes data
    themes_files = get_processed_files(project_name, 'theme_books')
    expanded_themes_files = [f for f in themes_files if 'expanded' in f]
    if not expanded_themes_files:
        return None, None
    latest_themes_file = max(expanded_themes_files, key=lambda f: os.path.getmtime(os.path.join(themes_folder, f)))
    themes_df = pd.read_csv(os.path.join(themes_folder, latest_themes_file))
    
    # Load codes data
    codes_files = get_processed_files(project_name, 'expanded_pairwise_reduced_codes')
    if not codes_files:
        return None, None
    latest_codes_file = max(codes_files, key=lambda f: os.path.getmtime(os.path.join(codes_folder, f)))
    codes_df = pd.read_csv(os.path.join(codes_folder, latest_codes_file))

    return themes_df, codes_df

def create_mind_map(project_name, themes_df, codes_df):
    """
    Create an interactive mind map visualization using NetworkX and Pyvis.

    Args:
        project_name (str): Name of the project.
        themes_df (pd.DataFrame): DataFrame containing theme data.
        codes_df (pd.DataFrame): DataFrame containing code data.

    Returns:
        str: HTML string representation of the interactive mind map.
    """
    G = nx.Graph()
    
    # Add project node
    G.add_node(project_name, color='#FF9999', size=50, title=project_name)
    
    # Add theme nodes and edges
    for _, theme_row in themes_df.iterrows():
        theme = theme_row['Theme']
        theme_id = f"theme_{theme}"
        theme_description = theme_row['Theme Description']
        G.add_node(theme_id, color='#99CCFF', size=35, title=f"{theme}\n\n{theme_description}", label=theme)
        G.add_edge(project_name, theme_id)
        
        # Add reduced code nodes and edges
        reduced_code = theme_row['Code']
        reduced_code_id = f"reduced_{reduced_code}"
        reduced_code_description = theme_row['Code Description']
        G.add_node(reduced_code_id, color='#99FF99', size=25, title=f"{reduced_code}\n\n{reduced_code_description}", label=reduced_code)
        G.add_edge(theme_id, reduced_code_id)
        
        # Add initial code nodes and edges
        initial_codes = codes_df[codes_df['code'] == reduced_code]
        for _, initial_code_row in initial_codes.iterrows():
            initial_code = initial_code_row['original_code']
            initial_code_id = f"initial_{initial_code}_{reduced_code}"  # Include reduced_code to ensure uniqueness
            initial_code_description = initial_code_row['description']
            G.add_node(initial_code_id, color='#FFCC99', size=20, title=f"{initial_code}\n\n{initial_code_description}", label=initial_code)
            G.add_edge(reduced_code_id, initial_code_id)
            
            # Add quote nodes and edges
            quote = initial_code_row['quote']
            quote_id = f"quote_{initial_code}_{reduced_code}"  # Include both initial_code and reduced_code for uniqueness
            G.add_node(quote_id, color='#CC99FF', size=15, title=quote, label=quote[:150])
            G.add_edge(initial_code_id, quote_id)
    
    # Create a Pyvis network from our NetworkX graph
    net = Network(height='600px', width='100%', bgcolor='#222222', font_color='white')
    net.from_nx(G)
    net.toggle_physics(False)
    
    # Set network options for better visualization
    net.set_options('''
    var options = {
      "nodes": {
        "font": {
          "size": 12
        }
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": false
      },
      "physics": {
        "hierarchicalRepulsion": {
          "centralGravity": 0
        },
        "minVelocity": 0.75,
        "solver": "hierarchicalRepulsion"
      }
    }
    ''')
    
    # Save and read the HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmpfile:
        net.save_graph(tmpfile.name)
        with open(tmpfile.name, 'r', encoding='utf-8') as f:
            html_string = f.read()
    
    return html_string

def main():
    """
    Main function to run the Streamlit app.
    
    This function sets up the user interface, handles project selection,
    loads data, creates the mind map, and displays it in the Streamlit app.
    """
    st.header(":orange[Theme-Codes Mind Map]")

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

        # Create and display the mind map
        mind_map_html = create_mind_map(selected_project, themes_df, codes_df)
        st.components.v1.html(mind_map_html, height=600)

        st.write("Drag nodes to rearrange. Zoom with mouse wheel. Click nodes to expand/collapse.")
    
    # Manage API keys
    manage_api_keys()

if __name__ == "__main__":
    main()