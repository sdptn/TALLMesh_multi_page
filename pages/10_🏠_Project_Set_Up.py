# Import necessary libraries
import os
import streamlit as st
from api_key_management import manage_api_keys
import shutil
from project_utils import get_projects
from instructions import project_setup_instructions
from file_conversion_utils import convert_to_txt
import stat
import time #added to hopefully fix project deletion error by allowing for read-only files to be deleted after a small delay

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Define the directory where all projects will be stored
PROJECTS_DIR = 'projects'
FOLDER_ORDER = ['data', 'initial_codes', 'pairwise_reduced_codes', 'expanded_pairwise_reduced_codes', 'themes', 'theme_books']

def get_project_structure(project_name):
    structure = {folder: [] for folder in FOLDER_ORDER} # Initialize structure with empty lists for each folder
    project_path = os.path.join(PROJECTS_DIR, project_name) # Construct the full path to the project folder    
    for folder in FOLDER_ORDER:
        folder_path = os.path.join(project_path, folder)
        if os.path.exists(folder_path):
            structure[folder] = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    return structure


# Function to delete multiple files
def delete_files(file_paths):
    """
    Delete multiple files across different folders.
    
    Args:
    file_paths (list): List of full file paths to delete
    
    Returns:
    list: List of successfully deleted file paths
    """
    deleted_files = []
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(file_path)
            except Exception as e:
                st.error(f"Error deleting {os.path.basename(file_path)}: {str(e)}")
    return deleted_files

# Function to handle file uploads for a project
def handle_file_upload():
    """
    Process uploaded files for a given project.

    This function saves .txt files directly and converts other supported files
    to .txt before saving them into the project's data folder.
    """
    if st.session_state.uploaded_files:
        project_name = st.session_state.selected_project
        saved_files, skipped_files, failed_files = save_or_convert_uploaded_files(
            st.session_state.uploaded_files, project_name
        )

        message_parts = []

        if saved_files:
            message_parts.append(
                f"Files uploaded successfully: {', '.join(saved_files)}"
            )

        if skipped_files:
            message_parts.append(
                f"Skipped files (already exist): {', '.join(skipped_files)}"
            )

        if failed_files:
            message_parts.append(
                f"Failed to process: {', '.join(failed_files)}"
            )

        st.session_state.message = (
            "\n\n".join(message_parts)
            if message_parts
            else "No new files were uploaded."
        )

        if failed_files:
            st.session_state.message_type = "warning"
        elif saved_files:
            st.session_state.message_type = "success"
        else:
            st.session_state.message_type = "info"

    else:
        st.session_state.message = "Please select files to upload."
        st.session_state.message_type = "warning"

def save_or_convert_uploaded_files(uploaded_files, project_name):
    """
    Save uploaded .txt files directly and convert other files to .txt.
    
    Args:
    uploaded_files (list): List of uploaded file objects from Streamlit's file_uploader
    project_name (str): Name of the current project

    Returns: 
    tuple: (saved_files, skipped_files, failed_files)    
    """  

    data_folder = os.path.join(PROJECTS_DIR, project_name, 'data')
    saved_files = []
    skipped_files = []
    failed_files = []

    for file in uploaded_files:
        try: 
            original_name = file.name
            txt_name = os.path.splitext(original_name)[0] + ".txt"
            txt_path = os.path.join(data_folder, txt_name)

            # Save txt files directly
            if original_name.lower().endswith('.txt'):
                direct_path = os.path.join(data_folder, original_name)

                if os.path.exists(direct_path):
                    skipped_files.append(original_name)
                else:
                    with open(direct_path, "wb") as f:
                        f.write(file.getbuffer())
                    saved_files.append(original_name)

            # Convert other files to txt
            else:
                if os.path.exists(txt_path):
                    skipped_files.append(original_name)
                else:
                    converted_file = convert_to_txt(file, project_name)
                    saved_files.append(converted_file)

        except Exception as e:
            failed_files.append(f"{file.name} ({str})")

    return saved_files, skipped_files, failed_files

