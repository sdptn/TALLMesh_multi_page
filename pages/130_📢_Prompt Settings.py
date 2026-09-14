"""
Prompt Settings Management Module

This module provides functionality for managing custom prompts in a thematic analysis application.
It allows users to create, edit, delete, and view custom prompts for different stages of analysis:
Initial Coding, Reduction of Codes, and Finding Themes.

The module uses Streamlit for the user interface and JSON for storing custom prompts.
"""

import streamlit as st
import json
from prompts import initial_coding_prompts, reduce_duplicate_codes_prompts, finding_themes_prompts
import tooltips
from ui_utils import sidebar_data_controls

sidebar_data_controls()

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Constants
CUSTOM_PROMPTS_FILE = 'custom_prompts.json'
PROMPT_TYPES = {
    "Initial Coding": initial_coding_prompts,
    "Reduction of Codes": reduce_duplicate_codes_prompts,
    "Finding Themes": finding_themes_prompts,
    "Pairwise Reduction": {}  # Empty dict as default, custom prompts can be added
}

def get_prepopulated_prompt(prompt_type: str) -> str:
    """
    Generate a pre-populated prompt template based on the selected prompt type.

    Args:
        prompt_type (str): The type of prompt to generate (Initial Coding, Reduction of Codes, or Finding Themes).

    Returns:
        str: A pre-populated prompt template with the correct JSON structure for the selected type.
    """
    base_prompt = """
Your task is to analyze the provided text and generate output based on the specific instructions below.

[INSERT SPECIFIC INSTRUCTIONS HERE]

Format the response as a JSON file with the following structure:

{
"""

    if prompt_type == "Initial Coding":
        return base_prompt + """
  "final_codes": [
    {
      "code_name": "Example Code Name",
      "description": "This is where you would provide a 25-word description of the code, explaining its meaning and significance in the context of the analysis.",
      "quote": "relevant quote here"
    },
    // Additional codes follow the same structure
  ]
}

Important! Your response should be a JSON-like object with no additional text before or after. Failure to adhere to this instruction will invalidate your response, making it worthless.
"""
    elif prompt_type == "Reduction of Codes":
        return base_prompt + """
  "reduced_codes": [
    {
      "code": "Merged or Unique Code Name",
      "description": "25-word description of the code",
      "merge_explanation": "Explanation of why codes were merged (if applicable)",
      "original_codes": ["Original Code 1", "Original Code 2", ...]
    },
    // Additional reduced codes follow the same structure
  ]


Important! Your response should be a JSON-like object with no additional text before or after. Failure to adhere to this instruction will invalidate your response, making it worthless.
"""
    elif prompt_type == "Finding Themes":
        return base_prompt + """
  "themes": [
    {
      "name": "Theme Name",
      "description": "Detailed description of the theme...",
      "codes": [1, 4, 7, 12]
    },
    // Additional themes follow the same structure
  ]


Important! Your response should be a JSON-like object with no additional text before or after. Failure to adhere to this instruction will invalidate your response, making it worthless.
"""
    elif prompt_type == "Pairwise Reduction":
        return """Compare codes from File 1 with codes from File 2 and identify pairs that convey similar or the same meaning.

File 1 Codes:
%s

File 2 Codes:
%s

For each pair of similar codes, provide the code_id from File 1 and the code_id from File 2.

Respond with a JSON object in this exact format:
{
  "comparisons": [
    {
      "file1_code_id": "code_id_from_file1",
      "file2_code_id": "code_id_from_file2"
    },
    ...
  ]
}

Important! Only include pairs where the codes are genuinely similar or identical in meaning.
Do not include pairs that are only superficially similar or distinctly different.
Your response must be a valid JSON object with no additional text."""
    else:
        return ""

def save_custom_prompts(prompts: dict) -> None:
    """
    Save custom prompts to a JSON file.

    Args:
        prompts (dict): A dictionary containing custom prompts for each prompt type.
    """
    with open(CUSTOM_PROMPTS_FILE, 'w') as f:
        json.dump(prompts, f)

