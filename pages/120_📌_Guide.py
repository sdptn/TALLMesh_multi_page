# -*- coding: utf-8 -*-
"""
TALLMesh Guide Module

This module provides a comprehensive guide for using the TALLMesh (Thematic Analysis with Large Language Models) application.
It includes detailed explanations of each step in the thematic analysis process, from project setup to visualization of results.

The guide is presented using Streamlit's interactive features, allowing users to explore different sections of the application
and understand how to effectively use each component.

Created on Sun Feb  4 15:28:10 2024
@author: Stefano

Dependencies:
    - streamlit: For creating the interactive web application
    - api_key_management: Custom module for managing API keys

Usage:
    This script is intended to be run as part of a Streamlit multi-page application.
    It will display as the "Guide" page in the TALLMesh application.

Note:
    Ensure that all dependencies are installed and the api_key_management module is available in the project directory.
"""

import streamlit as st


# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Videos
project_setup_video_file = open("pages/animations/project_set_up.webm", "rb")
project_set_up_video = project_setup_video_file.read()

initial_coding_video_file = open("pages/animations/initial_coding.webm", "rb")
initial_coding_video = initial_coding_video_file.read()

reduction_of_codes_video_file = open("pages/animations/reduction_of_codes.webm", "rb")
reduction_of_codes_video = reduction_of_codes_video_file.read()

finding_themes_video_file = open("pages/animations/finding_themes.webm", "rb")
finding_themes_video = finding_themes_video_file.read()

add_prompt_video_file = open("pages/animations/add_prompt.webm", "rb")
add_prompt_video = add_prompt_video_file.read()


def main():
    """
    Main function to render the TALLMesh guide page.
    
    This function creates the structure and content of the guide page, including:
    - An introduction to TALLMesh
    - Detailed explanations of each step in the thematic analysis process
    - Tips and best practices for using the application
    
    The content is organized into expandable sections for easy navigation.
    """
    # Display the main header and introduction
    st.header(":orange[Welcome to TALLMesh: Thematic Analysis with Large Language Models]")

    st.write("""
    This application is designed to assist researchers and students in conducting thematic analysis 
    using large language models (LLMs). Our approach is inspired by the widely-used Braun and Clarke 
    method, adapted for the capabilities of modern AI.

    TALLMesh aims to streamline the process of qualitative data analysis, offering a novel way to 
    interact with your research data. While it leverages the power of LLMs, it's important to note 
    that this tool is meant to augment, not replace, the researcher's critical thinking and interpretive skills.

    :blue[Key features of TALLMesh include:]
    - Automated initial coding
    - Assistance in reducing and refining codes
    - Support in identifying and defining themes
    - Integration with popular LLM providers

    As you use this tool, remember that the AI is a collaborator in your research process. Always 
    critically evaluate the outputs and use your expertise to guide the analysis.
    """)

    st.info("""
    :bulb: **Note for researchers:** While TALLMesh can significantly speed up parts of the thematic 
    analysis process, it's crucial to maintain rigorous oversight. The tool's suggestions should be 
    thoroughly reviewed and adjusted based on your research context and objectives.
    """)

    # Display the getting started section
    st.subheader(":orange[Getting Started]")

    st.write("""
    High level overview:
    \n:orange[1.] Set up your project and upload your data
    \n:orange[2.] Conduct initial coding phase
    \n:orange[3.] Reduction of duplicate/highly similar codes
    \n:orange[4.] Generate themes from reduced codes
    \n:orange[5.] Finalise theme book
    \n:orange[6.] Metrics and visualisations

    Each page of the application corresponds to one of the stages outlined above. 
    Let's explore each of these in more detail...
    """)

    st.divider()

    # Create expandable sections for each main part of the guide
    create_project_setup_guide()
    create_initial_coding_guide()
    create_code_reduction_guide()
    create_finding_themes_guide()
    #create_finalized_theme_book_guide() # deprecated - finalised theme book now generated in finding themes page automatically
    create_metrics_visualizations_guide()
    create_custom_prompt_management_guide()



import streamlit as st


