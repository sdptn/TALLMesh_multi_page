# Import necessary libraries
import os
import streamlit as st
import json
from api_key_management import manage_api_keys
import shutil
from project_utils import get_projects
from instructions import project_setup_instructions
import stat
import time #added to hopefully fix project deletion error by allowing for read-only files to be deleted after a small delay

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Define the directory where all projects will be stored
PROJECTS_DIR = 'projects'
FOLDER_ORDER = ['data', 'initial_codes', 'reduced_codes', 'expanded_reduced_codes', 'themes', 'theme_books']

def get_project_structure(project):
    structure = {folder: [] for folder in FOLDER_ORDER} # Initialize structure with empty lists for each folder
    project_path = os.path.join(PROJECTS_DIR, project) # Construct the full path to the project folder    
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
    
    This function saves valid .txt files to the project's data folder and provides
    feedback messages about the upload process.

    Side effects:
    - Saves valid files to the project's data folder
    - Updates session state with success/warning messages about the upload process
    """
    uploaded = st.session_state.get("uploaded_files")
    if uploaded:
        project_name = st.session_state.selected_project
        saved_files, invalid_files = save_uploaded_files(uploaded, project_name)
        if saved_files:
            st.session_state.message = f"Files uploaded successfully: {', '.join(saved_files)}"
            st.session_state.message_type = "success"
        else:
            st.session_state.message = "No new files were uploaded. They may already exist in the project."
            st.session_state.message_type = "info"
        if invalid_files:
            st.session_state.message += f"\n\nWarning: The following files were not uploaded as they are not .txt files: {', '.join(invalid_files)}. Please use the 📤 File Upload and Conversion page (from the side panel) to format these documents (.txt, utf8 encoding) before uploading."
            st.session_state.message_type = "warning"
    else:
        st.session_state.message = "Please select files to upload."
        st.session_state.message_type = "warning"

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
    
    # Create subfolders for different stages of the analysis
    subfolders = ['data', 'initial_codes', 'reduced_codes', 'expanded_reduced_codes', 'themes', 'theme_books']
    for folder in subfolders:
        os.makedirs(os.path.join(project_path, folder), exist_ok=True)

# Function to save uploaded files
def save_uploaded_files(uploaded_files, project_name):
    """
    Save uploaded files to the project's data folder.

    This function processes each uploaded file, saving valid .txt files and
    tracking invalid files.

    Args:
    uploaded_files (list): List of uploaded file objects from Streamlit's file_uploader
    project_name (str): Name of the current project

    Returns:
    tuple: Lists of saved file names and invalid file names

    Side effects:
    - Saves valid .txt files to the project's data folder
    """
    data_folder = os.path.join(PROJECTS_DIR, project_name, 'data')
    saved_files = []
    invalid_files = []
    for file in uploaded_files:
        if file.name.lower().endswith('.txt'):
            file_path = os.path.join(data_folder, file.name)
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
                saved_files.append(file.name)
        else:
            invalid_files.append(file.name)
    return saved_files, invalid_files

# Function to get the list of files in a project
def get_project_files(project_name):
    """
    Retrieve the list of files in a project's data folder.

    Args:
    project_name (str): Name of the project

    Returns:
    list: Names of files in the project's data folder
    """
    data_folder = os.path.join(PROJECTS_DIR, project_name, 'data')
    return [f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f))]

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

# New function to get contents of all subfolders in a project
def get_project_structure(project_name):
    """
    Get the structure of a project, including all subfolders and their contents.

    Args:
    project_name (str): Name of the project

    Returns:
    dict: A dictionary representing the project structure
    """
    project_path = os.path.join(PROJECTS_DIR, project_name)
    structure = {}
    for root, dirs, files in os.walk(project_path):
        folder = os.path.relpath(root, project_path)
        if folder == '.':
            continue
        structure[folder] = files
    return structure

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


#if 'uploaded_files' not in st.session_state:
#    st.session_state.uploaded_files = None #hopefully fixing Project Start widget error

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

        # Display existing files with checkboxes
        try:
            existing_files = get_project_files(st.session_state.selected_project)
        except:
            existing_files = []

        files_to_delete = []
        

        if existing_files:
            #st.write("Select files to delete:") # commented out as there's now a dedicated file management section at bottom of page
            # List files with checkboxes
            #for file in existing_files:
            #    if st.checkbox(file, key=f"checkbox_{file}"):
            #        files_to_delete.append(file)
            
            # Show delete button, disabled if no files are selected
            #if st.button("Delete Selected", disabled=len(files_to_delete) == 0):
            #    remove_files(st.session_state.selected_project, files_to_delete)
            #    st.success(f"Deleted {len(files_to_delete)} file(s)")
            #    st.rerun()
            pass
        else:
            st.write("No files in this project yet. Upload files below to get started")
        
        # File upload UI
        st.file_uploader("Upload interviews .txt files", accept_multiple_files=True, key="uploaded_files", on_change=handle_file_upload)

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