# Function to create a new project
def create_project(project_name):
    """
    Create a new project with the necessary folder structure.

    This function creates a main project folder and several subfolders for
    organizing different stages of the thematic analysis process.

    Args:
    project_name (str): Name of the project to be created

    Side effects:
    - Creates a new folder structure in the PROJECTS_DIR
    """
    project_path = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(project_path, exist_ok=True)
    
    for folder in FOLDER_ORDER:
        os.makedirs(os.path.join(project_path, folder), exist_ok=True) 


# Function to remove files from a project
def remove_files(project_name, filenames):
    """
    Remove specified files from a project's data folder.

    Args:
    project_name (str): Name of the project
    filenames (list): List of file names to be removed

    Side effects:
    - Deletes specified files from the project's data folder
    """
    for filename in filenames:
        file_path = os.path.join(PROJECTS_DIR, project_name, 'data', filename)
        if os.path.exists(file_path):
            os.remove(file_path)

# Function to remove an entire project
def remove_project(project_name):
    """
    Remove an entire project and all its contents.

    This function deletes the project folder and all its subfolders and files.
    It also updates the session state to reflect the changes.

    Args:
    project_name (str): Name of the project to be removed

    Side effects:
    - Deletes the project folder and all its contents
    - Updates session state variables
    - Sets success/error messages in session state
    """
    project_path = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(project_path):
        try: 
            # shutil.rmtree(project_path) #Error not allowing deletion of projects
            def remove_readonly(func, path, exc_info):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            time.sleep(0.5) # Small delay to ensure all files are deleted before proceeding
            shutil.rmtree(project_path, onerror=remove_readonly)

            st.session_state.message = f"Project '{project_name}' has been successfully removed."
            st.session_state.message_type = "success"
            # Update the projects list in session state
            st.session_state.projects = get_projects()
            st.session_state.selected_project = None
            st.session_state.delete_project = None  # Reset the delete_project flag
        except Exception as e:
            st.session_state.message = f"Error removing project '{project_name}': {str(e)}"
            st.session_state.message_type = "error"
    else:
        st.session_state.message = f"Project '{project_name}' does not exist."
        st.session_state.message_type = "warning"


# Initialize session state variables
# These variables persist across Streamlit reruns and store important application state
if 'message' not in st.session_state:
    st.session_state.message = None
    st.session_state.message_type = None

if 'projects' not in st.session_state:
    st.session_state.projects = get_projects()

if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

if 'delete_project' not in st.session_state:
    st.session_state.delete_project = None

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = None
#   st.session_state.uploaded_files = None #hopefully f

# ==============================================================================
#                             MAIN STREAMLIT FUNCTION
# ==============================================================================

