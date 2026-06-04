import streamlit as st
from ui_utils import centered_column_with_number, create_circle_number

'''
Abstract page instructions & blurb to avoid repetitions & walls of text in code

'''


def project_setup_instructions():
    st.header(":orange[Project Set Up & File Management]")
    
    with st.expander("Instructions"):
        st.write("""
        The "Folder Set Up" page is where you'll begin your thematic analysis journey. This page allows you to create new projects, manage existing ones, and upload the files you want to analyze. Here's how to use it:
        """)

        # 1. Creating a New Project
        st.subheader(":orange[1. Creating a New Project]")
        st.write("""
        - Enter a unique name for your project in the "Enter new project name:" text box.
        - Hit enter or click the "Create Project" button to set up your project.
        - The system will create a new folder structure for your project, including subfolders for data, initial codes, reduced codes, themes, and more.
        """)

        st.code("""
        YOUR_PROJECT_NAME/          # The name you assign to your project.
        ├── data/                   # This folder holds all of your raw data files (e.g., interview transcripts).
        ├── initial_codes/          # After initial codes have been parsed, the resultant files are stored here.
        ├── reduced_codes/          # This folder contains the results from your reduction of codes processing.
        ├── themes/                 # Themes derived from reduced codes.
        ├── theme_books/            # Combines outputs from above to generate a file with structure theme > reduced codes > initial codes > quotes > source files.
        └── expanded_reduced_codes/ # Contains expanded view of reduced_codes; needed for matching sources, quotes, and codes.
        """, language="")

        # 2. Selecting an Existing Project
        st.subheader(":orange[2. Selecting an Existing Project]")
        st.write("""
        - Use the dropdown menu labeled "Select a project:" to choose from your existing projects.
        - Once selected, you'll see the project name displayed and have options to manage its files.
        """)

        # 3. Uploading Files
        st.subheader(":orange[3. Uploading Files]")
        st.write("""
        - With a project selected, you'll see a file uploader labeled "Upload interviews .txt files".
        - You can drag and drop multiple .txt files or click to browse and select them.
        - Files will be automatically uploaded when selected or dropped.
        - Successful uploads will be confirmed with a message.
        - Note: Only .txt files are allowed. For other file types, please use the file_upload_and_conversion page to convert a range of other text formats to .txt
        """)

        # 4. Managing Existing Files
        st.subheader(":orange[4. Managing Existing Files]")
        st.write("""
        - Below the file uploader, you'll see a list of all files currently in your project.
        - Each file has a checkbox next to it. Select the checkbox for any files you want to delete.
        - Click 'Delete Selected Files' to remove selected files from your project. 
        """)

        # 5. Deleting a Project
        st.subheader(":orange[5. Deleting a Project]")
        st.write("""
        - If you need to remove an entire project, select it from the dropdown and click the "Delete Project" button.
        - This action will remove all files and folders associated with the project, so use it carefully.
        """)

        # 6. API Key Management
        st.subheader(":orange[6. API Key Management]")
        st.write("""
        - In the sidebar (on all pages), you'll find options to manage your API keys for different AI providers.
        - You can add new keys, view existing ones (last few digits only for security), and delete keys as needed.
        """)

        # Tips
        st.subheader(":orange[Tips]")
        st.write("""
        - Always double-check your project selection before uploading or deleting files.
        - It's recommended to use descriptive names for your projects to easily identify them later.
        - If you're analyzing interviews, consider naming your files consistently (e.g., "1_Interview_topic.txt", "2_Interview_topic.txt").
        - Remember that deleting files or projects is permanent and cannot be undone.
        """)

        st.info(":bulb: By properly setting up your project and managing your files here, you'll have a solid foundation for the subsequent steps in your thematic analysis process.")


