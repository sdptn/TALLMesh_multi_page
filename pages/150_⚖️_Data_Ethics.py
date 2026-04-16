import os
import streamlit as st
import json
import shutil

def main():
    # Set page config
    st.set_page_config(page_title="Data Processing Disclaimer", page_icon="⚠️")
    
    # Display logo
    #logo = "pages/static/tmeshlogo.png"
    #st.image(logo)
    
    # Main disclaimer
    st.title("⚠️ Important Disclaimer")
    st.error("""
        **Please read carefully before proceeding:**
        - You are responsible for ensuring compliance with your organization's data protection policies
        - Verify all data handling requirements before using this service
        - Check your organization's policies regarding AI model usage
        - Conduct appropriate risk assessments for your use case
    """)
    
    # OpenAI Section
    st.header("OpenAI Data Usage Policy")
    st.info("""
        Data submitted through the OpenAI API is not used to train OpenAI models or improve OpenAI's service offering. 
        
        Note: Data submitted through non-API consumer services (ChatGPT or DALL·E) may be used to improve OpenAI's models.
        
        For full details, see: https://openai.com/consumer-privacy/
    """)
    
    # Azure OpenAI Section
    st.header("Azure OpenAI Service Policy")
    st.info("""
        Your prompts (inputs) and completions (outputs), your embeddings, and your training data:
        - Are NOT available to other customers
        - Are NOT available to OpenAI
        - Are NOT used to improve OpenAI models
        - Are NOT used to train, retrain, or improve Azure OpenAI Service foundation models
        - Are NOT used to improve any Microsoft or 3rd party products or services without your permission
        
        Additional information:
        - Your fine-tuned Azure OpenAI models are available exclusively for your use
        - The Azure OpenAI Service is operated by Microsoft in Microsoft's Azure environment
        - The Service does NOT interact with any services operated by OpenAI
        
        For full details, see: https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy
    """)

    st.header("How TALLMesh Handles Data")
    st.info("""
        When you git clone and set up TALLMesh, it creates several directories within the project working directory which store potentially sensitive information you should be aware of..
        - api_keys.json ; whenever you add or remove keys via the GUI, they are stored (or deleted from) this file.
        - azure_settings.json ; any custom azure endpoints, deployments, and API keys are stored here.  
        - projects ; within the projects directory, you will find all of your raw and processed data files (e.g., transcripts, codes, themes).
        - custom_prompts.json ; if you create custom prompts, they will be saved here. They can be deleted from file or via the :orange[📢 Prompt Settings] page.
        -       
    """)
    


if __name__ == "__main__":
    main()