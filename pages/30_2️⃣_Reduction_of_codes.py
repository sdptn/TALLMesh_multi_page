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
from llm_utils import llm_call, default_models, blablador_models
import logging
import tooltips
import time
from ui_utils import centered_column_with_number
import uuid
from time import sleep
from instructions import reduce_codes_instructions
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
    output_folder = os.path.join(PROJECTS_DIR, project_name, 'expanded_reduced_codes')
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, f"expanded_reduced_codes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv")
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

def collect_all_initial_codes(selected_files):
    """
    Add a flag to identify reduced codes vs initial codes
    """
    all_codes = []
    codes_per_file = {}
    
    for file_path in selected_files:
        df = pd.read_csv(file_path)
        file_name = os.path.basename(file_path)
        
        if 'source' not in df.columns:
            df['source'] = file_name
        
        df['code_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        df['original_code'] = df['code']
        df['file_index'] = len(codes_per_file)  # Track which file the codes came from
        df['is_reduced'] = 'reduced_codes' in file_path  # Flag for reduced codes
        
        codes_per_file[file_name] = len(df)
        all_codes.append(df)
        
    master_codes_df = pd.concat(all_codes, ignore_index=True)
    master_codes_df.attrs['codes_per_file'] = codes_per_file
    
    return master_codes_df

def generate_comparison_prompt(target_code, comparison_codes, prompt, include_quotes=False):
    """
    Generate a prompt for code comparison that properly handles code IDs.
    
    Args:
        target_code (dict): The code to compare against
        comparison_codes (list): List of codes to compare with
        prompt (str): Base prompt template
        include_quotes (bool): Whether to include quotes in comparison
    """
    base_prompt = prompt
    target_quote = f',\n        "quote": "{target_code["quote"]}"' if include_quotes else ''
    comparison_text = []

    # Debugging 
    if not isinstance(target_code.get('code_id'), str):
        raise ValueError("Target code missing valid code_id")
    
    for code in comparison_codes:
        if not isinstance(code.get('code_id'), str):
            raise ValueError("Comparison code missing valid code_id")
    
    for code in comparison_codes:
        comparison_dict = {
            "code": code["code"],
            "description": code["description"],
            "code_id": code["code_id"]
        }
        if include_quotes:
            comparison_dict["quote"] = code["quote"]
        
        # Escape any special characters in the values
        for key, value in comparison_dict.items():
            if isinstance(value, str):
                comparison_dict[key] = value.replace('"', '\\"').replace('\n', '\\n')
        
        comparison_text.append(json.dumps(comparison_dict))
    
    comparison_list = ',\n    '.join(comparison_text)
    final_prompt = base_prompt % (
        target_code["code"].replace('"', '\\"').replace('\n', '\\n'),
        target_code["description"].replace('"', '\\"').replace('\n', '\\n'),
        target_quote,
        f'[\n    {comparison_list}\n]'
    )

    return final_prompt

def process_similarity_comparisons(master_codes_df, new_codes_start_idx, model, prompt, 
                                 model_temperature, model_top_p, include_quotes=False):
    """
    We need to restructure this to handle both modes properly:
    - In automatic mode: Each code should only compare with codes from subsequent files
    - In incremental mode: New codes should only compare with reduced codes
    """
    # Get the file_index for the current batch of codes
    current_file_indices = master_codes_df.iloc[new_codes_start_idx:]['file_index'].unique()
    
    similarity_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # For each file being processed
    for file_idx in current_file_indices:
        # Get codes from current file
        current_file_codes = master_codes_df[
            (master_codes_df['file_index'] == file_idx) & 
            (master_codes_df.index >= new_codes_start_idx)
        ]
        
        # Get valid comparison codes (from later files or reduced codes)
        comparison_codes = master_codes_df[
            (master_codes_df['file_index'] > file_idx) |  # Later files
            (master_codes_df.index < new_codes_start_idx)  # Previously reduced codes
        ]
        
        if len(comparison_codes) == 0:
            continue
            
        # Process each code from current file
        for idx, target_code in current_file_codes.iterrows():
            comparison_prompt = generate_comparison_prompt(
                target_code.to_dict(),
                [code.to_dict() for _, code in comparison_codes.iterrows()],
                prompt,
                include_quotes
            )

            #print('\n\n')
            #print('Prompt')
            #print(comparison_prompt)
            #print('\n\n')
            
            # API call and result processing remains same
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = llm_call(model, comparison_prompt, model_temperature, model_top_p)

                    print('Raw response')
                    print(response)

                    parsed_response = validate_json_response(response)
                    if parsed_response is None:
                        logger.error("Failed to parse LLM response as valid JSON")
                        continue

                    print('Cleaned response')
                    print(parsed_response)
                    
                    comparison_results = parsed_response.get('comparisons', {})
                    
                    for code_id, is_similar in comparison_results.items():
                        if is_similar:
                            # Find the matching code in comparison_codes
                            matching_rows = comparison_codes[comparison_codes['code_id'] == code_id]
                            if not matching_rows.empty:
                                # Use iloc[0] on matching_rows instead of using matching_idx
                                matching_code = matching_rows.iloc[0]
                                similarity_pair = {
                                    'code1': target_code['code'],
                                    'code1_idx': idx,
                                    'code2': matching_code['code'],
                                    'code2_idx': matching_code.name  # Use the original index
                                }
                                similarity_results.append(similarity_pair)
                                
                                print('Similarity results')
                                print(similarity_results)
                    break
                except Exception as e:
                    logger.error(f"Error processing comparison (attempt {attempt + 1}): {str(e)}")
                    if attempt < max_retries - 1:
                        sleep(2 ** attempt)
                    else:
                        raise
                        
            # Update progress
            relative_progress = (len(similarity_results) / 
                               (len(current_file_codes) * len(comparison_codes)))
            progress_bar.progress(min(1.0, relative_progress))
            status_text.text(f"Processing comparisons for file {file_idx + 1}")

    progress_bar.empty()
    status_text.empty()
    return similarity_results

def reduce_based_on_similarities(similarity_results, master_codes_df, model, model_temperature, model_top_p, include_quotes=False, include_merge_explanation=True):
    logger = logging.getLogger(__name__)

    def log_group_details(group_idx, group, group_codes):
        logger.info(f"\nProcessing group {group_idx}")
        logger.info(f"Group size: {len(group)}")
        logger.info("Group code IDs: " + ", ".join(group))
        logger.info("Original codes in group:")
        for _, code in group_codes.iterrows():
            logger.info(f"  Code ID: {code['code_id']}")
            logger.info(f"    Code: {code['code']}")
            logger.info(f"    Original code: {code.get('original_code', 'Not found')}")

    def generate_merge_prompt(codes_to_merge, include_merge_explanation):
        """
        Dynamically build the prompt, omitting merge explanation if not requested.
        """
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
                         f'Original Code: "{code_row.get("original_code", "Not found")}"')
            if include_quotes and 'quote' in code_row:
                code_text += f'\nQuote: "{code_row["quote"]}"'
            codes_text.append(code_text)

        return merge_prompt.format(codes='\n\n'.join(codes_text))

    def find_code_groups():
        processed_indices = set()
        groups = []
        
        # Create a dictionary to map indices to their similar pairs
        similarity_map = {}
        for pair in similarity_results:
            idx1 = pair['code1_idx']
            idx2 = pair['code2_idx']
            if idx1 not in similarity_map:
                similarity_map[idx1] = set()
            if idx2 not in similarity_map:
                similarity_map[idx2] = set()
            similarity_map[idx1].add(idx2)
            similarity_map[idx2].add(idx1)
        
        # Find connected groups
        for idx in range(len(master_codes_df)):
            if idx in processed_indices:
                continue
                
            # Start a new group with this index
            current_group = {master_codes_df.iloc[idx]['code_id']}
            if idx in similarity_map:
                # Add all similar codes
                for similar_idx in similarity_map[idx]:
                    current_group.add(master_codes_df.iloc[similar_idx]['code_id'])
            
            # Only add this group if it's not already a subset of an existing group
            if not any(current_group.issubset(existing_group) for existing_group in groups):
                groups.append(current_group)
                processed_indices.add(idx)
                if idx in similarity_map:
                    processed_indices.update(similarity_map[idx])
            
        logger.info(f"\nFound {len(groups)} code groups")
        return groups

    reduced_codes = []
    code_groups = find_code_groups()
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, group in enumerate(code_groups):
        status_text.text(f"Processing group {idx + 1}/{len(code_groups)}")
        progress_bar.progress((idx + 1) / len(code_groups))
        group_codes = master_codes_df[master_codes_df['code_id'].isin(group)]
        log_group_details(idx, group, group_codes)

        if len(group_codes) > 1:
            merge_prompt = generate_merge_prompt(group_codes, include_merge_explanation)
            logger.info("\nGenerated merge prompt:")
            logger.info(merge_prompt)
            try:
                response = llm_call(model, merge_prompt, model_temperature, model_top_p)
                logger.info("\nLLM Response:")
                logger.info(response)
                merged_details = json.loads(response)['merged_code']
                time.sleep(1) # Added a v short sleep, anything to avoid 429

                if 'merge_explanation' not in merged_details:
                    merged_details['merge_explanation'] = ""

                all_original_codes = []
                seen_codes = set()  # Track unique codes
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
                logger.info("\nCreated reduced code:")
                logger.info(json.dumps(reduced_code, indent=2))
            except Exception as e:
                logger.error(f"\nError merging codes in group {idx}: {str(e)}")
                # Gather all original codes from the group
                all_original_codes = []
                quotes_list = []
                unique_sources = set()
                seen_codes = set()  # Track unique codes
                for _, code_row in group_codes.iterrows():
                    orig_val = code_row.get('original_code', code_row['code'])
                    if isinstance(orig_val, str):
                        try:
                            parsed = json.loads(orig_val)
                            if isinstance(parsed, list):
                                for code in parsed:
                                    if code not in seen_codes:
                                        all_original_codes.append(code)
                                        seen_codes.add(code)
                            else:
                                if parsed not in seen_codes:
                                    all_original_codes.append(parsed)
                                    seen_codes.add(parsed)
                        except json.JSONDecodeError:
                            if orig_val not in seen_codes:
                                all_original_codes.append(orig_val)
                                seen_codes.add(orig_val)
                    else:
                        if orig_val not in seen_codes:
                            all_original_codes.append(orig_val)
                            seen_codes.add(orig_val)
                    
                    quotes_list.append({'text': code_row['quote'], 'source': code_row['source']})
                    unique_sources.add(code_row['source'])

                # Use the first code in the group as the representative code name and description
                fallback_code = group_codes.iloc[0]
                reduced_code = {
                    'code': fallback_code['code'],
                    'description': fallback_code['description'],
                    'merge_explanation': 'Merge failed - using original code',
                    'original_code': json.dumps(all_original_codes),
                    'quote': json.dumps(quotes_list),
                    'source': ', '.join(unique_sources)
                }

                logger.info("\nUsing fallback code:")
                logger.info(json.dumps(reduced_code, indent=2))
        else:
            single_code = group_codes.iloc[0]
            reduced_code = {
                'code': single_code['code'],
                'description': single_code['description'],
                'merge_explanation': '',  # Single code fallback
                'original_code': json.dumps([single_code['code']]),
                'quote': json.dumps([{'text': single_code['quote'], 'source': single_code['source']}]),
                'source': single_code['source']
            }
            logger.info("\nSingle code (no merge needed):")
            logger.info(json.dumps(reduced_code, indent=2))

        reduced_codes.append(reduced_code)

    progress_bar.empty()
    status_text.empty()

    reduced_df = pd.DataFrame(reduced_codes)
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


