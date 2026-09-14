import os
import shutil
import stat
import time

import streamlit as st
from ui_utils import sidebar_data_controls

sidebar_data_controls()

from project_utils import (
    get_projects,
    get_user_project_dir,
    restore_project_from_zip,

)

from file_conversion_utils import convert_to_txt


logo = "pages/static/tmeshlogo.png"
st.logo(logo)

st.header(":orange[Resume and Manage Project]")

st.write(
    ":green[Resume an existing project. "
    "Add or remove files.]"
)

st.divider()

st.subheader("Restore Saved Project")

st.write(
    "If you previously downloaded a TALLMesh project bundle, "
    "you can restore it here."
)

uploaded_zip = st.file_uploader(
    "Upload a TALLMesh project bundle (.zip)",
    type=["zip"],
    key="resume_project_bundle_upload"
)

if uploaded_zip and st.button("Restore Project Bundle"):

    try:
        restore_project_from_zip(uploaded_zip)

        st.success("Project restored successfully.")

        st.rerun()

    except Exception as e:
        st.error(
            f"Could not restore project: {e}"
        )

st.divider()

FOLDER_ORDER = [
    "data",
    "initial_codes",
    "pairwise_reduced_codes",
    "expanded_pairwise_reduced_codes",
    "themes",
    "theme_books",
]

STAGE_FOLDERS = {
    "Raw Data": [
        "data"
    ],
    "Initial Coding": [
        "initial_codes"
    ],
    "Pairwise Reduction": [
        "pairwise_reduced_codes",
        "expanded_pairwise_reduced_codes"
    ],
    "Finding Themes": [
        "themes",
        "theme_books"
    ],
}

def get_project_structure(project_name):
    structure = {folder: [] for folder in FOLDER_ORDER}

    base_dir = get_user_project_dir()
    project_path = os.path.join(base_dir, project_name)

    for folder in FOLDER_ORDER:
        folder_path = os.path.join(project_path, folder)

        if os.path.exists(folder_path):
            structure[folder] = [
                f
                for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]

    return structure

def delete_files(file_paths):
    deleted_files = []

    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(file_path)

            except Exception as e:
                st.error(
                    f"Error deleting {os.path.basename(file_path)}: {str(e)}"
                )

    return deleted_files

def remove_project(project_name):
    base_dir = get_user_project_dir()
    project_path = os.path.join(base_dir, project_name)

    if os.path.exists(project_path):
        try:
            def remove_readonly(func, path, exc_info):
                os.chmod(path, stat.S_IWRITE)
                func(path)

            time.sleep(0.5)

            shutil.rmtree(
                project_path,
                onerror=remove_readonly
            )

            st.session_state.selected_project = None
            st.success(
                f"Project '{project_name}' has been successfully removed."
            )

        except Exception as e:
            st.error(
                f"Error removing project '{project_name}': {str(e)}"
            )

# Initialise selected project
if "selected_project" not in st.session_state:
    st.session_state.selected_project = None

projects = get_projects()

st.subheader("Resume Existing Project")

if projects:
    project_options = ["Select a project..."] + projects

    default_index = 0

    if (
        st.session_state.selected_project
        and st.session_state.selected_project in projects
    ):
        default_index = project_options.index(
            st.session_state.selected_project
        )

    selected_project = st.selectbox(
        "Select a project:",
        project_options,
        index=default_index,
        key="resume_project_selector"
    )

    if selected_project != "Select a project...":
        st.session_state.selected_project = selected_project
    else:
        st.session_state.selected_project = None

else:
    st.info("There are no existing projects in this workspace.")

if st.session_state.selected_project:

    st.success(
        f"Current project: {st.session_state.selected_project}"
    )

    st.subheader("Add & Manage Files")

    st.markdown("#### Add New Files")

    uploaded_files = st.file_uploader(
        "Add files (.txt, .pdf, .docx, .rtf and other text files)",
        accept_multiple_files=True,
        key="resume_uploaded_files",
    )

    if uploaded_files and st.button("Add Files to Project"):

        base_dir = get_user_project_dir()
        data_folder = os.path.join(
            base_dir,
            st.session_state.selected_project,
            "data"
        )

        saved_files = []
        skipped_files = []
        failed_files = []

        for file in uploaded_files:
            try:
                original_name = file.name
                txt_name = os.path.splitext(original_name)[0] + ".txt"
                txt_path = os.path.join(data_folder, txt_name)

                if original_name.lower().endswith(".txt"):

                    direct_path = os.path.join(
                        data_folder,
                        original_name
                    )

                    if os.path.exists(direct_path):
                        skipped_files.append(original_name)

                    else:
                        with open(direct_path, "wb") as f:
                            f.write(file.getbuffer())

                        saved_files.append(original_name)

                else:

                    if os.path.exists(txt_path):
                        skipped_files.append(original_name)

                    else:
                        converted_file = convert_to_txt(
                            file,
                            st.session_state.selected_project
                        )

                        saved_files.append(converted_file)

            except Exception as e:
                failed_files.append(
                    f"{file.name} ({str(e)})"
                )

        if saved_files:
            st.success(
                f"Added: {', '.join(saved_files)}"
            )

        if skipped_files:
            st.info(
                f"Already present: {', '.join(skipped_files)}"
            )

        if failed_files:
            st.warning(
                f"Could not process: {', '.join(failed_files)}"
            )

        st.rerun() 

    st.divider()
    st.subheader("Manage Project Files")

    project_structure = get_project_structure(
        st.session_state.selected_project
    )

    files_to_delete = []

    for stage_name, folders in STAGE_FOLDERS.items():

        with st.expander(
            stage_name,
            expanded=(stage_name == "Raw Data")
        ):

            stage_has_files = False

            for folder in folders:

                files = project_structure.get(folder, [])

                if files:
                    stage_has_files = True

                    for file in files:

                        base_dir = get_user_project_dir()

                        file_path = os.path.join(
                            base_dir,
                            st.session_state.selected_project,
                            folder,
                            file
                        )

                        if st.checkbox(
                            f"📄 {file}",
                            key=f"manage_checkbox_{file_path}"
                        ):
                            files_to_delete.append(file_path)

            if not stage_has_files:
                st.write("(empty)")

    if files_to_delete:

        st.warning(
            f"{len(files_to_delete)} file(s) selected for deletion."
        )

        if st.button(
            "Delete Selected Files",
            type="primary"
        ):

            deleted_files = delete_files(files_to_delete)

            if deleted_files:
                st.success(
                    f"Deleted {len(deleted_files)} file(s)."
                )

                st.rerun()  


