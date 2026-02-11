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
from prompts import reduce_duplicate_codes_1_v_all
from llm_utils import llm_call, process_chunks, default_models, graphia_llm_models
import logging
import tooltips
import time
from ui_utils import centered_column_with_number, create_circle_number
import uuid
from time import sleep
import networkx as nx

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

# For 1 to All Reduction

def collect_all_initial_codes(selected_files):
    """
    Collects and normalizes all initial codes from all files into a single DataFrame.
    
    Args:
        selected_files (list): List of file paths to process
        
    Returns:
        pd.DataFrame: Master DataFrame containing all codes with added unique identifiers
        
    Raises:
        ValueError: If files cannot be read or required columns are missing
    """
    
    logger = logging.getLogger(__name__)
    
    # Initialize empty list to store all codes
    all_codes = []
    
    required_columns = {'code', 'description', 'quote'}
    
    for file_path in selected_files:
        try:
            df = pd.read_csv(file_path)
            
            # Verify required columns
            missing_cols = required_columns - set(df.columns)
            if missing_cols:
                raise ValueError(f"File {file_path} missing required columns: {missing_cols}")
            
            # Add source if not present
            if 'source' not in df.columns:
                df['source'] = os.path.basename(file_path)
            
            # Add unique identifier for each code
            df['code_id'] = [str(uuid.uuid4()) for _ in range(len(df))]

            df['original_code'] = df['code']  # Each code starts as its own original code
            
            all_codes.append(df)
            logger.info(f"Successfully processed {file_path} with {len(df)} codes")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise ValueError(f"Failed to process {file_path}: {str(e)}")
    
    if not all_codes:
        raise ValueError("No valid code files were processed")
    
    # Combine all DataFrames
    master_codes_df = pd.concat(all_codes, ignore_index=True)
    
    # Ensure all required columns exist
    for col in required_columns:
        if col not in master_codes_df.columns:
            raise ValueError(f"Required column {col} missing in final DataFrame")
    
    logger.info(f"Successfully created master codes DataFrame with {len(master_codes_df)} total codes")
    return master_codes_df

# Prompt for 1 to all approach, to be moved to prompt.py file after testing

def generate_comparison_prompt(target_code, comparison_codes, prompt, include_quotes=False):
    """
    Creates a prompt for the LLM to compare one code against many others.
    
    Args:
        target_code (dict): Dictionary containing the target code's information
        comparison_codes (list): List of dictionaries containing codes to compare against
        include_quotes (bool): Whether to include quotes in the comparison
        
    Returns:
        str: Formatted prompt for the LLM
        
    The function structures the prompt to elicit clear True/False responses for each comparison.
    """
    base_prompt = prompt

    # Format target code information
    target_quote = f',\n        "quote": "{target_code["quote"]}"' if include_quotes else ''
    
    # Format comparison codes
    comparison_text = []
    for code in comparison_codes:
        if include_quotes:
            comparison_text.append(
                f'{{"code_id": "{code["code_id"]}", '
                f'"code": "{code["code"]}", '
                f'"description": "{code["description"]}", '
                f'"quote": "{code["quote"]}"}}'
            )
        else:
            comparison_text.append(
                f'{{"code_id": "{code["code_id"]}", '
                f'"code": "{code["code"]}", '
                f'"description": "{code["description"]}"}}'
            )
    
    comparison_list = ',\n    '.join(comparison_text)
    
    # Format final prompt
    final_prompt = base_prompt % (
        target_code["code"],
        target_code["description"],
        target_quote,
        f'[\n    {comparison_list}\n]'
    )
    
    return final_prompt

# Function to iterate over all codes individually, generate prompt (above) and call LLM

