# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 14:30:28 2024

@author: Stefano De Paoli - s.depaoli@abertay.ac.uk

This script is part of the TALLMesh multi-page application for qualitative data analysis.
It focuses on the reduction of initial codes generated in the previous step of the analysis process.
The main purpose is to refine and consolidate codes, identifying patterns and reducing redundancy.
"""

import os
import streamlit as st
import pandas as pd
import json
import re
from api_key_management import manage_api_keys, load_api_keys, load_azure_settings, get_azure_models, AZURE_SETTINGS_FILE
from project_utils import get_projects, get_project_files, get_processed_files, PROJECTS_DIR
from prompts import reduce_duplicate_codes_prompts
from llm_utils import llm_call, process_chunks, default_models, graphia_llm_models
import logging
import tooltips
import time
from ui_utils import centered_column_with_number, create_circle_number

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import gifs and set text for top of isntruction expander 

process_gif = "pages/animations/process_rounded.gif"
compare_gif = "pages/animations/compare_rounded.gif"
merge_gif = "pages/animations/merge_rounded.gif"
#compare_gif = "pages/animations/copy_rounded.gif" # alternative animated icon...


process_text = 'The LLM compares each set of initial codes...'
compare_text = '...to identify duplicates based on the prompt...'
merge_text = "...which are merged into a set of unique codes."

# Implement auto save to avoid need to restart due to unexpected interruptions

class AutoSaveResume:
    def __init__(self, project_name):
        self.project_name = project_name
        self.save_path = os.path.join(PROJECTS_DIR, project_name, 'code_reduction_progress.json')

    def save_progress(self, processed_files, reduced_df, total_codes_list, unique_codes_list, cumulative_total, mode):
        progress = {
            'processed_files': processed_files,
            'reduced_df': reduced_df.to_json(),
            'total_codes_list': total_codes_list,
            'unique_codes_list': unique_codes_list,
            'cumulative_total': cumulative_total,
            'mode': mode  # Store the processing mode
        }
        with open(self.save_path, 'w') as f:
            json.dump(progress, f)

    def load_progress(self):
        if os.path.exists(self.save_path):
            with open(self.save_path, 'r') as f:
                progress = json.load(f)
            progress['reduced_df'] = pd.read_json(progress['reduced_df'])
            return progress
        return None

    def clear_progress(self):
        if os.path.exists(self.save_path):
            os.remove(self.save_path)

def process_files_with_autosave(selected_project, selected_files, model, prompt, model_temperature, model_top_p, include_quotes, resume_data=None, mode='Automatic'):
    auto_save = AutoSaveResume(selected_project)
    
    if resume_data:
        processed_files = resume_data['processed_files']
        reduced_df = resume_data['reduced_df']
        total_codes_list = resume_data['total_codes_list']
        unique_codes_list = resume_data['unique_codes_list']
        cumulative_total = resume_data['cumulative_total']
    else:
        processed_files = []
        reduced_df = None
        total_codes_list = []
        unique_codes_list = []
        cumulative_total = 0

    progress_bar = st.progress(0)
    status_message = st.empty()
    total_files = len(selected_files)
    processed_file_count = len(processed_files)

    for file in selected_files:
        if file in processed_files:
            continue  # Skip already processed files
        processed_file_count += 1
        status_message.info(f"Processing file {processed_file_count}/{total_files}: {os.path.basename(file)}... please wait")
        logger.info(f"Processing file {processed_file_count}/{total_files}: {file}")
        df = pd.read_csv(file)

        if 'source' not in df.columns:
            df['source'] = os.path.basename(file)
            logger.info(f"Added 'source' column to DataFrame for file: {file}")
        
        file_total_codes = len(df)
        cumulative_total += file_total_codes
        logger.info(f"Cumulative total codes: {cumulative_total}")
        
        if reduced_df is None:
            reduced_df = df.copy()
            # Add merge_explanation column if it doesn't exist
            if 'merge_explanation' not in reduced_df.columns:
                reduced_df['merge_explanation'] = ''
            if 'original_code' not in reduced_df.columns:
                reduced_df['original_code'] = reduced_df['code']
            logger.info("First file processed, no reduction needed")
        else:
            logger.info(f"Comparing and reducing codes for file {processed_file_count}")
            status_message.info(f"Comparing and reducing codes for file {processed_file_count}/{total_files}...")
            reduced_df, _, _ = compare_and_reduce_codes(reduced_df, df, model, prompt, model_temperature, model_top_p, include_quotes)
            if reduced_df is None:
                logger.error(f"Failed to process file {file}. Stopping the process.")
                st.error(f"Failed to process file {file}. Stopping the process.")
                return None, None, []  # Return empty processed_files list on error
        
        total_codes_list.append(cumulative_total)
        unique_codes = len(reduced_df['code'].unique())
        unique_codes_list.append(unique_codes)
        logger.info(f"After processing file {processed_file_count}: Total codes = {cumulative_total}, Unique codes = {unique_codes}")
        
        progress = processed_file_count / total_files
        progress_bar.progress(progress)
        status_message.success(f"Processed file {processed_file_count}/{total_files}: Total codes = {cumulative_total}, Unique codes = {unique_codes}")

        # Auto-save progress after each file
        processed_files.append(file)
        auto_save.save_progress(processed_files, reduced_df, total_codes_list, unique_codes_list, cumulative_total, mode)

        # Save results after each file
        results_df = pd.DataFrame({
            'total_codes': total_codes_list,
            'unique_codes': unique_codes_list
        })
        results_path = os.path.join(PROJECTS_DIR, selected_project, 'code_reduction_results.csv')
        results_df.to_csv(results_path, index=False)
        logger.info(f"Saved code reduction results to: {results_path}")

        if mode == 'Incremental':
            # Ensure all required columns exist before returning
            required_columns = ['code', 'description', 'merge_explanation', 'original_code', 'quote', 'source']
            for col in required_columns:
                if col not in reduced_df.columns:
                    if col == 'merge_explanation':
                        reduced_df[col] = ''
                    elif col == 'original_code':
                        reduced_df[col] = reduced_df['code']
                    else:
                        logger.error(f"Required column {col} missing in incremental mode")
                        return None, None, []  # Return empty processed_files list on error
            
            # For incremental mode, stop after each file to allow user review
            return reduced_df, results_df, processed_files

    auto_save.clear_progress()  # Clear progress file after successful completion
    
    # Final save of results (ensures it's saved even if loop is empty)
    results_df = pd.DataFrame({
        'total_codes': total_codes_list,
        'unique_codes': unique_codes_list
    })
    results_path = os.path.join(PROJECTS_DIR, selected_project, 'code_reduction_results.csv')
    results_df.to_csv(results_path, index=False)
    logger.info(f"Saved final code reduction results to: {results_path}")
    
    return reduced_df, results_df, processed_files
    

def load_custom_prompts():
    """
    Load custom prompts from a JSON file.
    
    Returns:
        dict: A dictionary of custom prompts, or an empty dictionary if the file is not found.
    """
    try:
        with open('custom_prompts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def extract_json(text):
    """
    Extract a JSON object from a string.
    
    Args:
        text (str): The input string containing a JSON object.
    
    Returns:
        str: The extracted JSON string, or None if no JSON object is found.
    """
    match = re.search(r'\{[\s\S]*\}', text)
    return match.group(0) if match else None

def format_quotes(quotes_json):
    """
    Parse and format a JSON string of quotes for better readability.
    
    Args:
        quotes_json (str): A JSON string containing quote information.
    
    Returns:
        str: A formatted string with each quote on a new line, or the original string if parsing fails.
    """
    try:
        quotes = json.loads(quotes_json)
        formatted_quotes = "\n".join(f"{quote['text']} (Source: {quote['source']})" for quote in quotes)
        return formatted_quotes
    except (json.JSONDecodeError, KeyError, TypeError):
        return quotes_json  # Return the original if there's an error

def amalgamate_duplicate_codes(df):
    """
    Combine duplicate codes in a DataFrame, merging their associated information.
    
    Args:
        df (pd.DataFrame): The input DataFrame containing code information.
    
    Returns:
        pd.DataFrame: A new DataFrame with amalgamated code information.
    """
    # Ensure all required columns exist
    required_columns = ['code', 'description', 'merge_explanation', 'original_code', 'quote', 'source']
    for col in required_columns:
        if col not in df.columns:
            if col == 'merge_explanation':
                df[col] = ''
            elif col == 'original_code':
                df[col] = df['code']
            else:
                logger.error(f"Required column {col} missing in DataFrame")
                return None

    # Group by 'code' and aggregate other columns
    try:
        amalgamated_df = df.groupby('code').agg({
            'description': 'first',
            'merge_explanation': 'first',
            'original_code': lambda x: list(x),
            'quote': lambda x: [{'text': q, 'source': s} for q, s in zip(x, df.loc[x.index, 'source'])],
            'source': lambda x: list(x)
        }).reset_index()

        amalgamated_df['original_code'] = amalgamated_df['original_code'].apply(lambda x: json.dumps(list(x)))
        amalgamated_df['quote'] = amalgamated_df['quote'].apply(json.dumps)
        amalgamated_df['source'] = amalgamated_df['source'].apply(lambda x: ', '.join(set(x)))

        return amalgamated_df
    except Exception as e:
        logger.error(f"Error in amalgamate_duplicate_codes: {str(e)}")
        return None

def match_reduced_to_original_codes(reduced_df, initial_codes_directory):
    """
    Match reduced codes to their original codes by comparing quotes.
    
    Args:
        reduced_df (pd.DataFrame or str): The reduced codes DataFrame or path to the CSV file.
        initial_codes_directory (str): Path to the directory containing initial codes CSV files.
    
    Returns:
        pd.DataFrame: The reduced codes DataFrame with matched original codes.
    """
    # Check if reduced_df is a string (file path) or DataFrame
    if isinstance(reduced_df, str):
        reduced_df = pd.read_csv(reduced_df)
    elif not isinstance(reduced_df, pd.DataFrame):
        raise ValueError("reduced_df must be either a file path or a pandas DataFrame")
    
    # Dictionary to store initial codes dataframes
    initial_codes_dfs = {}
    
    # Read all initial codes files
    for filename in os.listdir(initial_codes_directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(initial_codes_directory, filename)
            initial_codes_dfs[filename] = pd.read_csv(file_path)
    
    # Function to find the original code
    def find_original_code(row):
        source_file = row['source']
        quote = row['quote']
        
        if source_file in initial_codes_dfs:
            source_df = initial_codes_dfs[source_file]
            matching_row = source_df[source_df['quote'] == quote]
            
            if not matching_row.empty:
                return matching_row['code'].values[0]
        
        return 'Original code not found'
    
    # Apply the function to each row in the reduced codes dataframe
    reduced_df['original_code'] = reduced_df.apply(find_original_code, axis=1)
    
    return reduced_df

def save_reduced_codes(project_name, df, folder):
    """
    Save the reduced codes DataFrame to a CSV file in the specified project folder.
    
    Args:
        project_name (str): The name of the project.
        df (pd.DataFrame): The DataFrame containing reduced codes.
        folder (str): The subfolder name to save the file in.
    
    Returns:
        str: The path of the saved CSV file.
    """
    reduced_codes_folder = os.path.join(PROJECTS_DIR, project_name, folder)
    os.makedirs(reduced_codes_folder, exist_ok=True)
    
    output_file_path = os.path.join(reduced_codes_folder, f"reduced_codes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(output_file_path, index=False, encoding='utf-8')
    return output_file_path

def compare_and_reduce_codes(df1, df2, model, prompt, model_temperature, model_top_p, include_quotes):
    """
    Compare and reduce codes from two DataFrames using an AI model.
    
    Args:
        df1 (pd.DataFrame): The first DataFrame containing codes.
        df2 (pd.DataFrame): The second DataFrame containing codes.
        model (str): The name of the AI model to use.
        prompt (str): The prompt to guide the AI in code reduction.
        model_temperature (float): The temperature setting for the AI model.
        model_top_p (float): The top_p setting for the AI model.
        include_quotes (bool): Whether to include quotes in the process.
    
    Returns:
        tuple: A tuple containing the reduced DataFrame, total codes count, and unique codes count.
    """
    combined_codes = pd.concat([df1, df2], ignore_index=True)
    
    if not include_quotes:
        codes_list = [
            {
                "code": row['code'],
                "description": row['description']
            }
            for _, row in combined_codes.iterrows()
        ]
    else:
        codes_list = [
            {
                "code": row['code'],
                "description": row['description'],
                "quote": row['quote']
            }
            for _, row in combined_codes.iterrows()
        ]
    
    reduced_codes = process_chunks(model, prompt, codes_list, model_temperature, model_top_p, include_quotes=include_quotes)

    if not reduced_codes:
        logger.error("Failed to process any chunks successfully")
        return None, None, None

    # Create a mapping of original codes to reduced codes
    code_mapping = {}
    for reduced_code in reduced_codes:
        for original_code in reduced_code.get('original_codes', [reduced_code['code']]):
            code_mapping[original_code] = reduced_code

    # Apply the mapping to the original combined_codes DataFrame
    reduced_rows = []
    for _, row in combined_codes.iterrows():
        if row['code'] in code_mapping:
            reduced_code = code_mapping[row['code']]
            new_row = {
                'code': reduced_code['code'],
                'description': reduced_code['description'],
                'merge_explanation': reduced_code.get('merge_explanation', ''),
                'original_code': row['code'],
                'quote': row['quote'],
                'source': row['source']
            }
            reduced_rows.append(new_row)
        else:
            logger.warning(f"Code not found in mapping: {row['code']}")
            # Add the original code as-is if it's not in the mapping
            new_row = {
                'code': row['code'],
                'description': row['description'],
                'merge_explanation': '',
                'original_code': row['code'],
                'quote': row['quote'],
                'source': row['source']
            }
            reduced_rows.append(new_row)

    reduced_df = pd.DataFrame(reduced_rows)

    total_codes = len(combined_codes)
    unique_codes = len(reduced_df['code'].unique())

    return reduced_df, total_codes, unique_codes

def process_files(selected_project, selected_files, model, prompt, model_temperature, model_top_p, include_quotes):
    """
    Process multiple files to reduce codes and track the reduction process.
    
    Args:
        selected_project (str): The name of the selected project.
        selected_files (list): A list of file paths to process.
        model (str): The name of the llm to use.
        prompt (str): The prompt to guide the llm in code reduction. 
        model_temperature (float): The temperature setting for the llm
        model_top_p (float): The top_p setting for the llm.
        include_quotes (bool): Whether to include quotes in the process.
    
    Returns:
        tuple: A tuple containing the final reduced (pandas) DataFrame and a DataFrame of reduction results.
    """
    logger.info(f"Starting to process files for project: {selected_project}")
    logger.info(f"Number of files to process: {len(selected_files)}")
    logger.info(f"Model: {model}, Temperature: {model_temperature}, Top P: {model_top_p}")
    logger.info(f"Include Quotes: {include_quotes}")

    reduced_df = None
    total_codes_list = []
    unique_codes_list = []
    cumulative_total = 0
    progress_bar = st.progress(0)
    status_message = st.empty()

    for i, file in enumerate(selected_files):
        status_message.info(f"Processing file {i+1}/{len(selected_files)}: {os.path.basename(file)}... please wait")
        logger.info(f"Processing file {i+1}/{len(selected_files)}: {file}")
        df = pd.read_csv(file)
        logger.info(f"File {file} read. Shape: {df.shape}")

        # Add source column if it doesn't exist
        if 'source' not in df.columns:
            df['source'] = os.path.basename(file)
            logger.info(f"Added 'source' column to DataFrame for file: {file}")
        
        file_total_codes = len(df)
        cumulative_total += file_total_codes
        logger.info(f"Cumulative total codes: {cumulative_total}")
        
        if reduced_df is None:
            reduced_df = df
            logger.info("First file processed, no reduction needed")
        else:
            logger.info(f"Comparing and reducing codes for file {i+1}")
            status_message.info(f"Comparing and reducing codes for file {i+1}/{len(selected_files)}...")
            reduced_df, _, _ = compare_and_reduce_codes(reduced_df, df, model, prompt, model_temperature, model_top_p, include_quotes)
            if reduced_df is None:
                logger.error(f"Failed to process file {file}. Skipping to the next file.")
                st.error(f"Failed to process file {file}. Skipping to the next file.")
                continue
        
        total_codes_list.append(cumulative_total)
        unique_codes = len(reduced_df['code'].unique())
        unique_codes_list.append(unique_codes)
        logger.info(f"After processing file {i+1}: Total codes = {cumulative_total}, Unique codes = {unique_codes}")
        
        progress = (i + 1) / len(selected_files)
        progress_bar.progress(progress)
        status_message.success(f"Processed file {i+1}/{len(selected_files)}: Total codes = {cumulative_total}, Unique codes = {unique_codes}")
        time.sleep(1)  # Add a small delay to allow the user to see the message
    
    # Save intermediate results
    results_df = pd.DataFrame({
        'total_codes': total_codes_list,
        'unique_codes': unique_codes_list
    })
    results_path = os.path.join(PROJECTS_DIR, selected_project, 'code_reduction_results.csv')
    results_df.to_csv(results_path, index=False)
    logger.info(f"Saved code reduction results to: {results_path}")
    
    logger.info("File processing completed")
    #status_message.success("Code reduction process completed successfully!")
    return reduced_df, results_df

@st.cache_data
def convert_df(df):
    """
    Convert a DataFrame to a CSV string.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
    
    Returns:
        bytes: The DataFrame as a CSV string encoded in UTF-8.
    """
    return df.to_csv().encode('utf-8')

def format_original_codes(original_codes):
    """
    Format the original codes string for display.
    
    Args:
        original_codes (str): A string representation of original codes.
    
    Returns:
        str: A formatted string of original codes.
    """
    try:
        codes = json.loads(original_codes)
        return ', '.join(codes) if isinstance(codes, list) else original_codes
    except json.JSONDecodeError:
        return original_codes

def main():
    """
    The main function that sets up the Streamlit interface for code reduction.
    """
    # Reset the text input message in session_state
    if 'current_prompt' in st.session_state:
        del st.session_state.current_prompt 

    st.header(":orange[Reduction of Codes]")

    # Instructions expander
    with st.expander("Instructions"):
        st.write("""
        The Reduction of Codes page is where you refine and consolidate the initial codes generated in the previous step. This process helps to identify patterns and reduce redundancy in your coding.
        """)

        # Create columns for layout for gifs and main points
        col1, col2, col3 = st.columns(3)

        # Display content in each column
        centered_column_with_number(col1, 1, process_text, process_gif)
        centered_column_with_number(col2, 2, compare_text, compare_gif)
        centered_column_with_number(col3, 3, merge_text, merge_gif)

        st.markdown(
            """
            <p style="font-size: 8px; color: gray; text-align: center;">
            <a href="https://www.flaticon.com/animated-icons" title="document animated icons" style="color: gray; text-decoration: none;">
            Animated icons created by Freepik - Flaticon
            </a>
            </p>
            """,
            unsafe_allow_html=True
        )

        st.subheader(":orange[1. Project and File Selection]")
        st.write("""
        - Select your project from the dropdown menu.
        - Once a project is selected, you'll see a list of files containing initial codes.
        - Choose the files you want to process. You can select individual files or use the "Select All" checkbox.
        """)

        st.subheader(":orange[2. LLM Settings]")
        st.write("""
        - Choose the AI model you want to use for code reduction.
        - Select a preset prompt or edit the provided prompt to guide the reduction process.
        - Adjust the model temperature and top_p values using the sliders. These parameters influence the AI's output.
        - Choose whether to include quotes in the LLM processing. This is off by default for data privacy.
        """)

        st.subheader(":orange[3. Processing and Results]")
        st.write("""
        - Select 'automatic' or 'incremental' processing (whether to pause between files and display incremental results)
        - Select 'include quotes' if you want to send the associated quotes to the LLM. This will provide more context for identifying highly similar codes, but also increases the API usage (and thus, cost and time)
        - Click the "Process" button to start the code reduction.
        - The system will analyze the selected files sequentially, comparing and merging similar codes.
        - A progress bar will show the status of the processing.
        - Once complete, you'll see:
        - A table of reduced codes with their descriptions, merged explanations, and associated quotes.
        - A "Code Reduction Results" table showing the number of total and unique codes for each processed file.
        - You can download both the reduced codes and the code reduction results as CSV files.
        """)

        st.subheader(":orange[4. Saved Reduced Codes]")
        st.write("""
        - At the bottom of the page, you'll find an expandable section showing previously processed reduced code files.
        - You can view, delete, or download these saved reduced codes.
        """)

        st.subheader(":orange[Key Features]")
        st.write(f"""
        - :orange[Automatic merging:] The AI identifies similar codes and combines them, providing explanations for the merges.
        - :orange[Quote preservation:] All quotes associated with the original codes are retained and linked to the reduced codes.
        - :orange[Tracking changes:] The system keeps track of how initial codes map to reduced codes, maintaining traceability.
        - :orange[Saturation analysis:] The code reduction results can be used to assess thematic saturation in your analysis. (see <a href="pages/5_💹_Saturation_Metric.py" target="_self">Saturation Metric 💹</a>).
        """, unsafe_allow_html=True)

        st.subheader(":orange[Tips]")
        st.write("""
        - Review the merged codes carefully to ensure the AI's decisions align with your understanding of the data.
        - If you're not satisfied with the reduction, you can adjust the prompt or model settings and reprocess the files.
        - :orange[Pay attention to the "Code Reduction Results" table.] A plateauing number of unique codes may indicate approaching saturation in your analysis.
        - Consider running the reduction process multiple times with different settings to compare results and ensure thorough analysis.
        """)

        st.info("Code reduction is a critical step in refining your analysis. It helps to consolidate your findings and prepare for the identification of overarching themes in the next stage.")

    st.subheader(":orange[Project & Data Selection]")
    
    projects = get_projects()
    
    # Initialize session state for selected project if it doesn't exist
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = "Select a project..."

    # Calculate the index for the selectbox
    project_options = ["Select a project..."] + projects
    if st.session_state.selected_project in project_options:
        index = project_options.index(st.session_state.selected_project)
    else:
        index = 0

    # Use selectbox with the session state as the default value
    selected_project = st.selectbox(
        "Select a project:", 
        project_options,
        index=index,
        key="project_selector",
        help = tooltips.project_tooltip
    )

    # Update session state when a new project is selected
    if selected_project != st.session_state.selected_project:
        st.session_state.selected_project = selected_project
        st.rerun()

    if selected_project != "Select a project...":
        project_files = get_project_files(selected_project, 'initial_codes')
        
        # File selection expander
        with st.expander("Select files to process", expanded=True):
            col1, col2 = st.columns([0.9, 0.2])
            select_all = col2.checkbox("Select All", value=True)
            
            file_checkboxes = {}
            for i, file in enumerate(project_files):
                col1, col2 = st.columns([0.9, 0.2])
                col1.write(file)
                file_checkboxes[file] = col2.checkbox(".", key=f"checkbox_{file}", value=select_all, label_visibility="hidden")
        
        selected_files = [os.path.join(PROJECTS_DIR, selected_project, 'initial_codes', file) for file, checked in file_checkboxes.items() if checked]

        st.divider()
        st.subheader(":orange[LLM Settings]")

        # Model selection
        azure_models = get_azure_models()
        model_options = default_models + azure_models + [f"graphia-llm:{m}" for m in graphia_llm_models]
        selected_model = st.selectbox("Select Model", model_options, help = tooltips.model_tooltip)

        max_temperature_value = 2.0 if selected_model.startswith('gpt') else 1.0
        
        # Load custom prompts
        custom_prompts = load_custom_prompts().get('Reduction of Codes', {})

        # Combine preset and custom prompts
        all_prompts = {**reduce_duplicate_codes_prompts, **custom_prompts}

        # Prompt selection
        selected_prompt = st.selectbox("Select a prompt:", list(all_prompts.keys()), help = tooltips.presets_tooltip)

        # Load selected prompt values
        selected_prompt_data = all_prompts[selected_prompt]
        prompt_input = selected_prompt_data["prompt"]
        model_temperature = selected_prompt_data["temperature"]
        model_top_p = selected_prompt_data["top_p"]
        include_quotes = False

        prompt_input = st.text_area("Edit prompt if needed:", value=prompt_input, height=200, help=tooltips.prompt_tooltip)
        
        # Model settings
        settings_col1, settings_col2 = st.columns([0.5, 0.5])
        with settings_col1:
            model_temperature = st.slider(label="Model Temperature", min_value=float(0), max_value=float(max_temperature_value), step=0.01, value=model_temperature, help=tooltips.model_temp_tooltip)
        with settings_col2:
            model_top_p = st.slider(label="Model Top P", min_value=float(0), max_value=float(1), step=0.01, value=model_top_p, help=tooltips.top_p_tooltip)

        include_quotes = st.checkbox(label = "Include Quotes", value=False, help='Choose whether to send quotes to the LLM during the code-reduction process. This setting is :orange[off] by default; if you do choose to include quotes, check you are adhering to data privacy policies')
        
        st.subheader(":orange[Processing Mode]")
        processing_mode = st.radio(
            "Choose processing mode:",
            ("Automatic", "Incremental"),
            help="Automatic processes all files at once. Incremental allows review after each file."
        )


        auto_save = AutoSaveResume(selected_project)
        progress = auto_save.load_progress()
        resume_data = None
        if progress:
            processed_files = progress['processed_files']
            saved_mode = progress.get('mode', 'Automatic')
            if saved_mode == processing_mode:
                st.warning("Previous unfinished progress found.")
                st.info(f"Processed files: {[os.path.basename(f) for f in processed_files]}")
                st.info(f"Remaining files: {[os.path.basename(f) for f in selected_files if f not in processed_files]}")
                resume = st.checkbox("Resume from last checkpoint", value=True, key="resume_checkbox")
                if resume:
                    resume_data = progress
                else:
                    # Only clear progress if the user chooses not to resume
                    auto_save.clear_progress()
            else:
                st.warning(f"Previous unfinished progress found in a different mode: '{saved_mode}'.")
                st.info(f"Processed files: {[os.path.basename(f) for f in processed_files]}")
                st.info(f"Remaining files: {[os.path.basename(f) for f in selected_files if f not in processed_files]}")

                # Provide options to the user
                choice = st.radio(
                    "What would you like to do?",
                    (
                        f"Resume previous progress in '{saved_mode}' mode",
                        f"Discard previous progress and start fresh in '{processing_mode}' mode"
                    ),
                    key="mode_switch_choice"
                )

                if choice == f"Resume previous progress in '{saved_mode}' mode":
                    # Switch processing mode back to saved mode and resume
                    processing_mode = saved_mode
                    resume_data = progress
                    st.info(f"Switching back to '{saved_mode}' mode to resume progress.")
                else:
                    # User chose to discard progress
                    auto_save.clear_progress()
                    st.info(f"Starting fresh in '{processing_mode}' mode.")

        if st.button("Process"):
            st.divider()
            st.subheader(":orange[Output]")
            with st.spinner("Reducing codes... this may take some time depending on the number of files and initial codes."):
                reduced_df, results_df, processed_files = process_files_with_autosave(
                    selected_project, selected_files, selected_model, prompt_input,
                    model_temperature, model_top_p, include_quotes, resume_data, mode=processing_mode
                )

                if reduced_df is not None:
                    # Match reduced codes to initial codes
                    status_message = st.empty()
                    status_message.info("Matching reduced codes to initial codes...")
                    initial_codes_directory = os.path.join(PROJECTS_DIR, selected_project, 'initial_codes')
                    updated_df = match_reduced_to_original_codes(reduced_df, initial_codes_directory)
                    amalgamated_df = amalgamate_duplicate_codes(updated_df)
                    amalgamated_df_for_display = amalgamated_df.copy()
                    amalgamated_df_for_display['quote'] = amalgamated_df_for_display['quote'].apply(format_quotes)
                    amalgamated_df_for_display['original_code'] = amalgamated_df_for_display['original_code'].apply(format_original_codes)

                    # Display results
                    st.write("Reduced Codes:")
                    st.write(amalgamated_df_for_display)
                    
                    # Display total vs processed vs unique codes
                    st.write("Code Reduction Results:")
                    st.write(results_df)

                    # Save reduction figures for ITS 
                    results_csv = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download code reduction results",
                        data=results_csv,
                        file_name="code_reduction_results.csv",
                        mime="text/csv"
                    )
                    
                    # Save reduced codes
                    status_message.info("Saving reduced codes...")
                    save_reduced_codes(selected_project, updated_df, 'expanded_reduced_codes')
                    saved_file_path = save_reduced_codes(selected_project, amalgamated_df, 'reduced_codes')
                    st.success(f"Reduced codes saved to {saved_file_path}")
                    
                    # Download buttons for reduced codes and results
                    csv = amalgamated_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download reduced codes",
                        data=csv,
                        file_name="reduced_codes.csv",
                        mime="text/csv"
                    )
                    
                    status_message.success("Code reduction process completed successfully!")

                    # Check if in incremental mode and more files to process
                    if processing_mode == 'Incremental' and len(selected_files) > len(processed_files):
                        remaining_files = len(selected_files) - len(processed_files)
                        st.warning(f"Processing paused after current file in incremental mode. {remaining_files} file(s) remaining. Click 'Process' to continue with the next file.")
                else:
                    status_message.error("Failed to reduce codes. Please check the logs for more information and try again.")

        # View previously processed files
        processed_files_list = get_processed_files(selected_project, 'reduced_codes')
        with st.expander("Saved Reduced Codes", expanded=False):
            for processed_file in processed_files_list:
                col1, col2 = st.columns([0.9, 0.1])
                col1.write(processed_file)
                if col2.button("Delete", key=f"delete_{processed_file}"):
                    os.remove(os.path.join(PROJECTS_DIR, selected_project, 'reduced_codes', processed_file))
                    st.success(f"Deleted {processed_file}")
                    st.rerun()
                
                df = pd.read_csv(os.path.join(PROJECTS_DIR, selected_project, 'reduced_codes', processed_file))
                df['quote'] = df['quote'].apply(format_quotes)
                df['original_code'] = df['original_code'].apply(format_original_codes)
                st.write(df)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"Download {processed_file}",
                    data=csv,
                    file_name=processed_file,
                    mime="text/csv"
                )

    else:
        st.write("Please select a project to continue. If you haven't set up a project yet, head over to the '🏠 Folder Set Up' page to get started.")

    manage_api_keys()

if __name__ == "__main__":
    main()