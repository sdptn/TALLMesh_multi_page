'''
Just some util functions for dealing with project files and directories
'''
import os
import uuid
import streamlit as st
import shutil
import zipfile
import time
import logging
import threading
from pathlib import Path

PROJECTS_DIR = "projects"

# Workspace retention settings
WORKSPACE_RETENTION_HOURS = 24
WORKSPACE_TTL_SECONDS = WORKSPACE_RETENTION_HOURS * 60 * 60

# Check once per hour
CLEANUP_INTERVAL_SECONDS = 60 * 60
ACTIVITY_FILE = ".last_activity"

logger = logging.getLogger(__name__)

_workspace_lock = threading.RLock()
_cleanup_thread_started = False

def get_user_id():
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = str(uuid.uuid4())
    return st.session_state['user_id']

def _is_uuid_directory(name):

    """
    Only allow automatic cleanup of directories whose names are valid UUIDs.
    This prevent the cleanup routine from accidentally deleting unrelated directories inside projects/.
    """
    try:
        uuid.UUID(name)
        return True
    except (ValueError, AttributeError):
        return False

def _touch_workspace(user_dir):
    """
    Record activity for a workspace.
    """
    activity_file = os.path.join(user_dir, ACTIVITY_FILE)
    Path(activity_file).touch(exist_ok=True)

def _get_workspace_last_activity(user_dir):
    """
    Return the most recent known activity time.

    """
    activity_file = os.path.join(user_dir, ACTIVITY_FILE)
    if os.path.exists(activity_file):
        return os.path.getmtime(activity_file)

    latest = os.path.getmtime(user_dir)

    for root, dirs, files in os.walk(user_dir):
        for name in dirs + files:
            path = os.path.join(root, name)
            try:
                latest = max(latest, os.path.getmtime(path))
            except OSError:
                pass

    return latest

def cleanup_stale_workspaces():
    """
    Remove workspaces that have been inactive for more than 24 hours.
    """
    os.makedirs(PROJECTS_DIR, exist_ok=True)

    now = time.time()

    with _workspace_lock:
        for name in os.listdir(PROJECTS_DIR):
            
            #only automatically delete UUID workspace directories
            if not _is_uuid_directory(name):
                continue

            user_dir = os.path.join(PROJECTS_DIR, name)
            if not os.path.isdir(user_dir):
                continue

            try:
                last_activity = _get_workspace_last_activity(user_dir)

                if now - last_activity > WORKSPACE_TTL_SECONDS:
                    shutil.rmtree(user_dir)
                    logger.info(
                        "Deleted stale workspace %s after more than %s hours inactivity",
                        name,
                        WORKSPACE_RETENTION_HOURS
                    )

            except FileNotFoundError:
                #Another cleanup/user action may already have removed it
                pass

            except Exception as e:
                logger.warning(
                    "Could not clean workspace %s: %s",
                    name,
                    e
                )

def _workspace_cleanup_loop():
    """
    Background cleanup loop for this TALLMesh process.
    """
    while True:
        try:
            cleanup_stale_workspaces()
        except Exception as exc:
            logger.warning("Workspace cleanup failed: %s", exc)

        time.sleep(CLEANUP_INTERVAL_SECONDS)

def start_workspace_cleanup():
    """
    Start one background cleanip thread per TALLMesh process.
    """
    global _cleanup_thread_started

    with _workspace_lock:
        if _cleanup_thread_started:
            return

        cleanup_thread = threading.Thread(
            target=_workspace_cleanup_loop,
            name="workspace-cleanup",
            daemon=True
        )
        cleanup_thread.start()
        _cleanup_thread_started = True

        logger.info(
            "Workspace cleanup started: %s-hour expiry, hourly checks",
            WORKSPACE_RETENTION_HOURS
        )


def get_user_project_dir():

    # Make sure the cleanup service is running
    start_workspace_cleanup()

    user_id = get_user_id()
    user_dir = os.path.join(PROJECTS_DIR, user_id)

    with _workspace_lock:
        os.makedirs(user_dir, exist_ok=True)
        _touch_workspace(user_dir)

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
    _touch_workspace(user_dir)

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
    _touch_workspace(user_dir)