def process_similarity_comparisons(master_codes_df, model, prompt, model_temperature, model_top_p, 
                                 include_quotes=False, resume_data=None):
    """
    Processes code comparisons by asking LLM to compare each code against all others at once.
    
    Args:
        master_codes_df (pd.DataFrame): DataFrame containing all codes to compare
        model (str): Name of the LLM model to use
        prompt (str): The prompt template for comparison
        model_temperature (float): Temperature setting for the LLM
        model_top_p (float): Top P setting for the LLM
        include_quotes (bool): Whether to include quotes in comparisons
        resume_data (dict): Data from previous interrupted run
        
    Returns:
        dict: Similarity results containing all comparison outcomes
    """
    logger = logging.getLogger(__name__)
    
    def initialize_similarity_results(resume_data):
        """Initialize or resume similarity results tracking."""
        if resume_data and 'similarity_results' in resume_data:
            return resume_data['similarity_results']
        return {code_id: {'similar_codes': [], 'comparison_status': False} 
                for code_id in master_codes_df['code_id']}
    
    def process_comparison_response(response_text, target_code_id):
        """Process and validate LLM response for comparisons."""
        try:
            response_json = json.loads(response_text)
            comparisons = response_json.get('comparisons', {})
            
            # Validate response format
            if not isinstance(comparisons, dict):
                logger.error(f"Invalid response format for {target_code_id}: {response_text}")
                return None
                
            return comparisons
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {target_code_id}: {str(e)}")
            return None
    
    # Initialize similarity results
    similarity_results = initialize_similarity_results(resume_data)
    total_codes = len(master_codes_df)
    
    # Create progress bar and status message
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process each code against all others
    for idx, target_code in master_codes_df.iterrows():
        target_code_id = target_code['code_id']
        
        # Skip if already processed
        if similarity_results[target_code_id]['comparison_status']:
            continue
            
        # Convert target code to dict for prompt generation
        target_code_dict = target_code.to_dict()
        
        # Get all other codes for comparison
        comparison_codes = master_codes_df[master_codes_df['code_id'] != target_code_id]
        
        # Generate prompt comparing target code against all others at once
        comparison_prompt = generate_comparison_prompt(
            target_code_dict,
            [code.to_dict() for _, code in comparison_codes.iterrows()],
            prompt,
            include_quotes
        )
        
        # Make API call with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = llm_call(model, comparison_prompt, model_temperature, model_top_p)
                comparison_results = process_comparison_response(response, target_code_id)
                
                if comparison_results is not None:
                    # Update similarity results
                    for compared_id, is_similar in comparison_results.items():
                        if is_similar:
                            similarity_results[target_code_id]['similar_codes'].append(compared_id)
                            similarity_results[compared_id]['similar_codes'].append(target_code_id)
                    break
                
            except Exception as e:
                logger.error(f"Error in API call: {str(e)}")
                if attempt < max_retries - 1:
                    sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        # Mark this code as completely processed
        similarity_results[target_code_id]['comparison_status'] = True
        
        # Update progress
        progress = (idx + 1) / total_codes
        progress_bar.progress(progress)
        status_text.text(f"Processing code {idx + 1}/{total_codes}")
        
        # Save intermediate results every 5 codes
        if idx % 5 == 0:
            st.session_state['intermediate_results'] = {
                'similarity_results': similarity_results,
                'last_processed_idx': idx
            }
    
    progress_bar.empty()
    status_text.empty()
    
    return similarity_results