def initial_coding_instructions():

    search_gif = "pages/animations/search_rounded.gif"
    highlighter_gif = "pages/animations/highlight_rounded.gif"
    order_gif = "pages/animations/order_rounded.gif"


    search_text = 'During initial coding, the LLM analyzes each document…'
    highlighter_text = '...to extract quotes based on the user prompt…'
    order_text = "...which are named and compiled into lists of 'initial codes'."

    st.header(":orange[Initial Coding]")

    with st.expander("Instructions"):
        st.write("""
        The Initial Coding page is where you begin the analysis of your data. This step involves generating initial codes for each of your uploaded files using Large Language Models (LLMs). Read the guide below to find out more.
        """)

        # Create columns for layout for gifs and main points
        col1, col2, col3 = st.columns(3)

        # Display content in each column
        centered_column_with_number(col1, 1, search_text, search_gif)
        centered_column_with_number(col2, 2, highlighter_text, highlighter_gif)
        centered_column_with_number(col3, 3, order_text, order_gif)

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
        st.subheader(":orange[1. Project Selection]")
        st.write("""
        - Use the dropdown menu to select the project you want to work on.
        - If you haven't set up a project yet, you'll be prompted to go to the 'Folder Set Up' page first.
        """)

        st.subheader(":orange[2. File Selection]")
        st.write("""
        - Once a project is selected, you'll see a list of files available for processing.
        - You can select individual files or use the "Select All" checkbox to choose all files at once.
        - :orange[Files that have already been processed will be marked with a '⚠️ Already processed' label .]
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

def reduce_codes_instructions():

    process_gif = "pages/animations/process_rounded.gif"
    compare_gif = "pages/animations/compare_rounded.gif"
    merge_gif = "pages/animations/merge_rounded.gif"

    process_text = 'The LLM recursively compares all initial codes...'
    compare_text = '...to identify duplicates based on the prompt...'
    merge_text = "...which are merged into a set of unique codes."

    st.header(":orange[Reduction of Codes]")

    with st.expander("Instructions"):

        st.write("""
        The Reduction of Codes page is where you refine and consolidate the initial codes generated in the previous step. 
        This process helps to identify patterns and reduce redundancy in your coding.
        """)
        col1, col2, col3 = st.columns(3)
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
        - Select your project.
        - Choose the files you want to process.
        """)

        st.subheader(":orange[2. LLM Settings]")
        st.write("""
        - Choose the model.
        - Select or edit the prompt.
        - Adjust temperature and top_p.
        """)

        st.subheader(":orange[3. Processing and Results]")
        st.write("""
        - Choose 'automatic' or 'incremental' processing.
        - Click 'Process' to start.
        - Once complete, view and download results.
        """)

        st.subheader(":orange[4. Saved Reduced Codes]")
        st.write("""
        - View previously processed reduced code files.
        - Download or delete them as needed.
        """)

        st.info("Code reduction helps refine your analysis and prepare for thematic identification.")

def finding_themes_instructions():

    processing_gif = "pages/animations/data_processing_rounded.gif"
    connection_gif = "pages/animations/connection_rounded.gif"

    processing_text = 'The LLM analyses the reduced unique codes'
    connection_text = '...and groups them into overarching themes...'

    st.header(":orange[Finding Themes]")

    # Display instructions in an expandable section
    with st.expander("Instructions"):
        st.write("""
        The Finding Themes page is where you identify overarching themes from your reduced codes. This step helps you synthesize your data into meaningful patterns. 
        """)

        # Create columns for layout for gifs and main points
        col1, col2= st.columns(2)

        # Display content in each column
        centered_column_with_number(col1, 1, processing_text, processing_gif)
        centered_column_with_number(col2, 2, connection_text, connection_gif)

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

def saturation_metric_instructions():
    st.header(":orange[Measure saturation]")

    # Display guide in an expandable section
    with st.expander("Guide to ITS"):
        
        st.subheader(":orange[Introduction to Thematic Analysis and Saturation]")

        st.write("""
        Thematic Analysis (TA) is a method used in qualitative research to identify and analyze patterns or themes within data. When conducting TA, researchers often seek to ensure that their analysis is comprehensive and captures the breadth of themes present in the data. One way to measure the completeness of this analysis is by assessing **saturation**. Saturation is a concept indicating that further analysis would yield little to no new information or themes, suggesting that the researcher has fully explored the data.
        """)

        st.subheader(":orange[What is the Saturation Metric?]")

        st.info("""
        In the context of this tool, saturation is quantitatively assessed using a metric called **Initial Thematic Saturation (ITS)**. ITS focuses on the emergence of new codes during the analysis. The metric is particularly important when using Large Language Models (LLMs) for TA, as it helps determine if the model's analysis is thorough.
        """)

        st.subheader(":orange[Understanding ITS: A Simplified Explanation]")

        st.write(":green[1. Themes and Codes]")
        st.write("""
        - In TA, **codes** are labels given to specific pieces of data that represent a concept or idea. Multiple codes can combine into a **theme**, which is a broader pattern identified in the data.
        - When analyzing data, the goal is to identify these themes by coding the data. Initially, many new codes are created, but as the analysis continues, the occurrence of new codes should decrease if the data is being thoroughly analyzed—this decrease indicates saturation.
        """)

        st.write(":green[2. How ITS is Measured]")
        st.write("""
        - **Cumulative Total Codes**: As you analyze more data (e.g., more interviews), you continue to add to a list of all codes identified—this is your cumulative total.
        - **Cumulative Unique Codes**: Simultaneously, you track how many of these codes are unique (i.e., not duplicates). As analysis continues, fewer new unique codes should appear, indicating that the analysis is approaching saturation.
        - **Saturation Indicator**: The saturation metric is calculated as the ratio between the rate at which new unique codes are identified and the total number of codes. As you progress, this ratio decreases, indicating that you are identifying fewer new ideas—the data is becoming saturated.
        """)

        st.write(":green[3. Interpreting ITS]")
        st.write("""
        - A higher ITS ratio indicates less saturation (many new codes are still emerging), while a lower ITS ratio indicates more saturation (few new codes are emerging). 
        """)

        st.subheader(":orange[Why ITS is Important]")

        st.warning("""
        For new users, understanding ITS is crucial because it provides a measure of how well an analysis captures the richness of the data. If the ITS metric shows that saturation has been reached, it suggests that the themes identified are likely to be robust and comprehensive. Conversely, if saturation has not been reached, it may indicate that more data or analysis is needed.
        """)

        st.subheader(":orange[Conclusion]")

        st.success("""
        In summary, ITS is a valuable tool for ensuring the validity of thematic analysis, particularly when using advanced tools like LLMs. By tracking the emergence of new codes, researchers can quantitatively assess whether their analysis is complete and whether they have thoroughly explored the themes within their data.
        """)

        st.info("See our paper on saturation and LLMs (https://arxiv.org/pdf/2401.03239) for more information.")

