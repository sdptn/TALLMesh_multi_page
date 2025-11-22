# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 14:51:05 2024

@author: Stefano De Paoli - s.depaoli@abertay.ac.uk
"""
import streamlit as st
import os
import pandas as pd
import json
import re
from api_key_management import manage_api_keys, load_api_keys, load_azure_settings, get_azure_models, AZURE_SETTINGS_FILE
from prompts import initial_coding_prompts
from project_utils import get_projects, get_project_files, get_processed_files, PROJECTS_DIR
from llm_utils import llm_call, default_models, blablador_models # Ari Thomson added blablador models
import logging
import tooltips
import time
from instructions import initial_coding_instructions


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# function to load users own custom prompts
def load_custom_prompts():
    try:
        with open('custom_prompts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_uploaded_files(uploaded_files, project_name):
    data_folder = os.path.join(PROJECTS_DIR, project_name, 'data')
    saved_files = []
    for file in uploaded_files:
        file_path = os.path.join(data_folder, file.name)
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            saved_files.append(file.name)
    return saved_files

def save_initial_codes(project_name, file_name, df):
    initial_codes_folder = os.path.join(PROJECTS_DIR, project_name, 'initial_codes')
    os.makedirs(initial_codes_folder, exist_ok=True)
    
    file_name_stripped = str(os.path.splitext(file_name)[0])
    output_file_path = os.path.join(initial_codes_folder, f"{file_name_stripped}_initial_codes.csv")
    df.to_csv(output_file_path, index=False, encoding='utf-8')
    return output_file_path

def split_text(text, max_chunk_size=50000, overlap=1000):
    """Split the text into chunks of approximately max_chunk_size characters with overlap."""
    logger.info("Starting to split text into chunks.")
    
    chunks = []
    current_chunk = ""
    
    logger.info(f"Using max_chunk_size: {max_chunk_size} characters with {overlap} characters overlap.")
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    logger.info(f"Total number of sentences to process: {len(sentences)}")

    for i, sentence in enumerate(sentences):
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            logger.info(f"Chunk {len(chunks)} created with size {len(current_chunk.strip())} characters.")
            # Start the new chunk with the overlap from the previous chunk
            overlap_start = max(0, len(current_chunk) - overlap)
            current_chunk = current_chunk[overlap_start:] + sentence + " "
            logger.info(f"Starting a new chunk with sentence {i+1}, including {overlap} characters of overlap.")
    
    if current_chunk:
        chunks.append(current_chunk.strip())
        logger.info(f"Final chunk created with size {len(current_chunk.strip())} characters.")
    
    logger.info(f"Total number of chunks created: {len(chunks)}")
    return chunks

def split_text_blablador(text):


    #split the text based on the prompt that'll be used to stay below a speccifc tokenb count so that all propmpts are useable!


    return split_text()


def process_file(file_path, model, prompt, model_temperature, model_top_p, status_message):
    # Specify encoding to handle potential UnicodeDecodeError
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    status_message.info(f"Processing file: {os.path.basename(file_path)}")
    

    #for llama might need to chunk further but the default alias-large blablador model works fine

    chunks = split_text(content)

    all_codes = []
    
    status_message.info(f"File split into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        status_message.info(f"Processing chunk {i+1}/{len(chunks)} of {os.path.basename(file_path)}")
        chunk_prompt = f"{prompt}\n\nFile Content (Part {i+1}/{len(chunks)}):\n{chunk}"

        print("Call number: " + str(i+1)) #for console chekcing which we've sent
        chunk_response = llm_call(model, chunk_prompt, model_temperature, model_top_p)
        
        if chunk_response is None:
            logger.error(f"Failed to process chunk {i+1}/{len(chunks)}")
            status_message.warning(f"Failed to process chunk {i+1}/{len(chunks)}")
            continue

        try:
            json_output = json.loads(chunk_response)
            if isinstance(json_output, dict) and 'final_codes' in json_output:
                chunk_codes = json_output['final_codes']
                all_codes.extend(chunk_codes)
                status_message.info(f"Extracted {len(chunk_codes)} codes from chunk {i+1}")
            else:
                logger.warning(f"Unexpected JSON structure in chunk {i+1}")
                status_message.warning(f"Unexpected JSON structure in chunk {i+1}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON in response for chunk {i+1}")
            status_message.error(f"Failed to parse JSON in response for chunk {i+1}")
    
    if not all_codes:
        raise ValueError("No valid codes were extracted from any chunks")
    
    # Combine all codes from different chunks
    combined_output = {'final_codes': all_codes}
    status_message.success(f"Completed processing file: {os.path.basename(file_path)}")
    status_message.success(f"Total codes extracted: {len(all_codes)}")
    
    return json.dumps(combined_output)

# ==============================================================================
#                             MAIN STREAMLIT FUNCTION
# ==============================================================================

def main():
    # session_state persists through page changes so need to reset the text input message 
    if 'current_prompt' in st.session_state:
        del st.session_state.current_prompt 

    initial_coding_instructions()

    st.subheader(":orange[Project & Data Selection]")

    # Project selection
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
        # File upload
        uploaded_files = st.file_uploader("Upload additional files or select below", type=["txt"], accept_multiple_files=True)
        if uploaded_files:
            saved_files = save_uploaded_files(uploaded_files, selected_project)
            if saved_files:
                st.success(f"Files uploaded successfully: {', '.join(saved_files)}")
            else:
                st.info("No new files were uploaded. They may already exist in the project.")

        # File selection
        project_files = get_project_files(selected_project, 'data')
        processed_files = get_processed_files(selected_project, 'initial_codes')
        processed_file_names = [os.path.splitext(f)[0].replace('_initial_codes', '') for f in processed_files]
        
        with st.expander("Select files to process", expanded=True):
            col1, col2 = st.columns([0.9, 0.2])
            select_all = col2.checkbox("Select All", value=True)
            
            file_checkboxes = {}
            for i, file in enumerate(project_files):
                col1, col2 = st.columns([0.9, 0.2])
                col1.write(file)
                is_processed = file.replace('.txt', '') in processed_file_names
                if is_processed:
                    col2.warning("Already processed", icon="⚠️")
                else:
                    file_checkboxes[file] = col2.checkbox(".", key=f"checkbox_{file}", value=select_all, label_visibility="hidden")
        
        selected_files = [file for file, checked in file_checkboxes.items() if checked]
        
        st.divider()
        st.subheader(":orange[LLM Settings]")
        
        # Model selection
        azure_models = get_azure_models()
        model_options = default_models + azure_models + blablador_models # default models imported from llm_utils # Ari Thomson added, blablador models is also imported from llm_utils
        selected_model = st.selectbox("Select Model", model_options, help = tooltips.model_tooltip)
        
        # OpenAI & Anthropic Models have different max temperature settings (2 & 1, respectively)
        max_temperature_value = 2.0 if selected_model.startswith('gpt') else 1.0
        
        # Load custom prompts
        custom_prompts = load_custom_prompts().get('Initial Coding', {})

        # Combine preset and custom prompts
        all_prompts = {**initial_coding_prompts, **custom_prompts}

        # Prompt selection
        selected_prompt = st.selectbox("Select a prompt:", list(all_prompts.keys()), help = tooltips.presets_tooltip)

        # Load selected prompt values
        selected_prompt_data = all_prompts[selected_prompt]
        prompt_input = selected_prompt_data["prompt"]
        model_temperature = selected_prompt_data["temperature"]
        model_top_p = selected_prompt_data["top_p"]

        prompt_input = st.text_area("Edit prompt if needed:", value=prompt_input, height=200, help = tooltips.prompt_tooltip)
        settings_col1, settings_col2 = st.columns([0.5, 0.5])
        with settings_col1:
            model_temperature = st.slider(label="Model Temperature", min_value=float(0), max_value=float(max_temperature_value),step=0.01,value=model_temperature, help = tooltips.model_temp_tooltip)

        with settings_col2:
            model_top_p = st.slider(label="Model Top P", min_value=float(0), max_value=float(1),step=0.01,value=model_top_p, help = tooltips.top_p_tooltip)

        if st.button("Process"):
            st.divider()
            st.subheader(":orange[Output]")
            status_message = st.empty()
            status_message.info("Starting initial coding process. This may take some time depending on the number of files and their size...")
            prog_bar = st.progress(0)
            if selected_files and prompt_input:
                for i, file in enumerate(selected_files):
                    file_path = os.path.join(PROJECTS_DIR, selected_project, 'data', file)
                    try:
                        status_message.info(f"Processing file {i+1}/{len(selected_files)}: {file}")
                        processed_output = process_file(file_path, selected_model, prompt_input, model_temperature, model_top_p, status_message)
                        json_output = json.loads(processed_output)
                        df = pd.json_normalize(json_output['final_codes'])
                        df.columns = ['code', 'description', 'quote']
                        
                        with st.expander(f"Processed Output for {file}:", expanded=True):
                            st.write(df)
                        
                            # Save initial codes
                            saved_file_path = save_initial_codes(selected_project, file, df)
                            status_message.success(f"Initial codes saved to {saved_file_path}")
                        
                            # Add download button for each file's results
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label=f"Download initial codes for {str(os.path.splitext(file)[0])}",
                                data=csv,
                                file_name=f"{str(os.path.splitext(file)[0])}_initial_codes.csv",
                                mime="text/csv"
                            )
                        
                    except Exception as e:
                        status_message.error(f"Error processing {file}: {str(e)}")
                        logger.error(f"Error processing {file}: {str(e)}", exc_info=True)
                    progress = (i + 1) / len(selected_files)
                    prog_bar.progress(progress)
                    time.sleep(1)  # Add a small delay to allow the user to see the message
                
                status_message.success("Initial coding process completed successfully!")
            else:
                status_message.warning("Please select files and enter a prompt.")

        # View previously processed files
        processed_files = get_processed_files(selected_project, 'initial_codes')
        with st.expander("Saved Initial Codes", expanded=False):
            for processed_file in processed_files:
                col1, col2 = st.columns([0.9, 0.1])
                col1.write(processed_file)
                if col2.button("Delete", key=f"delete_{processed_file}"):
                    os.remove(os.path.join(PROJECTS_DIR, selected_project, 'initial_codes', processed_file))
                    st.success(f"Deleted {processed_file}")
                    st.rerun()
                
                df = pd.read_csv(os.path.join(PROJECTS_DIR, selected_project, 'initial_codes', processed_file))
                st.write(df)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"Download {processed_file}",
                    data=csv,
                    file_name=processed_file,
                    mime="text/csv"
                )
    else:
        st.write(f"Please select a project to continue. If you haven't set up a project yet, head over to the '🏠 Project Set Up' page to get started")

    # Call API key management function
    manage_api_keys()

if __name__ == "__main__":
    main()