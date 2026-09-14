import streamlit as st
from project_utils import make_project_zip, clear_user_workspace

# reused UI functions / components

# Function create circled numbers... seems overkill, there must be a simpler way
def create_circle_number(number):
    return f"""
        <div style="
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: orange;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0 auto 20px auto;
        ">
            <span style="
                color: white;
                font-size: 24px;
                font-weight: bold;
            ">{number}</span>
        </div>
    """

# Function to create centered content in a column with a numbered circle
def centered_column_with_number(column, number, title, image):
    with column:
        st.markdown(create_circle_number(number), unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center; color: orange;'>{title}</h3>", unsafe_allow_html=True)
        st.image(image, use_column_width=True)

#Function to create a download button for project data in the sidebar
def sidebar_data_controls():

    #st.sidebar.divider()
    st.sidebar.caption("Project Data")

    selected_project = st.session_state.get("selected_project")

    if selected_project:

        if st.sidebar.button(
            "💾 Prepare Project Download",
            use_container_width=True
        ):
            zip_path = make_project_zip(selected_project)

            with open(zip_path, "rb") as f:
                st.session_state.project_zip_bytes = f.read()

            st.session_state.project_zip_name = (
                f"{selected_project}.zip"
            )

        if "project_zip_bytes" in st.session_state:

            st.sidebar.download_button(
                "⬇️ Download Project",
                data=st.session_state.project_zip_bytes,
                file_name=st.session_state.project_zip_name,
                mime="application/zip",
                use_container_width=True
            )

    else:
        st.sidebar.button(
            "💾 Download Project",
            disabled=True,
            use_container_width=True,
            help="Select or create a project first."
        )

# Function to clear the user's workspace
    st.sidebar.divider()

    if "confirm_clear_workspace" not in st.session_state:
        st.session_state.confirm_clear_workspace = False

    if not st.session_state.confirm_clear_workspace:

        if st.sidebar.button(
            "🗑️ Clear Workspace",
            use_container_width=True
        ):
            st.session_state.confirm_clear_workspace = True
            st.rerun()

    else:
        st.sidebar.warning(
            "This will permanently delete all projects and files in your workspace."
        )

        if st.sidebar.button(
            "Confirm Clear",
            type="primary",
            use_container_width=True
        ):
            clear_user_workspace()

            st.session_state.selected_project = None
            st.session_state.confirm_clear_workspace = False

            st.session_state.pop("project_zip_bytes", None)
            st.session_state.pop("project_zip_name", None)

            st.rerun()

        if st.sidebar.button(
            "Cancel",
            use_container_width=True
        ):
            st.session_state.confirm_clear_workspace = False
            st.rerun()