class AutoSaveResume:
    def __init__(self, project_name):
        self.project_name = project_name
        self.save_path = os.path.join(PROJECTS_DIR, project_name, 'code_reduction_progress.json')
        self.results_path = os.path.join(PROJECTS_DIR, project_name, 'code_reduction_results.csv')
        
    def generate_run_id(self):
        return str(uuid.uuid4())
    
    def save_progress(self, processed_files, reduced_df, total_codes_list, unique_codes_list, 
                 cumulative_total, mode, master_codes_df=None, similarity_results=None, 
                 selected_files=None, run_id=None):
        """
        Ensure we maintain file indices and reduction status when saving progress
        """
        progress = {
            'processed_files': processed_files,
            'reduced_df': reduced_df.to_dict(orient='records'),
            'total_codes_list': convert_numpy_types(total_codes_list),
            'unique_codes_list': convert_numpy_types(unique_codes_list),
            'cumulative_total': convert_numpy_types(cumulative_total),
            'mode': mode,
            'run_id': run_id or self.generate_run_id()
        }
        
        if master_codes_df is not None:
            # Ensure we save file_index and is_reduced flags
            progress['master_codes_df'] = convert_numpy_types(
                master_codes_df.to_dict(orient='records')
            )
        if similarity_results is not None:
            progress['similarity_results'] = convert_numpy_types(similarity_results)
        if selected_files is not None:
            progress['selected_files'] = selected_files

        with open(self.save_path, 'w') as f:
            json.dump(progress, f)


    def load_progress(self):
        """
        Load progress state from a JSON file.
        """
        if os.path.exists(self.save_path):
            with open(self.save_path, 'r') as f:
                progress = json.load(f)
            # Convert dict back to DataFrame
            progress['reduced_df'] = pd.DataFrame.from_records(progress['reduced_df'])
            if 'master_codes_df' in progress:
                progress['master_codes_df'] = pd.DataFrame.from_records(progress['master_codes_df'])
            return progress
        return None


    def clear_progress(self, clear_results=True):
        if os.path.exists(self.save_path):
            os.remove(self.save_path)
        if clear_results and os.path.exists(self.results_path):
            os.remove(self.results_path)