def create_project_setup_guide():
    """
    Creates an expandable section explaining the project setup process.
    """
    with st.expander("Project Set Up"):
        st.header(":orange[Project and File Management]")

        st.write("""
        The "Project Set Up" page is where you'll begin your thematic analysis journey. This page allows you to create new projects, manage existing ones, and upload the files you want to analyze. Here's how to use it:
        """)

        st.video(project_set_up_video, loop = True, autoplay = True)

        st.subheader(":orange[1. Creating a New Project]")
        st.write("""
        - Enter a unique name for your project in the "Enter new project name:" text box.
        - Click the "Create Project" button to set up your project.
        - The system will create a new folder structure for your project, including subfolders for data, initial codes, reduced codes, themes, and more.
        """)

        st.subheader(":orange[2. Selecting an Existing Project]")
        st.write("""
        - Use the dropdown menu labeled "Select a project:" to choose from your existing projects.
        - Once selected, you'll see the project name displayed and have options to manage its files.
        """)

        st.subheader(":orange[3. Uploading Files]")
        st.write("""
        - With a project selected, you'll see a file uploader labeled "Upload interviews .txt files".
        - You can drag and drop multiple .txt files or click to browse and select them.
        - Click the "Upload Files" button to add these files to your project's data folder.
        - Successful uploads will be confirmed with a message.
        """)

        st.subheader(":orange[4. Managing Existing Files]")
        st.write("""
        - Below the file uploader, you'll see a list of all files currently in your project, separated into folders
        - Each folder holds files for a given stage of the thematic analysis process
        - You can delete files by selecting the checkbox to the left of the file you want to delete and clicking 'Delete Selected'
        """)

        st.subheader(":orange[5. Deleting a Project]")
        st.write("""
        - If you need to remove an entire project, select it from the dropdown and click the "Delete Project" button.
        - This action will remove all files and folders associated with the project, so use it carefully.
        """)

        st.subheader(":orange[6. API Key Management]")
        st.write("""
        - The PCSS deployment is preconfigured to access the required backend model.
        """)

        

        st.subheader(":orange[Tips]")
        st.write("""
        - Always double-check your project selection before uploading or deleting files.
        - It's recommended to use descriptive names for your projects to easily identify them later.
        - If you're analyzing interviews, consider naming your files consistently (e.g., "1_Interview_topic.txt", "2_Interview_topic.txt").
        - Remember that deleting files or projects is permanent and cannot be undone.
        """)

        st.info(":bulb: By properly setting up your project and managing your files here, you'll have a solid foundation for the subsequent steps in your thematic analysis process.")

def create_initial_coding_guide():
    """
    Creates an expandable section explaining the initial coding process.
    """
    with st.expander("Initial Coding"):
        st.header(":orange[Initial Coding]")

        st.write("""
        The Initial Coding page is where you begin the analysis of your data. This step involves generating initial codes for each of your uploaded files using AI assistance. Here's how to use this page:
        """)

        st.video(initial_coding_video, loop=True, autoplay=True)

        st.subheader(":orange[1. Project Selection]")
        st.write("""
        - Use the dropdown menu to select the project you want to work on.
        - If you haven't set up a project yet, you'll be prompted to go to the 'Folder Set Up' page first.
        """)

        st.subheader(":orange[2. File Selection]")
        st.write("""
        - Once a project is selected, you'll see a list of files available for processing.
        - You can select individual files or use the "Select All" checkbox to choose all files at once.
        - :orange[Files that have already been processed will be marked with a warning icon.]
        """)

        st.subheader(":orange[3. LLM Settings]")
        st.write("""
        - Choose the AI model you want to use for the analysis from the dropdown menu. 
        - Select a preset prompt or edit the provided prompt to customize your analysis.
        - Adjust the model temperature and top_p values using the sliders. These parameters control the creativity and randomness of the AI's output.
        """)

        st.info("Make sure you have provided an API key for the provider of the model you have selected (e.g., Anthropic, Azure, OpenAI)")

        st.subheader(":orange[4. Processing Files]")
        st.write("""
        - After configuring your settings, click the "Process" button to start the initial coding.
        - :orange[The system will process each selected file and generate initial codes.]
        - A progress bar will show you the status of the processing.
        """)

        st.subheader(":orange[5. Viewing Results]")
        st.write("""
        - Once processing is complete, you'll see the results for each file in expandable sections.
        - Each section will show a table with the generated codes, their descriptions, and relevant quotes.
        - You can download the results for each file individually using the provided download buttons.
        """)

        st.subheader(":orange[6. Saved Initial Codes]")
        st.write("""
        - At the bottom of the page, you'll find an expandable section showing previously processed files.
        - You can view, delete, or download these saved initial codes.
        """)

        st.subheader(":orange[Tips]")
        st.write("""
        - :orange[Experiment with different prompts and model settings to get the best results for your data.]
        - If you're not satisfied with the initial codes, you can delete them and reprocess the file with different settings.
        - Remember that this is just the first step in the analysis process. The codes generated here will be refined in later stages.
        """)

        st.info("Initial coding sets the foundation for your thematic analysis. Take your time to review the generated codes and ensure they capture the essence of your data before moving on to the next stage.")