# Main function to run the Streamlit app
def main():
    """
    Main function to run the Streamlit application.

    This function sets up the user interface for project management, including:
    - Creating new projects
    - Selecting existing projects
    - Uploading files to projects
    - Managing existing files in projects
    - Deleting projects
    
    It also handles the display of instruction text and manages the overall flow of the application.
    """

    # Project setyp instructions
    project_setup_instructions()
    
    st.write(":green[Select an existing project or create a new one to get started.]")
    
    # Update projects list at the start of each run
    st.session_state.projects = get_projects()

    # Initialize selected_project in session state if it doesn't exist
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None

    # Check if a project needs to be deleted
    if 'delete_project' in st.session_state and st.session_state.delete_project:
        remove_project(st.session_state.delete_project)
        st.session_state.delete_project = None
        st.session_state.selected_project = None
        st.rerun()

    # Project creation UI
    with st.form(key='create_project_form'):
        new_project = st.text_input("Enter new project name:")
        create_project_button = st.form_submit_button("Create Project")

    if create_project_button:
        if new_project and new_project not in st.session_state.projects:
            create_project(new_project)
            st.session_state.message = f"Project '{new_project}' created successfully!"
            st.session_state.message_type = "success"
            st.session_state.projects = get_projects()
            st.session_state.selected_project = new_project
            st.rerun()
        else:
            st.session_state.message = "Invalid project name or project already exists."
            st.session_state.message_type = "error"

    # Project selection UI
    project_options = ["Select a project..."] + st.session_state.projects
    index = 0 if st.session_state.selected_project is None else project_options.index(st.session_state.selected_project)
    selected_project = st.selectbox("Select a project:", project_options, index=index, key="project_selector")
    
    if selected_project != "Select a project...":
        st.session_state.selected_project = selected_project
    else:
        st.session_state.selected_project = None

    # Project management UI
    if st.session_state.selected_project:
        col1, col2 = st.columns([0.88, 0.12])
        col1.subheader(f"Project: {st.session_state.selected_project}")
        
        # Create a placeholder for the delete button and confirmation
        delete_placeholder = col2.empty()

        # Initialize session state for delete confirmation
        if 'show_delete_confirm' not in st.session_state:
            st.session_state.show_delete_confirm = False

        # Show delete button or confirmation based on state
        if not st.session_state.show_delete_confirm:
            if delete_placeholder.button("Delete Project"):
                st.session_state.show_delete_confirm = True
                st.rerun()
        else:
            with delete_placeholder.container():
                st.button("Cancel", key="cancel_delete", on_click=lambda: setattr(st.session_state, 'show_delete_confirm', False))
                st.button("Confirm", key="confirm_delete", on_click=lambda: [remove_project(st.session_state.selected_project), setattr(st.session_state, 'selected_project', None), setattr(st.session_state, 'show_delete_confirm', False)])
            
            st.warning(f"Are you sure you want to delete the project '{st.session_state.selected_project}'? This action cannot be undone.")

        st.write("Upload files below to get started or manage files in the section below")
        
        # File upload UI
        st.file_uploader(
            "Upload interviews files (.txt, .pdf, .docx, .rtf and other text files)", 
            accept_multiple_files=True,  
            key="uploaded_files", 
            on_change=handle_file_upload)
        # New expander section for project structure to let users delete files without having to go into file explorer
        with st.expander("View Project Structure & Files"):
            project_structure = get_project_structure(st.session_state.selected_project)
            files_to_delete = []  # Move this outside the folder loop
            
            # Display files by folder
            for folder in FOLDER_ORDER:
                files = project_structure.get(folder, [])
                st.subheader(f":file_folder: {folder}")
                if files:
                    for file in files:
                        file_path = os.path.join(PROJECTS_DIR, st.session_state.selected_project, folder, file)
                        if st.checkbox(f":page_facing_up: {file}", key=f"checkbox_{file_path}"):
                            files_to_delete.append(file_path)
                else:
                    st.write("  (empty)")
            
            # Single delete button for all selected files
            if files_to_delete:
                col1, col2 = st.columns([0.7, 0.3])
                with col1:
                    st.write(f"Selected {len(files_to_delete)} file(s) for deletion")
                with col2:
                    if st.button("Delete Selected Files", type="primary", use_container_width=True):
                        deleted_files = delete_files(files_to_delete)
                        if deleted_files:
                            folders_affected = len(set(os.path.dirname(f) for f in deleted_files))
                            st.success(f"Successfully deleted {len(deleted_files)} file(s) from {folders_affected} folder(s)")
                            st.rerun()

    else:
        st.write("Please select or create a project to continue.")

    # Display message if it exists in session state
    if 'message' in st.session_state and st.session_state.message:
        if st.session_state.message_type == "success":
            st.toast(st.session_state.message, icon="😍")
        elif st.session_state.message_type == "info":
            st.toast(st.session_state.message, icon="⚠️")
        elif st.session_state.message_type == "warning":
            st.warning(st.session_state.message)
        elif st.session_state.message_type == "error":
            st.error(st.session_state.message)
        
        # Clear the message after displaying
        st.session_state.message = None
        st.session_state.message_type = None

    # Call API key saving function
    manage_api_keys()

# Entry point of the script
if __name__ == "__main__":
    main()