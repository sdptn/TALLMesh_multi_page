"""
Sankey Diagram (Initial Codes -> Reduced Codes -> Themes) Generator

This module creates an interactive Sankey diagram visualization of the flow from initial codes
to reduced codes to themes in a qualitative data analysis project. It uses Streamlit for the web interface
and Plotly for the interactive diagram.

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
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Custom modules
from project_utils import get_projects, PROJECTS_DIR, get_processed_files

def load_data(project_name):
    """
    Load the latest theme and code data for a given project.

    Args:
        project_name (str): Name of the project to load data for.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the merged data.
                      Returns None if no data is available.
    """
    themes_folder = os.path.join(PROJECTS_DIR, project_name, 'theme_books')
    codes_folder = os.path.join(PROJECTS_DIR, project_name, 'expanded_pairwise_reduced_codes')
    
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
    
    # Merge dataframes to associate codes with themes
    merged_df = codes_df.merge(themes_df, left_on='code', right_on='Code', how='left')
    
    return merged_df

def hex_to_rgba(hex_color, opacity):
    """Convert hex color to rgba string with the given opacity."""
    hex_color = hex_color.lstrip('#')
    h_len = len(hex_color)
    rgb = tuple(int(hex_color[i:i+h_len//3], 16) for i in range(0, h_len, h_len//3))
    return f'rgba{rgb + (opacity,)}'



def create_sankey_diagram(data, level_selection, style_settings=None):
    """
    Create an improved Sankey diagram with better visual hierarchy and readability.
    """
    # Set default style settings with improved colors and layout
    default_settings = {
        'node_pad': 20,
        'node_thickness': 25,
        'node_line_color': '#ffffff',
        'node_line_width': 0.5,
        'initial_code_color': '#fde047',  # Warm yellow
        'reduced_code_color': '#84cc16',  # Fresh green
        'theme_color': '#22c55e',         # Deep green
        'link_opacity': 0.6,
        'font_size': 14,
        'margin_top': 20,
        'margin_bottom': 20,
        'margin_left': 20,
        'margin_right': 20,
        'nodes_per_height_unit': 15,
        'bgcolor': '#ffffff',
        'paper_bgcolor': '#ffffff'
    }
    
    # Update with user settings if provided
    if style_settings:
        default_settings.update(style_settings)
    
    if level_selection == ['Initial Code', 'Reduced Code', 'Theme']:
        grouped_data = data.groupby(['original_code', 'code', 'Theme']).size().reset_index(name='count')
        
        # Calculate optimal height
        max_nodes = max(
            len(grouped_data['original_code'].unique()),
            len(grouped_data['code'].unique()),
            len(grouped_data['Theme'].unique())
        )
        dynamic_height = min(2000, max(600, max_nodes * default_settings['nodes_per_height_unit']))
        
        # Create node lists and link data
        nodes = []
        links = []
        node_indices = {}
        
        # Process nodes with improved colors
        for idx, code in enumerate(grouped_data['original_code'].unique()):
            node_indices[code] = len(nodes)
            nodes.append(dict(
                label=code,
                color=default_settings['initial_code_color'],
                customdata=[code],
                hovertemplate='%{customdata[0]}<extra></extra>'
            ))
            
        for code in grouped_data['code'].unique():
            if code not in node_indices:
                node_indices[code] = len(nodes)
                nodes.append(dict(
                    label=code,
                    color=default_settings['reduced_code_color'],
                    customdata=[code],
                    hovertemplate='%{customdata[0]}<extra></extra>'
                ))
                
        for theme in grouped_data['Theme'].unique():
            if theme not in node_indices:
                node_indices[theme] = len(nodes)
                nodes.append(dict(
                    label=theme,
                    color=default_settings['theme_color'],
                    customdata=[theme],
                    hovertemplate='%{customdata[0]}<extra></extra>'
                ))
        
        # Create links with improved styling
        for _, row in grouped_data.iterrows():
            # Link from initial to reduced code
            links.append(dict(
                source=node_indices[row['original_code']],
                target=node_indices[row['code']],
                value=row['count'],
                color=f'rgba{tuple(int(default_settings["initial_code_color"].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (default_settings["link_opacity"],)}'
            ))
            
            # Link from reduced code to theme
            links.append(dict(
                source=node_indices[row['code']],
                target=node_indices[row['Theme']],
                value=row['count'],
                color=f'rgba{tuple(int(default_settings["reduced_code_color"].lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (default_settings["link_opacity"],)}'
            ))
        
        # Create figure with improved layout
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=default_settings['node_pad'],
                thickness=default_settings['node_thickness'],
                line=dict(
                    color=default_settings['node_line_color'],
                    width=default_settings['node_line_width']
                ),
                label=[node['label'] for node in nodes],
                color=[node['color'] for node in nodes],
                customdata=[node['customdata'] for node in nodes],
                hovertemplate=[node['hovertemplate'] for node in nodes]
            ),
            link=dict(
                source=[link['source'] for link in links],
                target=[link['target'] for link in links],
                value=[link['value'] for link in links],
                color=[link['color'] for link in links]
            ),
            arrangement="snap"
        )])
        
        # Update layout with improved styling
        fig.update_layout(
            font=dict(
                family="Arial, sans-serif",
                size=default_settings['font_size'],
                color="#1f2937"
            ),
            paper_bgcolor=default_settings['paper_bgcolor'],
            plot_bgcolor=default_settings['bgcolor'],
            height=dynamic_height,
            margin=dict(
                t=default_settings['margin_top'],
                l=default_settings['margin_left'],
                r=default_settings['margin_right'],
                b=default_settings['margin_bottom']
            ),
            autosize=True
        )
        
        return fig
    else:
        st.error("Currently, only the 'Initial Code -> Reduced Code -> Theme' flow is implemented.")
        return None

def main():
    """
    Main function to run the Streamlit app.

    This function sets up the user interface, handles project selection,
    loads data, creates the Sankey diagram, and displays it in the Streamlit app.
    """
    st.header(":orange[Sankey Diagram of Codes Flow]")

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
        data = load_data(selected_project)
        
        if data is None or data.empty:
            st.error("No data available for the selected project.")
            return

        selected_levels = ['Initial Code', 'Reduced Code', 'Theme']

        # Advanced settings in an expander
        with st.expander("Advanced Settings"):
            # Create a single tab for settings
            tab, = st.tabs(["Settings"])
            with tab:
                # Filters Section
                st.markdown("#### Filters")
                filter_theme = st.multiselect(
                    "Filter by Theme", 
                    options=data['Theme'].unique(), 
                    help="Select themes to display in the Sankey diagram"
                )
                filter_reduced_code = st.multiselect(
                    "Filter by Reduced Code", 
                    options=data['code'].unique(),
                    help="Select reduced codes to display in the Sankey diagram"
                )
                filter_initial_code = st.multiselect(
                    "Filter by Initial Code", 
                    options=data['original_code'].unique(),
                    help="Select initial codes to display in the Sankey diagram"
                )
                
                # Colours Section
                st.markdown("#### Colours")
                col1, col2, col3 = st.columns(3)
                with col1:
                    initial_code_color = st.color_picker(
                        "Initial Codes Color", 
                        '#F7F069', 
                        help="Choose the color for initial code nodes"
                    )
                with col2:
                    reduced_code_color = st.color_picker(
                        "Reduced Codes Color", 
                        '#DE7863', 
                        help="Choose the color for reduced code nodes"
                    )
                with col3:
                    theme_color = st.color_picker(
                        "Themes Color", 
                        '#6BE6D3',
                        help="Choose the color for theme nodes"
                    )
                link_opacity = st.slider(
                    "Link Opacity", 
                    0.0, 1.0, 1.0, 0.1, 
                    help="Adjust the opacity of the links between nodes (0 is fully transparent, 1 is fully opaque)"
                )
                
                # Layout Section
                st.markdown("#### Layout")
                col1, col2 = st.columns(2)
                with col1:
                    font_size = st.number_input(
                        "Font Size", 
                        8, 24, 16, 
                        help="Set the font size of the labels in the diagram"
                    )
                    nodes_per_height = st.number_input(
                        "Height per Node", 
                        5, 50, 20,
                        help="Adjust the vertical spacing between nodes; higher values increase spacing"
                    )
                with col2:
                    margin_top = st.number_input(
                        "Top Margin", 
                        0, 100, 5, 
                        help="Set the top margin of the diagram in pixels"
                    )
                    margin_bottom = st.number_input(
                        "Bottom Margin", 
                        0, 100, 10, 
                        help="Set the bottom margin of the diagram in pixels"
                    )
                    margin_left = st.number_input(
                        "Left Margin", 
                        0, 100, 5, 
                        help="Set the left margin of the diagram in pixels"
                    )
                    margin_right = st.number_input(
                        "Right Margin", 
                        0, 100, 10, 
                        help="Set the right margin of the diagram in pixels"
                    )
                
                # Node Style Section
                st.markdown("#### Node Style")
                col1, col2 = st.columns(2)
                with col1:
                    node_pad = st.number_input(
                        "Node Padding", 
                        5, 50, 15, 
                        help="Set the amount of padding between nodes"
                    )
                    node_thickness = st.number_input(
                        "Node Thickness", 
                        5, 50, 20, 
                        help="Set the thickness of the nodes in pixels"
                    )
                with col2:
                    node_line_color = st.color_picker(
                        "Node Line Color", 
                        '#ffffff', 
                        help="Choose the color of the node borders"
                    )
                    node_line_width = st.number_input(
                        "Node Line Width", 
                        0.0, 5.0, 1.0, 0.1, 
                        help="Set the width of the node borders"
                    )

        # Apply filters
        df_filtered = data.copy()
        if filter_theme:
            df_filtered = df_filtered[df_filtered['Theme'].isin(filter_theme)]
        if filter_reduced_code:
            df_filtered = df_filtered[df_filtered['code'].isin(filter_reduced_code)]
        if filter_initial_code:
            df_filtered = df_filtered[df_filtered['original_code'].isin(filter_initial_code)]

        # Collect style settings
        style_settings = {
            'initial_code_color': initial_code_color,
            'reduced_code_color': reduced_code_color,
            'theme_color': theme_color,
            'link_opacity': link_opacity,
            'font_size': font_size,
            'margin_top': margin_top,
            'margin_bottom': margin_bottom,
            'margin_left': margin_left,
            'margin_right': margin_right,
            'node_pad': node_pad,
            'node_thickness': node_thickness,
            'node_line_color': node_line_color,
            'node_line_width': node_line_width,
            'nodes_per_height_unit': nodes_per_height
        }

        # Create and display the Sankey diagram
        fig = create_sankey_diagram(df_filtered, selected_levels, style_settings)

        if fig:

            st.plotly_chart(fig, use_container_width=True)

            # Option to display data as a table
            with st.expander("Show Data Table"):
                st.dataframe(df_filtered)
    

if __name__ == "__main__":
    main()