def reduce_based_on_similarities(similarity_results, master_codes_df, model, 
                               model_temperature, model_top_p, include_quotes=False):
    """
    Creates reduced codes based on similarity comparison results with enhanced debugging.
    """
    logger = logging.getLogger(__name__)
    
    def log_group_details(group_idx, group, group_codes):
        """Log detailed information about each group being processed."""
        logger.info(f"\nProcessing group {group_idx}")
        logger.info(f"Group size: {len(group)}")
        logger.info("Group code IDs: " + ", ".join(group))
        logger.info("Original codes in group:")
        for _, code in group_codes.iterrows():
            logger.info(f"  Code ID: {code['code_id']}")
            logger.info(f"    Code: {code['code']}")
            logger.info(f"    Original code: {code.get('original_code', 'Not found')}")

    def generate_merge_prompt(codes_to_merge):
        """Generate prompt for LLM to create merged code details."""
        merge_prompt = """Create a merged code from the following similar codes. Provide:
            1. A concise name for the merged code (maximum 6 words)
            2. A detailed description (up to 25 words) explaining the merged code's meaning
            3. A brief explanation (max 50 words) of why these codes were merged

            The codes to merge are:
            {codes}

            Format the response as a JSON object with this structure:
            {{
                "merged_code": {{
                    "code": "name of merged code",
                    "description": "merged description",
                    "merge_explanation": "explanation of merge"
                }}
            }}

            Important! Your response must be a valid JSON object with no additional text."""
        
        codes_text = []
        for _, code in codes_to_merge.iterrows():
            code_text = (f'Code ID: {code["code_id"]}\n'
                        f'Code: "{code["code"]}"\n'
                        f'Description: "{code["description"]}"\n'
                        f'Original Code: "{code.get("original_code", "Not found")}"')
            if include_quotes and 'quote' in code:
                code_text += f'\nQuote: "{code["quote"]}"'
            codes_text.append(code_text)
        
        return merge_prompt.format(codes='\n\n'.join(codes_text))

    def find_code_groups():
        """Use network analysis to find groups of similar codes."""
        G = nx.Graph()
        
        # Add edges for similar codes
        for code_id, data in similarity_results.items():
            for similar_code_id in data['similar_codes']:
                G.add_edge(code_id, similar_code_id)
        
        # Find connected components (groups of similar codes)
        groups = list(nx.connected_components(G))
        logger.info(f"\nFound {len(groups)} code groups")
        return groups

    # Initialize results DataFrame with required columns
    reduced_codes = []
    
    # Find groups of similar codes
    code_groups = find_code_groups()
    
    # Process each group
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, group in enumerate(code_groups):
        status_text.text(f"Processing group {idx + 1}/{len(code_groups)}")
        progress_bar.progress((idx + 1) / len(code_groups))
        
        # Get codes in this group
        group_codes = master_codes_df[master_codes_df['code_id'].isin(group)]
        log_group_details(idx, group, group_codes)
        
        if len(group_codes) > 1:
            # Generate merged code details using LLM
            merge_prompt = generate_merge_prompt(group_codes)
            logger.info("\nGenerated merge prompt:")
            logger.info(merge_prompt)
            
            try:
                response = llm_call(model, merge_prompt, model_temperature, model_top_p)
                logger.info("\nLLM Response:")
                logger.info(response)
                
                merged_details = json.loads(response)['merged_code']
                
                # Track all original codes from the group
                all_original_codes = []
                for _, code in group_codes.iterrows():
                    # If the code has original_code as JSON string, parse it
                    if isinstance(code.get('original_code'), str):
                        try:
                            original_codes = json.loads(code['original_code'])
                            if isinstance(original_codes, list):
                                all_original_codes.extend(original_codes)
                            else:
                                all_original_codes.append(original_codes)
                        except json.JSONDecodeError:
                            all_original_codes.append(code['original_code'])
                    else:
                        # If original_code is not a JSON string, use the code itself
                        all_original_codes.append(code['code'])
                
                logger.info("\nCollected original codes:")
                logger.info(all_original_codes)
                
                # Create reduced code entry
                reduced_code = {
                    'code': merged_details['code'],
                    'description': merged_details['description'],
                    'merge_explanation': merged_details['merge_explanation'],
                    'original_code': json.dumps(all_original_codes),
                    'quote': json.dumps([
                        {'text': row['quote'], 'source': row['source']}
                        for _, row in group_codes.iterrows()
                    ]),
                    'source': ', '.join(group_codes['source'].unique())
                }
                
                logger.info("\nCreated reduced code:")
                logger.info(json.dumps(reduced_code, indent=2))
                
            except Exception as e:
                logger.error(f"\nError merging codes in group {idx}: {str(e)}")
                logger.error(f"Response that caused error: {response if 'response' in locals() else 'No response'}")
                # If merge fails, use first code as fallback
                first_code = group_codes.iloc[0]
                reduced_code = {
                    'code': first_code['code'],
                    'description': first_code['description'],
                    'merge_explanation': 'Merge failed - using original code',
                    'original_code': json.dumps([first_code['code']]),
                    'quote': json.dumps([{'text': first_code['quote'], 'source': first_code['source']}]),
                    'source': first_code['source']
                }
                logger.info("\nUsing fallback code:")
                logger.info(json.dumps(reduced_code, indent=2))
        else:
            # Single code - no merging needed
            single_code = group_codes.iloc[0]
            reduced_code = {
                'code': single_code['code'],
                'description': single_code['description'],
                'merge_explanation': '',
                'original_code': json.dumps([single_code['code']]),
                'quote': json.dumps([{'text': single_code['quote'], 'source': single_code['source']}]),
                'source': single_code['source']
            }
            logger.info("\nSingle code (no merge needed):")
            logger.info(json.dumps(reduced_code, indent=2))
        
        reduced_codes.append(reduced_code)
    
    progress_bar.empty()
    status_text.empty()
    
    # Create final DataFrame with required columns in correct order
    reduced_df = pd.DataFrame(reduced_codes)
    
    # Ensure all required columns exist and are in the correct order
    required_columns = ['code', 'description', 'merge_explanation', 'original_code', 'quote', 'source']
    for col in required_columns:
        if col not in reduced_df.columns:
            reduced_df[col] = ''
    
    reduced_df = reduced_df[required_columns]
    
    logger.info("\nFinal reduced DataFrame:")
    logger.info(f"Shape: {reduced_df.shape}")
    logger.info("Sample of reduced codes:")
    logger.info(reduced_df.head().to_string())
    
    return reduced_df


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