def create_code_reduction_guide():
    """
    Creates an expandable section explaining the code reduction process.
    """
    with st.expander("Reduction of Codes"):
        st.header(":orange[Reduction of Codes]")

        st.write("""
        The Reduction of Codes page is where you refine and consolidate the initial codes generated in the previous step. This process helps to identify patterns and reduce redundancy in your coding. Here's how to use this page:
        """)

        st.video(reduction_of_codes_video, loop=True, autoplay=True)

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
        - Choose whether you want the AI to process all files recursively or if you would like it to pause between files
        """)

        st.subheader(":orange[3. Processing and Results]")
        st.write("""
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
        st.write("""
        - :orange[Automatic merging:] The AI identifies similar codes and combines them, providing explanations for the merges.
        - :orange[Quote preservation:] All quotes associated with the original codes are retained and linked to the reduced codes.
        - :orange[Tracking changes:] The system keeps track of how initial codes map to reduced codes, maintaining traceability.
        - :orange[Saturation analysis:] The code reduction results can be used to assess thematic saturation in your analysis (see 'Saturation Metric).
        """)

        st.subheader(":orange[Tips]")
        st.write("""
        - Review the merged codes carefully to ensure the AI's decisions align with your understanding of the data.
        - If you're not satisfied with the reduction, you can adjust the prompt or model settings and reprocess the files.
        - :orange[Pay attention to the "Code Reduction Results" table.] A plateauing number of unique codes may indicate approaching saturation in your analysis.
        - Consider running the reduction process multiple times with different settings to compare results and ensure thorough analysis.
        """)

        st.info("Code reduction is a critical step in refining your analysis. It helps to consolidate your findings and prepare for the identification of overarching themes in the next stage.")

def create_finding_themes_guide():
    """
    Creates an expandable section explaining the process of finding themes.
    """
    with st.expander("Finding Themes"):
        st.header(":orange[Finding Themes]")

        st.write("""
        The Finding Themes page is where you identify overarching themes from your reduced codes. This step helps you synthesize your data into meaningful patterns. Here's how to use this page:
        """)

        st.video(finding_themes_video, loop=True, autoplay=True)

        st.subheader(":orange[1. Project and File Selection]")
        st.write("""
        - Select your project from the dropdown menu.
        - Once a project is selected, you'll see a list of reduced code files available for processing.
        - Choose the files you want to analyze. You can select individual files or use the "Select All" checkbox.
        """)

        st.subheader(":orange[2. LLM Settings]")
        st.write("""
        - Choose the AI model you want to use for theme identification.
        - Select a preset prompt or edit the provided prompt to guide the theme finding process.
        - Adjust the model temperature and top_p values using the sliders. These parameters influence the AI's creativity and output variability.
        """)

        st.subheader(":orange[3. Processing and Results]")
        st.write("""
        - Click the "Process" button to start finding themes.
        - The system will analyze the selected reduced code files and generate themes.
        - Once complete, you'll see:
        - An expandable section for each generated theme, showing the theme name, description, and associated codes.
        - A reference section showing all codes and their descriptions used in the analysis.
        - You can download the generated themes as a CSV file.
        """)

        st.subheader(":orange[4. Saved Themes]")
        st.write("""
        - At the bottom of the page, you'll find an expandable section showing previously generated theme files.
        - You can view, delete, or download these saved theme files.
        """)

        st.subheader("Key Features")
        st.write("""
        - :orange[Automated theme generation:] The AI identifies patterns across your reduced codes to suggest overarching themes.
        - :orange[Theme descriptions:] Each theme comes with a detailed description to explain its meaning and relevance.
        - :orange[Code mapping:] The system shows which codes are associated with each theme, maintaining the connection between your data and the higher-level themes.
        - :orange[Flexibility:] You can adjust the prompt and model settings to influence how themes are generated and organized.
        """)

        st.subheader(":orange[Tips]")
        st.write("""
        - Review the generated themes carefully. While the AI is helpful, your expertise and understanding of the context are crucial for validating and refining these themes.
        - :orange[Experiment with different prompts and settings] if you're not satisfied with the initial results. Different approaches can yield different insights.
        - Consider the number of themes generated. Too few might oversimplify your data, while too many might make it difficult to draw meaningful conclusions.
        - Use the reference section to understand how individual codes contribute to the larger themes.
        - Remember that theme generation is an iterative process. You may need to run this step multiple times, adjusting your approach based on the results.
        """)

        st.info("Finding themes is a crucial step in synthesizing your analysis. It helps you move from detailed codes to broader, more conceptual understanding of your data. Take your time to reflect on the themes and how they relate to your research questions.")

        st.header(":orange[Finalised Theme Book]")

        st.write("""
        The Finalised Theme Book is generated automatically once themes have been generated:
        """)

        st.subheader(":orange[1. Data Processing]")
        st.write("""
        - Once you've selected a project, the system will automatically process the data to create your theme book.
        - This process combines your themes with their associated codes, descriptions, and quotes.
        - :orange[No additional input is required] - the theme book is generated based on your previous work in the earlier stages.
        """)

        st.subheader(":orange[2. Viewing Results]")
        st.write("""
        - The results are presented in three main sections:
        1. :orange[Condensed Themes:] A concise view of your themes without the associated codes and quotes.
        2. :orange[Expanded Themes:] A detailed view including themes, codes, quotes, and sources.
        3. :orange[Merged Codes:] A reference section showing all your reduced codes.
        - Each section is displayed in a table format for easy reading and comparison.
        """)

        st.subheader(":orange[3. Saving and Downloading]")
        st.write("""
        - The system automatically saves two versions of your theme book:
        1. A condensed version with just the themes.
        2. An expanded version with all details including codes and quotes.
        - You can download the final theme book as a CSV file using the provided download button.
        """)

        st.subheader("Key Features")
        st.write("""
        - :orange[Automatic compilation:] The system pulls together all your work from previous stages into a coherent structure.
        - :orange[Multiple views:] You can see your analysis at different levels of detail, from high-level themes to specific quotes.
        - :orange[Traceability:] The expanded view allows you to trace each theme back to its constituent codes and original data sources.
        - :orange[Easy export:] You can easily save and share your final analysis as a CSV file.
        """)

        st.subheader("Tips")
        st.write("""
        - Take time to review the expanded themes carefully. This is your opportunity to see how everything fits together.
        - Use the condensed view for a quick overview, and the expanded view when you need to dive into the details.
        - :orange[Consider how your themes relate to each other.] Are there any overarching patterns or relationships between themes?
        - If you notice any inconsistencies or areas that need refinement, you can go back to earlier stages of the analysis and make adjustments.
        - The final theme book is an excellent resource for writing up your findings or preparing presentations about your analysis.
        """)

        st.info("The Finalised Theme Book represents the culmination of your thematic analysis. It provides a structured overview of your themes and their grounding in the data, which is crucial for ensuring the validity and reliability of your qualitative research. The following pages make use of these finalised themes for metrics and visualisations")