def amalgamate_duplicate_codes(df):
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
    reduced_codes_folder = os.path.join(PROJECTS_DIR, project_name, folder)
    os.makedirs(reduced_codes_folder, exist_ok=True)
    output_file_path = os.path.join(reduced_codes_folder, f"reduced_codes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(output_file_path, index=False, encoding='utf-8')
    return output_file_path

def process_files_with_autosave(selected_project, selected_files, model, prompt, 
                               model_temperature, model_top_p, include_quotes, 
                               resume_data=None, mode='Automatic', include_merge_explanation=True):
    """
    Unified processing function with streamlined status messaging.
    """
    auto_save = AutoSaveResume(selected_project)
    processing_message = st.empty()

    # Get or generate run_id
    run_id = None
    if resume_data:
        run_id = resume_data.get('run_id')
    if not run_id:
        run_id = auto_save.generate_run_id()
    
    # Initialize or resume state
    if resume_data:
        master_codes_df = resume_data.get('master_codes_df')
        similarity_results = resume_data.get('similarity_results', [])
        processed_files = resume_data['processed_files']
        processed_codes_count = sum(len(pd.read_csv(f)) for f in processed_files)
    else:
        master_codes_df = None
        similarity_results = []
        processed_files = []
        processed_codes_count = 0

    # Handle file selection based on mode
    if mode == 'Incremental':
        next_file_index = len(processed_files)
        if next_file_index >= len(selected_files):
            return master_codes_df, pd.DataFrame(), processed_files
        current_files = [selected_files[next_file_index]]
    else:
        current_files = selected_files

    # Process current batch
    current_master_df = collect_all_initial_codes(current_files)
    
    if master_codes_df is None:
        master_codes_df = current_master_df
    else:
        master_codes_df = pd.concat([master_codes_df, current_master_df], ignore_index=True)

    # Store progress info for current batch
    st.session_state['progress_info'] = {
        'total_codes': len(master_codes_df),
        'processed_codes_count': processed_codes_count,
        'new_codes_count': len(current_master_df)
    }

    if mode == 'Incremental':
        current_file = os.path.basename(current_files[0])
        processing_message.info(f"Processing {current_file}...")
    
    # Process and reduce codes
    # Note: Let the individual functions handle their own progress bars
    new_similarity_results = process_similarity_comparisons(
        master_codes_df=master_codes_df,
        new_codes_start_idx=len(master_codes_df) - len(current_master_df),
        model=model,
        prompt=prompt,
        model_temperature=model_temperature,
        model_top_p=model_top_p,
        include_quotes=include_quotes
    )
    similarity_results.extend(new_similarity_results)

    reduced_df = reduce_based_on_similarities(
        similarity_results=similarity_results,
        master_codes_df=master_codes_df,
        model=model,
        model_temperature=model_temperature,
        model_top_p=model_top_p,
        include_quotes=include_quotes,
        include_merge_explanation=include_merge_explanation
    )

    # Update tracking
    if mode == 'Incremental':
        processed_files.append(current_files[0])
    else:
        processed_files = selected_files

    # Create results summary
    total_codes = len(master_codes_df)
    current_processed = processed_codes_count + len(current_master_df)

    # Track progress for saturation metrics
    if mode == 'Incremental':
        results_df = pd.DataFrame({
            'total_codes': [total_codes],
            'processed_codes': [current_processed],
            'unique_codes': [len(reduced_df['code'].unique())]
        })
    else:
        # For automatic mode, create points for each file
        file_counts = [len(pd.read_csv(f)) for f in selected_files]
        cum_total = list(pd.Series(file_counts).cumsum())
        results_df = pd.DataFrame({
            'total_codes': cum_total,
            'processed_codes': [current_processed] * len(selected_files),
            'unique_codes': [len(reduced_df['code'].unique())] * len(selected_files)
        })

    # Save intermediate results for saturation metrics
    results_path = os.path.join(PROJECTS_DIR, selected_project, 'code_reduction_results.csv')
    if mode == 'Incremental':
        if os.path.exists(results_path):
            existing_results = pd.read_csv(results_path)
            # Only concatenate if it's the same run
            if 'run_id' in existing_results.columns and run_id in existing_results['run_id'].values:
                results_df = pd.concat([existing_results, results_df], ignore_index=True)
            else:
                # New run, start fresh
                results_df['run_id'] = run_id
        else:
            results_df['run_id'] = run_id
    results_df.to_csv(results_path, index=False)

    # Generate and save expanded format
    expanded_file = save_expanded_reduced_codes(selected_project, reduced_df)
    
    # Handle autosave with run_id
    if mode == 'Incremental' and len(processed_files) < len(selected_files):
        try:
            auto_save.save_progress(
                processed_files=processed_files,
                reduced_df=reduced_df,
                total_codes_list=[total_codes],
                unique_codes_list=[len(reduced_df['code'].unique())],
                cumulative_total=current_processed,
                mode=mode,
                master_codes_df=master_codes_df,
                similarity_results=similarity_results,
                selected_files=selected_files,
                run_id=run_id
            )
            next_file = os.path.basename(selected_files[len(processed_files)])
            processing_message.info(f"Ready to process: {next_file}")
        except Exception as e:
            st.error(f"Error saving progress: {str(e)}. Progress may be incomplete.")
            raise
    else:
        auto_save.clear_progress()
        processing_message.empty()

    return reduced_df, results_df, processed_files

def load_custom_prompts():
    try:
        with open('custom_prompts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def format_quotes(quotes_json):
    try:
        quotes = json.loads(quotes_json)
        formatted_quotes = "\n".join(f"{quote['text']} (Source: {quote['source']})" for quote in quotes)
        return formatted_quotes
    except (json.JSONDecodeError, KeyError, TypeError):
        return quotes_json

def format_original_codes(original_codes):
    try:
        codes = json.loads(original_codes)
        return ', '.join(codes) if isinstance(codes, list) else original_codes
    except json.JSONDecodeError:
        return original_codes

@st.cache_data
def convert_df(df):
    return df.to_csv().encode('utf-8')


# ==============================================================================
#                             MAIN STREAMLIT FUNCTION
# ==============================================================================

def main():
    if 'current_prompt' in st.session_state:
        del st.session_state.current_prompt 

    reduce_codes_instructions()

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

        st.divider()
        st.subheader(":orange[LLM Settings]")
        azure_models = get_azure_models()
        model_options = default_models + azure_models + blablador_models
        selected_model = st.selectbox("Select Model", model_options, help=tooltips.model_tooltip)
        max_temperature_value = 2.0 if selected_model.startswith('gpt') else 1.0
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
            help="In the 1-vs-all approach, this prompt guides merging."
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

        st.subheader(":orange[Processing Mode]")
        processing_mode = st.radio(
            "Choose processing mode:",
            ("Automatic", "Incremental"),
            help="Automatic: all files at once. Incremental: one file at a time."
        )

        auto_save = AutoSaveResume(selected_project)
        progress = auto_save.load_progress()
        resume_data = None

        # Track whether we're actively processing
        is_processing = 'processing_active' in st.session_state and st.session_state.processing_active
        
        # Only show resume options if we have progress AND we're not actively processing
        if progress and not is_processing:
            processed_files = progress['processed_files']
            saved_mode = progress.get('mode', 'Automatic')
            
            if saved_mode == processing_mode:
                col1, col2 = st.columns(2)
                with col1:
                    resume = st.checkbox("Resume from last checkpoint", value=True, key="resume_checkbox")
                if resume:
                    resume_data = progress
                else:
                    auto_save.clear_progress()
            else:
                choice = st.radio(
                    "Found progress in different mode. Choose:",
                    (
                        f"Resume in '{saved_mode}' mode",
                        f"Start fresh in '{processing_mode}' mode"
                    ),
                    key="mode_switch_choice"
                )
                if choice == f"Resume in '{saved_mode}' mode":
                    processing_mode = saved_mode
                    resume_data = progress
                else:
                    auto_save.clear_progress()

        if st.button("Process"):
            # Set processing active flag
            st.session_state.processing_active = True
            
            st.divider()
            st.subheader(":orange[Output]")
            
            reduced_df, results_df, processed_files = process_files_with_autosave(
                selected_project=selected_project,
                selected_files=selected_files,
                model=selected_model,
                prompt=prompt_input,
                model_temperature=model_temperature,
                model_top_p=model_top_p,
                include_quotes=include_quotes,
                resume_data=resume_data,
                mode=processing_mode,
                include_merge_explanation=include_merge_explanation
            ) 

            if reduced_df is not None:
                st.session_state.processing_active = False
                
                if processing_mode == 'Incremental' and len(processed_files) < len(selected_files):
                    next_file = os.path.basename(selected_files[len(processed_files)])
                    st.info(f"Click 'Process' again to process the next file: {next_file}")
                else:
                    st.success("Processing complete!")
                    auto_save.clear_progress()
                    
                st.write("Reduced Codes:")
                amalgamated_df = amalgamate_duplicate_codes(reduced_df)
                if amalgamated_df is not None:
                    amalgamated_df_for_display = amalgamated_df.copy()
                    amalgamated_df_for_display['quote'] = amalgamated_df_for_display['quote'].apply(format_quotes)
                    amalgamated_df_for_display['original_code'] = amalgamated_df_for_display['original_code'].apply(format_original_codes)
                    st.write(amalgamated_df_for_display)

                    # Display and save total vs processed vs unique codes
                    st.write("Code Reduction Tracking:")
                    st.write(results_df)
                    results_csv = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download code reduction results",
                        data=results_csv,
                        file_name="code_reduction_results.csv",
                        mime="text/csv"
                    )

                    saved_file_path = save_reduced_codes(selected_project, amalgamated_df, 'reduced_codes')
                    st.success(f"Results saved to {os.path.basename(saved_file_path)}")

                    # Download buttons
                    csv = amalgamated_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download reduced codes",
                        data=csv,
                        file_name="reduced_codes.csv",
                        mime="text/csv"
                    )

                    # Generate and save expanded format
                    expanded_file = save_expanded_reduced_codes(selected_project, amalgamated_df)
                    st.success(f"Expanded format saved to {os.path.basename(expanded_file)}")

                    # Save results for saturation metrics
                    results_path = os.path.join(PROJECTS_DIR, selected_project, 'code_reduction_results.csv')
                    if os.path.exists(results_path):
                        existing_results = pd.read_csv(results_path)
                        results_df = pd.concat([existing_results, results_df], ignore_index=True)
                    else:
                        results_df.to_csv(results_path, index=False)

                    
                    
                else:
                    st.error("Failed to reduce codes. Check logs for more info.")

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
        st.write("Please select a project. If none, go to '🏠 Project Set Up' to create one.")

    manage_api_keys()

if __name__ == "__main__":
    main()