def pairwise_reduce_codes_instructions():

    process_gif = "pages/animations/process_rounded.gif"
    compare_gif = "pages/animations/compare_rounded.gif"
    merge_gif = "pages/animations/merge_rounded.gif"

    process_text = 'The LLM compares codes between pairs of files...'
    compare_text = '...to identify similar codes across different sources...'
    merge_text = "...which are merged into a unified set of codes."

    st.header(":orange[Pairwise Reduction of Codes]")

    with st.expander("Instructions"):

        st.write("""
        The Pairwise Reduction page offers an alternative approach to code reduction that compares codes between pairs of files rather than comparing each code against all others. 
        This method significantly reduces the number of API calls while maintaining effective code consolidation.
        """)
        col1, col2, col3 = st.columns(3)
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
        - Choose at least 2 files containing initial codes to compare.
        - Use the "Select All" checkbox to quickly select all available files.
        """)

        st.subheader(":orange[2. Pairwise Comparison Settings]")
        st.write("""
        - **All Pairs**: Compares each file with every other file (more thorough but more API calls).
        - **Sequential Pairs**: Compares each file only with the next file in the list (fewer API calls).
        - The system shows you which file pairs will be compared before processing.
        """)

        st.subheader(":orange[3. LLM Settings]")
        st.write("""
        - Choose the AI model for the analysis.
        - Select or customize the comparison prompt.
        - Adjust temperature and top_p parameters to control the AI's behavior.
        - Enable "Include Quotes" for more context-aware comparisons.
        - Toggle "Include merge explanation" to get detailed reasoning for merged codes.
        """)

        st.subheader(":orange[4. Processing and Results]")
        st.write("""
        - Click 'Process' to start the pairwise comparison.
        - The system will:
          - Compare codes between the selected file pairs
          - Identify similar codes across files
          - Merge similar codes into unified representations
        - View the reduced codes with their descriptions and sources.
        - Download results as CSV files for further analysis.
        """)

        st.subheader(":orange[5. Reduction Statistics]")
        st.write("""
        - See the total number of original codes across all files.
        - View the final number of reduced codes.
        - Check the reduction percentage to understand the consolidation achieved.
        """)

        st.subheader(":orange[Key Advantages]")
        st.write("""
        - :orange[Efficiency]: Fewer API calls compared to 1-vs-all comparison approach.
        - :orange[Scalability]: Better suited for projects with many files or codes.
        - :orange[Flexibility]: Choose between thorough (all pairs) or efficient (sequential) comparison modes.
        - :orange[Transparency]: See exactly which files are being compared before processing.
        """)

        st.subheader(":orange[Tips]")
        st.write("""
        - For initial exploration, try "Sequential Pairs" mode to get quick results with fewer API calls.
        - Use "All Pairs" mode when you need the most comprehensive code reduction.
        - If you have files from different sources or time periods, consider the order when using sequential mode.
        - Review the file pairs before processing to ensure the comparison strategy makes sense for your data.
        """)

        st.info("Pairwise reduction offers a balanced approach between thoroughness and efficiency, making it ideal for larger projects or when API usage is a concern.")
