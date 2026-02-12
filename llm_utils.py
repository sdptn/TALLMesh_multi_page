from openai import OpenAI, AzureOpenAI
#import anthropic
import streamlit as st
from api_key_management import load_api_keys, load_azure_settings
import time
import random
import logging
import json
import re

import requests # Ari Thomson added - need this for making api requests to Blablador as there is no wrapper, already in the requirements file, super handy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_models = ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-2025-04-14", "gpt-4.1-mini", "gpt-4.1-nano"] #, "claude-sonnet-3.5"] # Anthropic model removed, dependency issue with anthropic package

blablador_models = ["Blablador - Qwen3-VL-32B-Instruct-FP8 (Large Model as of Novemeber 2025)"]#, "Blablador - Llama3.1 405b (Currently Testing)"] # Ari Thomson added blablador models, thought it best to keep them seperate from the GPT ones

graphia_llm_models = ["DeepSeek-V3.1-vLLM", "Qwen3-Coder-30B-A3B-Instruct-Q8_0"] #Add more as needed

def exponential_backoff(attempt, max_attempts=5, base_delay=5, max_delay=120):
    if attempt >= max_attempts:
        raise Exception("Max retry attempts reached")
    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 0.5 * (2 ** attempt)), max_delay)
    logger.info(f"Backing off for {delay:.2f} seconds (attempt {attempt + 1}/{max_attempts})")
    time.sleep(delay)

def extract_json(text):
    try:
        # First, try to parse the entire text as JSON
        return json.loads(text)
    except json.JSONDecodeError:
        # If that fails, try to find a JSON-like structure
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None

def llm_call(model, full_prompt, model_temperature, model_top_p):
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if model.startswith("gpt"):
                client = OpenAI(api_key=load_api_keys().get('OpenAI'))
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": full_prompt}],
                    response_format={ "type": "json_object" },
                    temperature=model_temperature,
                    top_p=model_top_p
                )
                return response.choices[0].message.content
            
            elif model.startswith("claude"):
                client = anthropic.Anthropic(api_key=load_api_keys().get('Anthropic'))
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=8192,
                    temperature=model_temperature,
                    top_p=model_top_p,
                    messages=[{"role": "user", "content": full_prompt}]
                )
                content = response.content[0].text
                json_content = extract_json(content)
                if json_content is None:
                    logger.warning(f"Failed to extract valid JSON from Claude's response. Raw content: {content}")
                    raise ValueError("Failed to extract valid JSON from Claude's response")
                return json.dumps(json_content)

            elif model.startswith("azure_"):
                azure_settings = load_azure_settings()
                if not azure_settings:
                    st.error("Azure settings are not configured. Please set them up in the Azure Settings page.")
                    return None

                print(f"Azure settings: {azure_settings}")
                print(f"Azure settings type: {type(azure_settings)}")

                deployment_name = model.split("azure_")[1]
                
                if 'deployments' not in azure_settings or not isinstance(azure_settings['deployments'], list):
                    st.error("Invalid Azure settings format. 'deployments' should be a list.")
                    return None

                deployment = next((d for d in azure_settings['deployments'] if d == deployment_name), None)
                
                if not deployment:
                    st.error(f"Selected Azure deployment '{deployment_name}' not found in settings.")
                    return None

                client = AzureOpenAI(
                    api_key=azure_settings['api_key'],
                    api_version="2024-10-21",
                    azure_endpoint=azure_settings['endpoint']
                )
                response = client.chat.completions.create(
                    model=deployment,
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=model_temperature,
                    top_p=model_top_p
                )
                content = response.choices[0].message.content

                json_content = extract_json(content)
                if json_content is None:
                    logger.warning(f"Failed to extract valid JSON from Azure's response. Raw content: {content}")
                    raise ValueError("Failed to extract valid JSON from Azure's response")
                return json.dumps(json_content)
            
            elif model.startswith("graphia-llm:"):
                actual_model = model.split("graphia-llm:", 1)[1]

                keys = load_api_keys()
                proxy_key = keys.get('GRAPHIA_LLM')
                if not proxy_key:
                    st.error("GRAPHIA_LLM Proxy settings are not configured. Please set them up in the API Key Management page.")
                    return None
                
                client = OpenAI(api_key=proxy_key, base_url="https://llm.graphia-ssh.eu")
                response = client.chat.completions.create(
                    model=actual_model,
                    messages=[{"role": "user", "content": full_prompt}],
                    response_format={"type": "json_object"},
                    temperature=model_temperature,
                    top_p=model_top_p
                )
                content = response.choices[0].message.content 
                
                if content and "<!DOCTYPE html>" in content:
                    raise RuntimeError("GRAPHIA LLM returned HTML (likely 503 maintenance page).")
                
                json_content = extract_json(content)
                if json_content is None:
                    logger.warning(f"Failed to extract valid JSON from GRAPHIA_LLM response. Raw content: {content[:300]}")
                    raise ValueError("Failed to extract valid JSON from GRAPHIA_LLM response")
                return json.dumps(json_content) 

            #testing having the call outside the loop, even if i think it wont change anything 
            elif model.startswith("Blablador"):

                alias = "alias-large"

                settings = {
                "model": alias,
                "messages":  [
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": full_prompt}
                ],
                "temperature": model_temperature,
                "top_p": model_top_p,
                }

                settings = json.dumps(settings)

                headers = {
                    'accept': 'application/json', 
                    'Authorization': f"Bearer {load_api_keys().get('Blablador')}", 
                    'Content-Type': 'application/json',
                    'Connection': 'close' 
                }

                response = requests.post(url="https://api.helmholtz-blablador.fz-juelich.de/v1/chat/completions", headers=headers, data=settings)  # make the api call
                response_data = response.json() # parse the api call

                return response_data['choices'][0]['message']['content'] # return the content from the api call, we don't care about the other information

            
            else:
                st.error(f"Unsupported model type: {model}")
                return None

        except Exception as e:
            if hasattr(e, 'status_code') and e.status_code == 429:
                logger.info(f"Rate limit error (429) hit... backing off gracefully (attempt {attempt + 1}/{max_attempts})")
                exponential_backoff(attempt)
            elif isinstance(e, ValueError) and "Failed to extract valid JSON" in str(e):
                logger.warning(f"JSON extraction failed (attempt {attempt + 1}/{max_attempts}): {str(e)}")
                if attempt < max_attempts - 1:
                    logger.info("Retrying with the same prompt...")
                    time.sleep(2)  # Short delay before retrying
                else:
                    logger.error("Max attempts reached for JSON extraction")
                    return None
                
            elif "503" in str(e) or "maintenance" in str(e).lower() or "returned HTML" in str(e):
                logger.info(f"Received 503 or maintenance response from GRAPHIA LLM (attempt {attempt + 1}/{max_attempts}). Backing off and retrying...")
                exponential_backoff(attempt, base_delay=2, max_delay=30) 
            else:
                logger.error(f"Unexpected error occurred: {str(e)}")
                st.error(f"An unexpected error occurred: {str(e)}")
                return None

    st.error("Max retry attempts reached. Unable to complete the API call.")
    return None