def create_metrics_visualizations_guide():
    """
    Creates an expandable section explaining the metrics and visualizations available in the application.
    """
    with st.expander("Metrics and Visualisations"):
        st.header(":orange[Visualization and Analysis Tools]")

        st.write("""
        The following pages provide powerful tools for visualizing your thematic analysis and assessing its completeness. These tools help you gain deeper insights into your data and the relationships between your themes and codes.
        """)

        st.subheader(":orange[1. Saturation Metric]")
        st.write("""
        The Saturation Metric page helps you assess the completeness of your analysis by measuring the rate at which new unique codes are being generated.

        Key features:
        - Calculates the Initial Thematic Saturation (ITS) metric.
        - Displays a graph showing the cumulative count of unique codes vs. total codes.
        - Provides a downloadable CSV of the code reduction results.

        How to use:
        - Select your project from the dropdown menu.
        - The system automatically processes the data from your initial coding and code reduction phases.
        - Review the ITS Metric and the graph to determine if you've reached saturation in your analysis.

        :orange[Tip:] A plateauing curve in the graph suggests you're approaching saturation, indicating that further data analysis may yield diminishing returns in terms of new insights.
        """)

        st.divider()

        st.subheader(":orange[2. Theme-Codes Icicle]")
        st.write("""
        The Theme-Codes Icicle page provides a hierarchical visualization of your themes, codes, and data.

        Key features:
        - Interactive icicle plot showing the hierarchy: Theme > Reduced Codes > Initial Code(s) > Quote(s) > Source.
        - Ability to select and focus on specific themes.
        - Hover functionality to view detailed descriptions.

        How to use:
        - Select your project from the dropdown menu.
        - Choose a specific theme to visualize from the dropdown menu.
        - Interact with the icicle plot:
        - Click on components to zoom in and see more detail.
        - Hover over elements to see descriptions and additional information.

        :orange[Tip:] Use this visualization to understand the relative sizes of your themes and the distribution of codes within them. It's particularly useful for identifying dominant themes and understanding the structure of your analysis.
        """)

        st.divider()

        st.subheader(":orange[3. Thematic Network Map]")
        st.write("""
        The Thematic Network Map page offers a network visualization of your entire thematic structure, from project level down to individual quotes.

        Key features:
        - Interactive network graph showing relationships between project, themes, reduced codes, initial codes, and quotes.
        - Color-coded nodes for easy identification of different levels in the hierarchy.
        - Ability to drag nodes for custom arrangement.

        How to use:
        - Select your project from the dropdown menu.
        - The system will generate and display the network map.
        - Interact with the map:
        - Drag nodes to rearrange the layout.
        - Zoom in/out using the mouse wheel.
        - Click on nodes to expand or collapse branches of the network.

        :orange[Tip:] This visualization is excellent for understanding the interconnections in your data. Pay attention to themes with many connections, as these may be central to your analysis.
        """)

        st.info("""
        These visualization tools provide different perspectives on your thematic analysis. Use them in combination to gain a comprehensive understanding of your data, verify the robustness of your analysis, and identify key insights and patterns.
        """)