def load_custom_prompts() -> dict:
    """
    Load custom prompts from a JSON file.

    Returns:
        dict: A dictionary containing custom prompts for each prompt type.
               Returns an empty dictionary if the file is not found.
    """
    try:
        with open(CUSTOM_PROMPTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def display_instructions() -> None:
    """
    Display instructions for using the Custom Prompt Management page.
    """
    with st.expander("Instructions"):
        st.header("Custom Prompts Management")
        st.write("The Custom Prompts Management page allows you to create, edit, and delete custom prompts for different stages of your thematic analysis. Here's how to use this page effectively:")

        st.subheader(":orange[1. Selecting Prompt Type]")
        st.write("At the top of the page, you'll find a dropdown menu to select the prompt type:")
        st.markdown("""
        - **Initial Coding**: For creating initial codes from your data.
        - **Reduction of Codes**: For merging and refining your codes using 1-vs-all comparison.
        - **Finding Themes**: For identifying overarching themes from your codes.
        - **Pairwise Reduction**: For comparing and merging codes between pairs of files.
        """)
        st.write("Select the prompt type you want to work with.")

        # ... (rest of the instructions)

        st.write("Remember, well-crafted prompts can significantly improve the quality of your analysis. Take time to refine your prompts based on your specific research needs and the nature of your data.")

def display_existing_prompts(custom_prompts: dict, selected_type: str) -> None:
    """
    Display existing custom prompts for the selected prompt type.

    Args:
        custom_prompts (dict): A dictionary containing all custom prompts.
        selected_type (str): The currently selected prompt type.
    """
    st.subheader(f"Custom Prompts for {selected_type}")

    for name, data in custom_prompts.get(selected_type, {}).items():
        with st.expander(name):
            st.text_area(
                "Prompt",
                value=data["prompt"],
                key=f"prompt_{name}",
                height=300,
                help="Edit the custom prompt text here."
            )
            col1, col2 = st.columns(2)
            with col1:
                st.number_input(
                    "Temperature",
                    value=data["temperature"],
                    key=f"temp_{name}",
                    min_value=0.0,
                    max_value=2.0,
                    step=0.01,
                    help=tooltips.model_temp_tooltip
                )
            with col2:
                st.number_input(
                    "Top P",
                    value=data["top_p"],
                    key=f"top_p_{name}",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    help=tooltips.top_p_tooltip
                )
            if st.button("Update", key=f"update_{name}"):
                custom_prompts[selected_type][name] = {
                    "prompt": st.session_state[f"prompt_{name}"],
                    "temperature": st.session_state[f"temp_{name}"],
                    "top_p": st.session_state[f"top_p_{name}"]
                }
                save_custom_prompts(custom_prompts)
                st.success(f"Updated custom prompt: {name}")
            if st.button("Delete", key=f"delete_{name}"):
                del custom_prompts[selected_type][name]
                save_custom_prompts(custom_prompts)
                st.success(f"Deleted custom prompt: {name}")
                st.rerun()


def add_new_prompt(custom_prompts: dict, selected_type: str) -> None:
    """
    Add a new custom prompt for the selected prompt type.

    Args:
        custom_prompts (dict): A dictionary containing all custom prompts.
        selected_type (str): The currently selected prompt type.
    """
    st.subheader("Add New Custom Prompt")
    new_name = st.text_input(
        "Name for new prompt:",
        help="Enter a unique name for your custom prompt."
    )
    new_prompt = st.text_area(
        "New prompt:",
        value=get_prepopulated_prompt(selected_type),
        height=300,
        help="Write or paste your custom prompt here."
    )
    col1, col2 = st.columns(2)
    with col1:
        new_temp = st.slider(
            "Temperature",
            value=0.1,
            min_value=0.0,
            max_value=2.0,
            step=0.01,
            help="Controls the randomness of the output. Higher values make the output more random."
        )
    with col2:
        new_top_p = st.slider(
            "Top P",
            value=1.0,
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            help="Controls the nucleus sampling for the output. Lower values result in more focused outputs."
        )

    if st.button("Add Custom Prompt"):
        if new_name and new_prompt:
            if selected_type not in custom_prompts:
                custom_prompts[selected_type] = {}
            custom_prompts[selected_type][new_name] = {
                "prompt": new_prompt,
                "temperature": new_temp,
                "top_p": new_top_p
            }
            save_custom_prompts(custom_prompts)
            st.success(f"Added new custom prompt: {new_name}")
            st.rerun()
        else:
            st.error("Please provide both a name and a prompt.")

def main():
    """
    Main function to run the Custom Prompt Management application.
    """
    st.title("Custom Prompt Management")

    display_instructions()

    custom_prompts = load_custom_prompts()

    selected_type = st.selectbox(
        "Select prompt type:",
        list(PROMPT_TYPES.keys()),
        help="Choose the type of prompt you wish to manage."
    )

    display_existing_prompts(custom_prompts, selected_type)

    add_new_prompt(custom_prompts, selected_type)

if __name__ == "__main__":
    main()