def chunk_codes(codes, chunk_size):
    """
    Split the codes into chunks of specified size.
    
    Args:
        codes (list): List of code dictionaries.
        chunk_size (int): Maximum number of codes per chunk.
    
    Returns:
        list: List of code chunks.
    """
    return [codes[i:i + chunk_size] for i in range(0, len(codes), chunk_size)]

def process_chunks(model, prompt_template, codes, model_temperature, model_top_p, chunk_size=50, include_quotes=False):
    """
    Process codes in chunks for models with output limitations.
    
    Args:
        model (str): The name of the AI model to use.
        prompt_template (str): The template for the prompt.
        codes (list): List of code dictionaries.
        model_temperature (float): The temperature setting for the AI model.
        model_top_p (float): The top_p setting for the AI model.
        chunk_size (int): Maximum number of codes per chunk.
        include_quotes (bool): Whether to include quotes in the processing.
    
    Returns:
        list: List of reduced codes.
    """
    chunked_codes = chunk_codes(codes, chunk_size)
    reduced_codes = []
    original_code_set = set(code['code'] for code in codes)
    processed_original_codes = set()
    missing_codes = {}

    for chunk in chunked_codes:
        chunk_prompt = prompt_template.replace("{codes}", json.dumps(chunk))
        chunk_result = llm_call(model, chunk_prompt, model_temperature, model_top_p)
        
        if chunk_result:
            try:
                chunk_reduced_codes = json.loads(chunk_result)['reduced_codes']
                for reduced_code in chunk_reduced_codes:
                    original_codes = set(reduced_code.get('original_codes', [reduced_code['code']]))
                    processed_original_codes.update(original_codes)
                    reduced_codes.append(reduced_code)
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing chunk result: {str(e)}")
                # Add retry logic here if needed
                continue
        
        # Check for missing codes after each chunk
        current_missing_codes = original_code_set - processed_original_codes
        for code in chunk:
            if code['code'] in current_missing_codes:
                missing_code = {'description': code['description']}
                if include_quotes:
                    missing_code['quote'] = code['quote']
                missing_codes[code['code']] = missing_code

    # Process missing codes
    if missing_codes:
        logger.warning(f"Processing {len(missing_codes)} missing codes")
        missing_codes_chunk = [{'code': k, **v} for k, v in missing_codes.items()]
        missing_prompt = prompt_template.replace("{codes}", json.dumps(missing_codes_chunk))
        missing_result = llm_call(model, missing_prompt, model_temperature, model_top_p)
        
        if missing_result:
            try:
                missing_reduced_codes = json.loads(missing_result)['reduced_codes']
                reduced_codes.extend(missing_reduced_codes)
                for code in missing_reduced_codes:
                    processed_original_codes.update(code.get('original_codes', [code['code']]))
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing missing codes: {str(e)}")

    # Final check
    final_missing_codes = original_code_set - processed_original_codes
    if final_missing_codes:
        logger.warning(f"Still missing codes after final processing: {final_missing_codes}")

    return reduced_codes