def process_files_with_autosave(selected_project, selected_files, model, prompt, 
                              model_temperature, model_top_p, include_quotes, 
                              resume_data=None, mode='Automatic'):
    """
    Process files using the similarity-based approach with auto-save functionality.
    
    Args:
        selected_project (str): Name of the project
        selected_files (list): List of files to process
        model (str): Name of the LLM model to use
        prompt (str): The prompt template for comparison
        model_temperature (float): Temperature setting for the LLM
        model_top_p (float): Top P setting for the LLM
        include_quotes (bool): Whether to include quotes in processing
        resume_data (dict): Data from previous interrupted run
        mode (str): Processing mode ('Automatic' or 'Incremental')
        
    Returns:
        tuple: (reduced_df, results_df, processed_files) in format expected by downstream processes
    """
    auto_save = AutoSaveResume(selected_project)
    
    # Initialize or resume progress tracking
    if resume_data:
        progress_data = resume_data
        master_codes_df = pd.read_json(progress_data['master_codes_df'])
        similarity_results = progress_data['similarity_results']
        processed_files = progress_data['processed_files']
        total_codes_list = progress_data.get('total_codes_list', [])
        unique_codes_list = progress_data.get('unique_codes_list', [])
        cumulative_total = progress_data.get('cumulative_total', 0)
    else:
        processed_files = []
        total_codes_list = []
        unique_codes_list = []
        cumulative_total = 0
        
        # Collect all initial codes
        status_message = st.empty()
        status_message.info("Collecting codes from all files...")
        try:
            master_codes_df = collect_all_initial_codes(selected_files)
            similarity_results = None
        except Exception as e:
            logger.error(f"Error collecting initial codes: {str(e)}")
            st.error(f"Error collecting initial codes: {str(e)}")
            return None, None, []
    
    try:
        # Process similarity comparisons if not already done
        if similarity_results is None:
            status_message = st.empty()
            status_message.info("Processing code comparisons...")
            similarity_results = process_similarity_comparisons(
                master_codes_df=master_codes_df,
                model=model,
                prompt=prompt,
                model_temperature=model_temperature,
                model_top_p=model_top_p,
                include_quotes=include_quotes,
                resume_data=resume_data
            )
        
        # Save intermediate results
        progress_data = {
            'master_codes_df': master_codes_df.to_json(),
            'similarity_results': similarity_results,
            'processed_files': processed_files,
            'total_codes_list': total_codes_list,
            'unique_codes_list': unique_codes_list,
            'cumulative_total': cumulative_total,
            'mode': mode
        }
        auto_save.save_progress(
            processed_files=processed_files,
            reduced_df=pd.DataFrame(),  # Placeholder until reduction complete
            total_codes_list=total_codes_list,
            unique_codes_list=unique_codes_list,
            cumulative_total=cumulative_total,
            mode=mode
        )
        
        # Reduce codes based on similarities
        status_message = st.empty()
        status_message.info("Reducing codes based on similarities...")
        reduced_df = reduce_based_on_similarities(
            similarity_results=similarity_results,
            master_codes_df=master_codes_df,
            model=model,
            model_temperature=model_temperature,
            model_top_p=model_top_p,
            include_quotes=include_quotes
        )

        logger.info("Original codes before saving:")
        for _, row in reduced_df.iterrows():
            logger.info(f"Code: {row['code']}")
            logger.info(f"Original codes: {row['original_code']}")
        
        # Update progress tracking
        processed_files = selected_files
        cumulative_total = len(master_codes_df)
        total_codes_list.append(cumulative_total)
        unique_codes = len(reduced_df['code'].unique())
        unique_codes_list.append(unique_codes)
        
        # Create results DataFrame
        results_df = pd.DataFrame({
            'total_codes': total_codes_list,
            'unique_codes': unique_codes_list
        })
        
        # Save final results
        results_path = os.path.join(PROJECTS_DIR, selected_project, 'code_reduction_results.csv')
        results_df.to_csv(results_path, index=False)
        logger.info(f"Saved code reduction results to: {results_path}")
        
        # Clear progress file after successful completion
        auto_save.clear_progress()
        
        return reduced_df, results_df, processed_files
        
    except Exception as e:
        logger.error(f"Error in code reduction process: {str(e)}")
        st.error(f"Error in code reduction process: {str(e)}")
        return None, None, []
    

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
        help=tooltips.project_tooltip
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
        
        selected_files = [os.path.join(PROJECTS_DIR, selected_project, 'initial_codes', file) 
                         for file, checked in file_checkboxes.items() if checked]

        st.divider()
        st.subheader(":orange[LLM Settings]")

        # Model selection
        azure_models = get_azure_models()
        model_options = default_models + azure_models + graphia_llm_models
        selected_model = st.selectbox("Select Model", model_options, help=tooltips.model_tooltip)

        max_temperature_value = 2.0 if selected_model.startswith('gpt') else 1.0
        
        
        # Load custom prompts (kept for compatibility)
        custom_prompts = load_custom_prompts().get('Reduction of Codes', {})
        all_prompts = {**reduce_duplicate_codes_1_v_all, **custom_prompts}
        selected_prompt = st.selectbox("Select a prompt:", list(all_prompts.keys()), help=tooltips.presets_tooltip)
        selected_prompt_data = all_prompts[selected_prompt]
        prompt_input = selected_prompt_data["prompt"]
        model_temperature = selected_prompt_data["temperature"]
        model_top_p = selected_prompt_data["top_p"]

        prompt_input = st.text_area(
            "Edit prompt if needed:",
            value=prompt_input,
            height=200,
            help="Note: In the new comparison approach, this prompt is used for merging similar codes."
        )
        
        # Model settings
        settings_col1, settings_col2 = st.columns([0.5, 0.5])
        with settings_col1:
            model_temperature = st.slider(
                label="Model Temperature",
                min_value=float(0),
                max_value=float(max_temperature_value),
                step=0.01,
                value=model_temperature,
                help=tooltips.model_temp_tooltip
            )
        with settings_col2:
            model_top_p = st.slider(
                label="Model Top P",
                min_value=float(0),
                max_value=float(1),
                step=0.01,
                value=model_top_p,
                help=tooltips.top_p_tooltip
            )
        

        include_quotes = st.checkbox(
            label="Include Quotes",
            value=False,
            help='Include quotes in code comparisons. This provides more context but increases API usage.'
        )
        
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
                    selected_project=selected_project,
                    selected_files=selected_files,
                    model=selected_model,
                    prompt=prompt_input,
                    model_temperature=model_temperature,
                    model_top_p=model_top_p,
                    include_quotes=include_quotes,
                    resume_data=resume_data if 'resume_data' in locals() else None,
                    mode=processing_mode
                ) 

                if reduced_df is not None:
                    # Match reduced codes to initial codes
                    status_message = st.empty()
                    status_message.info("Finalizing reduced codes...")
                    amalgamated_df = amalgamate_duplicate_codes(reduced_df)
                    amalgamated_df_for_display = amalgamated_df.copy()
                    amalgamated_df_for_display['quote'] = amalgamated_df_for_display['quote'].apply(format_quotes)
                    amalgamated_df_for_display['original_code'] = amalgamated_df_for_display['original_code'].apply(format_original_codes)

                    # Display results
                    st.write("Reduced Codes:")
                    st.write(amalgamated_df_for_display)
                    
                    # Display intermediate results
                    st.write("Code Reduction Results:")
                    st.write(results_df)
                    
                    # Save reduced codes
                    status_message.info("Saving reduced codes...")
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
                    
                    results_csv = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download code reduction results",
                        data=results_csv,
                        file_name="code_reduction_results.csv",
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