def create_custom_prompt_management_guide():
    """
    Creates an expandable section explaining the custom prompt management process.
    """
    with st.expander("Custom Prompt Management"):
        st.header("Custom Prompts Management")
        st.write("The Custom Prompts Management page allows you to create, edit, and delete custom prompts for different stages of your thematic analysis. Here's how to use this page effectively:")

        st.video(add_prompt_video, loop=True, autoplay=True)

        st.subheader(":orange[1. Selecting Prompt Type]")
        st.write("At the top of the page, you'll find a dropdown menu to select the prompt type:")
        st.markdown("""
        - **Initial Coding**: For creating initial codes from your data.
        - **Reduction of Codes**: For merging and refining your codes.
        - **Finding Themes**: For identifying overarching themes from your codes.
        """)
        st.write("Select the prompt type you want to work with.")

        st.subheader(":orange[2. Viewing Existing Custom Prompts]")
        st.write("After selecting a prompt type, you'll see a list of existing custom prompts (if any) for that category.")
        st.markdown("""
        - Each prompt is displayed in an expandable section.
        - Click on a prompt name to view its details.
        """)

        st.subheader(":orange[3. Editing Existing Prompts]")
        st.write("To edit an existing custom prompt:")
        st.markdown("""
        1. Expand the prompt you want to edit.
        2. Modify the prompt text in the text area.
        3. Adjust the Temperature and Top P values using the number input fields.
        4. Click the "Update" button to save your changes.
        """)
        st.warning("Remember to maintain the JSON structure in your prompt to ensure proper functionality.")

        st.subheader(":orange[4. Deleting Custom Prompts]")
        st.write("To delete a custom prompt:")
        st.markdown("""
        1. Expand the prompt you want to delete.
        2. Click the "Delete" button at the bottom of the expanded section.
        3. Confirm the deletion when prompted.
        """)
        st.warning("Deleted prompts cannot be recovered, so be sure before deleting.")

        st.subheader(":orange[5. Creating New Custom Prompts]")
        st.write("To create a new custom prompt:")
        st.markdown("""
        1. Scroll to the "Add New Custom Prompt" section at the bottom of the page.
        2. Enter a name for your new prompt in the "Name for new prompt" field.
        3. Edit the pre-populated prompt in the "New prompt" text area. 
        - The pre-populated text includes the required JSON structure for the selected prompt type.
        - Modify the [INSERT SPECIFIC INSTRUCTIONS HERE] section with your custom instructions.
        4. Set the desired Temperature and Top P values.
        5. Click the "Add Custom Prompt" button to create your new prompt.
        """)
        st.info("Tip: The pre-populated prompt structure helps ensure your custom prompt will work correctly with the system. Try to maintain this structure while customizing your instructions.")

        st.subheader(":orange[6. Using Custom Prompts]")
        st.write("After creating custom prompts, you can use them in their respective analysis stages:")
        st.markdown("""
        - Custom Initial Coding prompts will appear in the prompt selection on the Initial Coding page.
        - Custom Reduction of Codes prompts will be available on the Reduction of Codes page.
        - Custom Finding Themes prompts can be selected on the Finding Themes page.
        """)
        st.info("Your custom prompts will appear alongside the preset prompts in these pages.")

        st.write("Remember, well-crafted prompts can significantly improve the quality of your analysis. Take time to refine your prompts based on your specific research needs and the nature of your data.")

if __name__ == "__main__":
    main()