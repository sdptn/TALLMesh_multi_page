'''
Just some util functions for dealing with project files and directories
'''
import os
import uuid
import streamlit as st
import shutil
import zipfile
import time
from pathlib import Path

PROJECTS_DIR = "projects"

def get_user_id():
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = str(uuid.uuid4())
    return st.session_state['user_id']

def get_user_project_dir():
    user_dir = os.path.join(PROJECTS_DIR, get_user_id())
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def get_projects():
    user_projects_dir = get_user_project_dir()
    return [
        d for d in os.listdir(user_projects_dir) 
        if os.path.isdir(os.path.join(user_projects_dir, d))
    ]

def get_project_files(project_name, folder):
    base_dir = get_user_project_dir()
    data_folder = os.path.join(base_dir, project_name, folder)

    if not os.path.exists(data_folder):
        return []
    return [
        f for f in os.listdir(data_folder) 
        if os.path.isfile(os.path.join(data_folder, f))]

def get_processed_files(project_name, folder):
    base_dir = get_user_project_dir()
    requested_folder = os.path.join(base_dir, project_name, folder)

    if not os.path.exists(requested_folder):
        return []
    return os.listdir(requested_folder)

def get_project_path(project_name):
    return os.path.join(get_user_project_dir(), project_name)

def make_project_zip(project_name):
    zip_path_base = os.path.join(get_user_project_dir(), project_name)

    shutil.make_archive(
        base_name=zip_path_base,
        format="zip",
        root_dir=get_user_project_dir(),
        base_dir=project_name
    )

    return f"{zip_path_base}.zip"

def restore_project_from_zip(zip_file):
    user_dir = get_user_project_dir()

    with zipfile.ZipFile(zip_file, "r") as z:
        for member in z.namelist():
            target_path = Path(user_dir, member).resolve()
            if not str(target_path).startswith(str(Path(user_dir).resolve())):
                raise Exception("Unsafe ZIP file path detected.")

        z.extractall(user_dir)

def clear_user_workspace():
    user_dir = get_user_project_dir()

    def remove_readonly(func, path, exc_info):
        try:
            os.chmod(path, 0o777)
            func(path)
        except Exception:
            pass

    if os.path.exists(user_dir):
        for _ in range(5):
            try:
                shutil.rmtree(user_dir, onerror=remove_readonly)
                break
            except PermissionError:
                time.sleep(0.5)

    os.makedirs(user_dir, exist_ok=True)