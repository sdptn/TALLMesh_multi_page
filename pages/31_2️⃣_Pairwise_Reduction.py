# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 2025

@author: Based on Stefano De Paoli's work - adapted for pairwise reduction

This script is part of the TALLMesh multi-page application for qualitative data analysis.
It focuses on pairwise reduction of initial codes generated in the previous step of the analysis process.
The main purpose is to refine and consolidate codes by comparing sets of codes from different files
in a pairwise fashion, reducing the number of API calls compared to the 1-vs-all approach.
"""

import os
import streamlit as st
import pandas as pd
import json
import re
from api_key_management import manage_api_keys, load_api_keys, load_azure_settings, get_azure_models, AZURE_SETTINGS_FILE
from project_utils import get_projects, get_project_files, get_processed_files, PROJECTS_DIR
from prompts import reduce_duplicate_codes_pairwise
from llm_utils import llm_call, default_models, blablador_models
import logging
import tooltips
import time
from ui_utils import centered_column_with_number
import uuid
from time import sleep
from instructions import pairwise_reduce_codes_instructions
from text_processing import generate_comparison_prompt, validate_json_response


logo = "pages/static/tmeshlogo.png"
st.logo(logo)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_expanded_reduced_codes(project_name, df):
    """Create expanded format required by visualizations"""
    expanded_rows = []
    
    for _, row in df.iterrows():
        # Parse JSON arrays
        original_codes = json.loads(row['original_code'])
        quotes = json.loads(row['quote'])
        
        # Create a row for each original code and quote combination
        for orig_code in original_codes:
            for quote_obj in quotes:
                expanded_rows.append({
                    'code': row['code'],
                    'description': row['description'],
                    'original_code': orig_code,
                    'quote': quote_obj['text'],
                    'source': quote_obj['source']
                })
    
    expanded_df = pd.DataFrame(expanded_rows)
    
    # Save to expanded_reduced_codes folder
    output_folder = os.path.join(PROJECTS_DIR, project_name, 'expanded_pairwise_reduced_codes')
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"expanded_pairwise_reduced_codes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv")
    expanded_df.to_csv(output_file, index=False)
    return output_file

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def collect_codes_from_files(file_paths):
    """
    Collect codes from multiple files and organize them by file
    """
    codes_by_file = {}
    
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        file_name = os.path.basename(file_path)
        
        if 'source' not in df.columns:
            df['source'] = file_name
        
        df['code_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        df['original_code'] = df['code']
        
        codes_by_file[file_name] = df
        
    return codes_by_file

def generate_pairwise_comparison_prompt(file1_codes, file2_codes, prompt, include_quotes=False):
    """
    Generate a prompt for pairwise comparison between two sets of codes.
    """
    base_prompt = prompt
    
    # Prepare file 1 codes
    file1_list = []
    for _, code in file1_codes.iterrows():
        code_dict = {
            "code": code["code"],
            "description": code["description"],
            "code_id": code["code_id"]
        }
        if include_quotes:
            code_dict["quote"] = code["quote"]
        file1_list.append(json.dumps(code_dict))
    
    # Prepare file 2 codes
    file2_list = []
    for _, code in file2_codes.iterrows():
        code_dict = {
            "code": code["code"],
            "description": code["description"],
            "code_id": code["code_id"]
        }
        if include_quotes:
            code_dict["quote"] = code["quote"]
        file2_list.append(json.dumps(code_dict))
    
    file1_json = ',\n    '.join(file1_list)
    file2_json = ',\n    '.join(file2_list)
    
    final_prompt = base_prompt % (
        f'[\n    {file1_json}\n]',
        f'[\n    {file2_json}\n]'
    )
    
    return final_prompt

def process_pairwise_comparisons(codes_by_file, file_pairs, model, prompt, 
                                model_temperature, model_top_p, include_quotes=False):
    """
    Process pairwise comparisons between files.
    """
    similarity_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_pairs = len(file_pairs)
    
    for idx, (file1, file2) in enumerate(file_pairs):
        status_text.text(f"Comparing {file1} with {file2}...")
        
        file1_codes = codes_by_file[file1]
        file2_codes = codes_by_file[file2]
        
        comparison_prompt = generate_pairwise_comparison_prompt(
            file1_codes, file2_codes, prompt, include_quotes
        )
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = llm_call(model, comparison_prompt, model_temperature, model_top_p)
                
                parsed_response = validate_json_response(response)
                if parsed_response is None:
                    logger.error("Failed to parse LLM response as valid JSON")
                    continue
                
                # Process the pairwise comparisons
                comparisons = parsed_response.get('comparisons', [])
                
                for comparison in comparisons:
                    file1_code_id = comparison.get('file1_code_id')
                    file2_code_id = comparison.get('file2_code_id')
                    
                    if file1_code_id and file2_code_id:
                        # Find the actual codes
                        file1_code_row = file1_codes[file1_codes['code_id'] == file1_code_id]
                        file2_code_row = file2_codes[file2_codes['code_id'] == file2_code_id]
                        
                        if not file1_code_row.empty and not file2_code_row.empty:
                            similarity_pair = {
                                'code1': file1_code_row.iloc[0]['code'],
                                'code1_id': file1_code_id,
                                'code1_file': file1,
                                'code2': file2_code_row.iloc[0]['code'],
                                'code2_id': file2_code_id,
                                'code2_file': file2
                            }
                            similarity_results.append(similarity_pair)
                
                break
            except Exception as e:
                logger.error(f"Error processing comparison (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    sleep(2 ** attempt)
                else:
                    raise
        
        # Update progress
        progress_bar.progress((idx + 1) / total_pairs)
    
    progress_bar.empty()
    status_text.empty()
    return similarity_results

def reduce_based_on_similarities(similarity_results, codes_by_file, model, model_temperature, model_top_p, include_quotes=False, include_merge_explanation=True):
    """
    Reduce codes based on pairwise similarities.
    """
    logger = logging.getLogger(__name__)
    
    # Combine all codes into a single dataframe with file tracking
    all_codes = []
    for file_name, df in codes_by_file.items():
        df['file_name'] = file_name
        all_codes.append(df)
    master_codes_df = pd.concat(all_codes, ignore_index=True)
    
    def find_code_groups():
        """Find groups of similar codes based on similarity results"""
        code_groups = {}
        
        # Build a graph of similarities
        for result in similarity_results:
            code1_id = result['code1_id']
            code2_id = result['code2_id']
            
            # Find which group each code belongs to
            group1 = None
            group2 = None
            
            for group_id, group_codes in code_groups.items():
                if code1_id in group_codes:
                    group1 = group_id
                if code2_id in group_codes:
                    group2 = group_id
            
            if group1 is None and group2 is None:
                # Create new group
                new_group_id = str(uuid.uuid4())
                code_groups[new_group_id] = {code1_id, code2_id}
            elif group1 is not None and group2 is None:
                # Add code2 to group1
                code_groups[group1].add(code2_id)
            elif group1 is None and group2 is not None:
                # Add code1 to group2
                code_groups[group2].add(code1_id)
            elif group1 != group2:
                # Merge groups
                code_groups[group1].update(code_groups[group2])
                del code_groups[group2]
        
        # Add ungrouped codes as single-code groups
        all_code_ids = set(master_codes_df['code_id'])
        grouped_code_ids = set()
        for group in code_groups.values():
            grouped_code_ids.update(group)
        
        for ungrouped_id in all_code_ids - grouped_code_ids:
            code_groups[str(uuid.uuid4())] = {ungrouped_id}
        
        return list(code_groups.values())
    
    def generate_merge_prompt(codes_to_merge, include_merge_explanation):
        """Generate prompt for merging codes"""
        if include_merge_explanation:
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
        else:
            merge_prompt = """Create a merged code from the following similar codes. Provide:
                1. A concise name for the merged code (maximum 6 words)
                2. A detailed description (up to 25 words) explaining the merged code's meaning

                The codes to merge are:
                {codes}

                Format the response as a JSON object with this structure:
                {{
                    "merged_code": {{
                        "code": "name of merged code",
                        "description": "merged description"
                    }}
                }}

                Important! Your response must be a valid JSON object with no additional text."""

        codes_text = []
        for _, code_row in codes_to_merge.iterrows():
            code_text = (f'Code ID: {code_row["code_id"]}\n'
                         f'Code: "{code_row["code"]}"\n'
                         f'Description: "{code_row["description"]}"\n'
                         f'Source File: "{code_row["file_name"]}"')
            if include_quotes and 'quote' in code_row:
                code_text += f'\nQuote: "{code_row["quote"]}"'
            codes_text.append(code_text)

        return merge_prompt.format(codes='\n\n'.join(codes_text))
    
    reduced_codes = []
    code_groups = find_code_groups()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, group in enumerate(code_groups):
        status_text.text(f"Processing group {idx + 1}/{len(code_groups)}")
        progress_bar.progress((idx + 1) / len(code_groups))
        
        group_codes = master_codes_df[master_codes_df['code_id'].isin(group)]
        
        if len(group_codes) > 1:
            merge_prompt = generate_merge_prompt(group_codes, include_merge_explanation)
            try:
                response = llm_call(model, merge_prompt, model_temperature, model_top_p)
                merged_details = json.loads(response)['merged_code']
                time.sleep(1)
                
                if 'merge_explanation' not in merged_details:
                    merged_details['merge_explanation'] = ""
                
                # Collect all original codes
                all_original_codes = []
                seen_codes = set()
                for _, code in group_codes.iterrows():
                    if isinstance(code.get('original_code'), str):
                        try:
                            original_codes = json.loads(code['original_code'])
                            if isinstance(original_codes, list):
                                for orig_code in original_codes:
                                    if orig_code not in seen_codes:
                                        all_original_codes.append(orig_code)
                                        seen_codes.add(orig_code)
                            else:
                                if original_codes not in seen_codes:
                                    all_original_codes.append(original_codes)
                                    seen_codes.add(original_codes)
                        except json.JSONDecodeError:
                            if code['original_code'] not in seen_codes:
                                all_original_codes.append(code['original_code'])
                                seen_codes.add(code['original_code'])
                    else:
                        if code['code'] not in seen_codes:
                            all_original_codes.append(code['code'])
                            seen_codes.add(code['code'])
                
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
            except Exception as e:
                logger.error(f"Error merging codes in group {idx}: {str(e)}")
                # Fallback: use first code as representative
                fallback_code = group_codes.iloc[0]
                reduced_code = {
                    'code': fallback_code['code'],
                    'description': fallback_code['description'],
                    'merge_explanation': 'Merge failed - using original code',
                    'original_code': json.dumps([code['code'] for _, code in group_codes.iterrows()]),
                    'quote': json.dumps([
                        {'text': row['quote'], 'source': row['source']}
                        for _, row in group_codes.iterrows()
                    ]),
                    'source': ', '.join(group_codes['source'].unique())
                }
        else:
            # Single code, no merge needed
            single_code = group_codes.iloc[0]
            reduced_code = {
                'code': single_code['code'],
                'description': single_code['description'],
                'merge_explanation': '',
                'original_code': json.dumps([single_code['code']]),
                'quote': json.dumps([{'text': single_code['quote'], 'source': single_code['source']}]),
                'source': single_code['source']
            }
        
        reduced_codes.append(reduced_code)
    
    progress_bar.empty()
    status_text.empty()
    
    reduced_df = pd.DataFrame(reduced_codes)
    required_columns = ['code', 'description', 'merge_explanation', 'original_code', 'quote', 'source']
    for col in required_columns:
        if col not in reduced_df.columns:
            reduced_df[col] = ''
    reduced_df = reduced_df[required_columns]
    
    return reduced_df

def generate_file_pairs(file_names, mode='all_pairs'):
    """
    Generate pairs of files for comparison.
    
    Args:
        file_names: List of file names
        mode: 'all_pairs' for all possible pairs, 'sequential' for sequential pairs
    
    Returns:
        List of tuples (file1, file2)
    """
    pairs = []
    
    if mode == 'all_pairs':
        # Compare each file with every other file (no duplicates)
        for i in range(len(file_names)):
            for j in range(i + 1, len(file_names)):
                pairs.append((file_names[i], file_names[j]))
    elif mode == 'sequential':
        # Compare each file only with the next file
        for i in range(len(file_names) - 1):
            pairs.append((file_names[i], file_names[i + 1]))
    
    return pairs

def amalgamate_duplicate_codes(df):
    """Amalgamate codes with the same name"""
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
    try:
        amalgamated_df = df.groupby('code').agg({
            'description': 'first',
            'merge_explanation': 'first',
            'original_code': lambda x: sum((json.loads(item) if isinstance(item, str) and item.strip().startswith('[') else [item] for item in x), []),
            'quote': lambda x: [{'text': q, 'source': s} for q, s in zip(x, df.loc[x.index, 'source'])],
            'source': lambda x: list(x)
        }).reset_index()

        amalgamated_df['original_code'] = amalgamated_df['original_code'].apply(json.dumps)
        amalgamated_df['quote'] = amalgamated_df['quote'].apply(json.dumps)
        amalgamated_df['source'] = amalgamated_df['source'].apply(lambda x: ', '.join(set(x)))

        return amalgamated_df
    except Exception as e:
        logger.error(f"Error in amalgamate_duplicate_codes: {str(e)}")
        return None

def save_reduced_codes(project_name, df, folder):
    """Save reduced codes to CSV file"""
    reduced_codes_folder = os.path.join(PROJECTS_DIR, project_name, folder)
    os.makedirs(reduced_codes_folder, exist_ok=True)
    output_file_path = os.path.join(reduced_codes_folder, f"pairwise_reduced_codes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(output_file_path, index=False, encoding='utf-8')
    return output_file_path

def format_quotes(quotes_json):
    """Format quotes for display"""
    try:
        quotes = json.loads(quotes_json)
        formatted_quotes = "\n".join(f"{quote['text']} (Source: {quote['source']})" for quote in quotes)
        return formatted_quotes
    except (json.JSONDecodeError, KeyError, TypeError):
        return quotes_json

def format_original_codes(original_codes):
    """Format original codes for display"""
    try:
        codes = json.loads(original_codes)
        return ', '.join(codes) if isinstance(codes, list) else original_codes
    except json.JSONDecodeError:
        return original_codes

def load_custom_prompts():
    """Load custom prompts from JSON file"""
    try:
        with open('custom_prompts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ==============================================================================
#                             MAIN STREAMLIT FUNCTION
# ==============================================================================

def main():
    if 'current_prompt' in st.session_state:
        del st.session_state.current_prompt 

    pairwise_reduce_codes_instructions()

    st.subheader(":orange[Project & Data Selection]")
    projects = get_projects()
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = "Select a project..."
    project_options = ["Select a project..."] + projects
    if st.session_state.selected_project in project_options:
        index = project_options.index(st.session_state.selected_project)
    else:
        index = 0

    selected_project = st.selectbox(
        "Select a project:", 
        project_options,
        index=index,
        key="project_selector",
        help=tooltips.project_tooltip
    )

    if selected_project != st.session_state.selected_project:
        st.session_state.selected_project = selected_project
        st.rerun()

    if selected_project != "Select a project...":
        project_files = get_project_files(selected_project, 'initial_codes')
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

        if len(selected_files) < 2:
            st.warning("Please select at least 2 files for pairwise comparison.")
            return

        st.divider()
        st.subheader(":orange[Pairwise Comparison Settings]")
        
        pairing_mode = st.radio(
            "Select pairing mode:",
            ("All Pairs", "Sequential Pairs"),
            help="All Pairs: Compare each file with every other file. Sequential: Compare each file only with the next file."
        )
        
        # Show which pairs will be compared
        file_names = [os.path.basename(f) for f in selected_files]
        pairs = generate_file_pairs(file_names, 'all_pairs' if pairing_mode == "All Pairs" else 'sequential')
        
        with st.expander(f"File pairs to be compared ({len(pairs)} comparisons)", expanded=False):
            for i, (file1, file2) in enumerate(pairs):
                st.write(f"{i+1}. {file1} ↔ {file2}")

        st.divider()
        st.subheader(":orange[LLM Settings]")
        azure_models = get_azure_models()
        model_options = default_models + azure_models + blablador_models
        selected_model = st.selectbox("Select Model", model_options, help=tooltips.model_tooltip)
        max_temperature_value = 2.0 if selected_model.startswith('gpt') else 1.0
        
        custom_prompts = load_custom_prompts().get('Pairwise Reduction', {})
        all_prompts = {**reduce_duplicate_codes_pairwise, **custom_prompts}
        selected_prompt = st.selectbox("Select a prompt:", list(all_prompts.keys()), help=tooltips.presets_tooltip)
        selected_prompt_data = all_prompts[selected_prompt]
        prompt_input = selected_prompt_data["prompt"]
        model_temperature = selected_prompt_data["temperature"]
        model_top_p = selected_prompt_data["top_p"]

        prompt_input = st.text_area(
            "Edit prompt if needed:",
            value=prompt_input,
            height=200,
            help="This prompt guides the pairwise comparison and merging of codes."
        )

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
            help='Include quotes in comparisons for more context.'
        )

        include_merge_explanation = st.checkbox(
            label="Include merge explanation in merges",
            value=True,
            help="If unticked, the LLM will not generate a merge explanation (saving tokens)."
        )

        if st.button("Process"):
            st.divider()
            st.subheader(":orange[Output]")
            
            # Collect codes from files
            codes_by_file = collect_codes_from_files(selected_files)
            
            # Process pairwise comparisons
            similarity_results = process_pairwise_comparisons(
                codes_by_file=codes_by_file,
                file_pairs=pairs,
                model=selected_model,
                prompt=prompt_input,
                model_temperature=model_temperature,
                model_top_p=model_top_p,
                include_quotes=include_quotes
            )
            
            # Reduce based on similarities
            reduced_df = reduce_based_on_similarities(
                similarity_results=similarity_results,
                codes_by_file=codes_by_file,
                model=selected_model,
                model_temperature=model_temperature,
                model_top_p=model_top_p,
                include_quotes=include_quotes,
                include_merge_explanation=include_merge_explanation
            )
            
            if reduced_df is not None:
                st.success("Processing complete!")
                
                st.write("Reduced Codes:")
                amalgamated_df = amalgamate_duplicate_codes(reduced_df)
                if amalgamated_df is not None:
                    amalgamated_df_for_display = amalgamated_df.copy()
                    amalgamated_df_for_display['quote'] = amalgamated_df_for_display['quote'].apply(format_quotes)
                    amalgamated_df_for_display['original_code'] = amalgamated_df_for_display['original_code'].apply(format_original_codes)
                    st.write(amalgamated_df_for_display)
                    
                    # Save results
                    saved_file_path = save_reduced_codes(selected_project, amalgamated_df, 'pairwise_reduced_codes')
                    st.success(f"Results saved to {os.path.basename(saved_file_path)}")
                    
                    # Download buttons
                    csv = amalgamated_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download reduced codes",
                        data=csv,
                        file_name="pairwise_reduced_codes.csv",
                        mime="text/csv"
                    )
                    
                    # Generate and save expanded format
                    expanded_file = save_expanded_reduced_codes(selected_project, amalgamated_df)
                    st.success(f"Expanded format saved to {os.path.basename(expanded_file)}")
                    
                    # Display statistics
                    st.write("Reduction Statistics:")
                    total_original_codes = sum(len(df) for df in codes_by_file.values())
                    total_reduced_codes = len(amalgamated_df)
                    reduction_percentage = ((total_original_codes - total_reduced_codes) / total_original_codes) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Original Codes", total_original_codes)
                    with col2:
                        st.metric("Reduced Codes", total_reduced_codes)
                    with col3:
                        st.metric("Reduction", f"{reduction_percentage:.1f}%")
                else:
                    st.error("Failed to reduce codes. Check logs for more info.")

        # Display saved files
        pairwise_folder = os.path.join(PROJECTS_DIR, selected_project, 'pairwise_reduced_codes')
        if os.path.exists(pairwise_folder):
            processed_files_list = get_processed_files(selected_project, 'pairwise_reduced_codes')
            with st.expander("Saved Pairwise Reduced Codes", expanded=False):
                for processed_file in processed_files_list:
                    col1, col2 = st.columns([0.9, 0.1])
                    col1.write(processed_file)
                    if col2.button("Delete", key=f"delete_{processed_file}"):
                        os.remove(os.path.join(PROJECTS_DIR, selected_project, 'pairwise_reduced_codes', processed_file))
                        st.success(f"Deleted {processed_file}")
                        st.rerun()
                    df = pd.read_csv(os.path.join(PROJECTS_DIR, selected_project, 'pairwise_reduced_codes', processed_file))
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
            with st.expander("Saved Pairwise Reduced Codes", expanded=False):
                st.info("No pairwise reduced codes saved yet. Process some files to see results here.")

    else:
        st.write("Please select a project. If none, go to '🏠 Project Set Up' to create one.")

    manage_api_keys()

if __name__ == "__main__":
    main()
