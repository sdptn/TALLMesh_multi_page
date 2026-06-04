"""
File Upload and Conversion Module

This module provides functionality for uploading various file types and converting them to .txt format
with appropriate encoding. It supports PDF, DOCX, RTF, and other text formats.

The main features include:
1. File upload through Streamlit interface
2. Automatic file format detection and conversion
3. Encoding detection for text files
4. Project-based file management

Dependencies:
- streamlit: for creating the web interface
- PyMuPDF (fitz): for handling PDF files
- python-docx: for handling DOCX files
- striprtf: for handling RTF files
- chardet: for detecting file encodings
"""

import streamlit as st
import os
import chardet
import fitz  # PyMuPDF
from docx import Document
from striprtf.striprtf import rtf_to_text
import logging
from project_utils import get_projects

# Constants
PROJECTS_DIR = 'projects'

# Set logo
logo = "pages/static/tmeshlogo.png"
st.logo(logo)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_encoding(file_content: bytes) -> str:
    """
    Detect the encoding of the given file content.

    Args:
        file_content (bytes): The content of the file as bytes.

    Returns:
        str: The detected encoding, or None if detection fails.
    """
    result = chardet.detect(file_content)
    return result['encoding']

def convert_pdf_to_txt(pdf_file, output_path: str) -> None:
    """
    Convert a PDF file to a text file.

    Args:
        pdf_file: The PDF file object.
        output_path (str): The path where the output text file will be saved.

    Raises:
        Exception: If there's an error during the conversion process.
    """
    try:
        document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""

        for page_num in range(len(document)):
            page = document[page_num]
            text += page.get_text()

        with open(output_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)
    except Exception as e:
        logger.error(f"Error converting PDF to text: {str(e)}")
        raise

def convert_docx_to_txt(docx_file, output_path: str) -> None:
    """
    Convert a DOCX file to a text file.

    Args:
        docx_file: The DOCX file object.
        output_path (str): The path where the output text file will be saved.

    Raises:
        Exception: If there's an error during the conversion process.
    """
    try:
        doc = Document(docx_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        with open(output_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)
    except Exception as e:
        logger.error(f"Error converting DOCX to text: {str(e)}")
        raise

def convert_rtf_to_txt(rtf_content: str, output_path: str) -> None:
    """
    Convert RTF content to a text file.

    Args:
        rtf_content (str): The content of the RTF file.
        output_path (str): The path where the output text file will be saved.

    Raises:
        Exception: If there's an error during the conversion process.
    """
    try:
        text = rtf_to_text(rtf_content)
        
        with open(output_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)
    except Exception as e:
        logger.error(f"Error converting RTF to text: {str(e)}")
        raise

def convert_to_txt(file, project_name: str) -> str:
    """
    Convert an uploaded file to a text file with appropriate encoding.

    This function handles various file formats including PDF, DOCX, RTF, and other text formats.
    It automatically detects the encoding for text files to ensure accurate conversion.

    Args:
        file: The uploaded file object.
        project_name (str): The name of the project where the file will be saved.

    Returns:
        str: The name of the converted text file.

    Raises:
        Exception: If there's an error during the conversion process.
    """
    file_extension = os.path.splitext(file.name)[1].lower()
    file_name = os.path.splitext(file.name)[0] + '.txt'
    file_path = os.path.join(PROJECTS_DIR, project_name, 'data', file_name)

    try:
        if file_extension == '.pdf':
            convert_pdf_to_txt(file, file_path)
        elif file_extension == '.docx':
            convert_docx_to_txt(file, file_path)
        elif file_extension == '.rtf':
            rtf_content = file.read().decode('utf-8')
            convert_rtf_to_txt(rtf_content, file_path)
        else:
            file_content = file.read()
            encoding = detect_encoding(file_content) or 'utf-8'

            try:
                # Attempt to decode the content using the detected encoding
                decoded_content = file_content.decode(encoding)
            except UnicodeDecodeError:
                # If decoding fails, try with 'utf-8' as a fallback
                try:
                    decoded_content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    # If 'utf-8' also fails, use 'latin-1' which can decode any byte string
                    decoded_content = file_content.decode('latin-1')

            # Write the content to a new .txt file with UTF-8 encoding
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(decoded_content)

        logger.info(f"Successfully converted {file.name} to {file_name}")
        return file_name
    except Exception as e:
        logger.error(f"Error converting {file.name}: {str(e)}")
        raise

def get_project_files(project_name: str) -> list:
    """
    Get a list of files in the project's data folder.

    Args:
        project_name (str): The name of the project.

    Returns:
        list: A list of filenames in the project's data folder.
    """
    data_folder = os.path.join(PROJECTS_DIR, project_name, 'data')
    return [f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f))]

def main():
    """
    Main function to run the Streamlit app for file upload and conversion.

    This function sets up the Streamlit interface, handles file uploads,
    manages file conversions, and displays the results to the user.
    """
    st.header(":orange[File Upload and Conversion]")
    
    with st.expander("Instructions"):
        st.write("""
        This page allows you to upload files and convert them to .txt format with appropriate encoding. Here's how to use it:
        
        1. Select your project from the dropdown menu.
        2. Upload your files using the file uploader.
        3. The app will automatically convert the files to .txt format with UTF-8 encoding.
        4. You can view the list of converted files below the uploader.
        
        Note: This tool supports various file formats including PDF, DOCX, RTF, and other text formats. It automatically detects the original encoding to ensure accurate conversion.
        """)

    # Project selection
    projects = get_projects()
    
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = "Select a project..."

    project_options = ["Select a project..."] + projects
    index = project_options.index(st.session_state.selected_project) if st.session_state.selected_project in project_options else 0

    selected_project = st.selectbox(
        "Select a project:", 
        project_options,
        index=index,
        key="project_selector"
    )

    if selected_project != st.session_state.selected_project:
        st.session_state.selected_project = selected_project
        st.rerun()
    
    if selected_project != "Select a project...":
        st.write(f"Selected project: {selected_project}")
        
        # File upload
        uploaded_files = st.file_uploader("Upload files to convert to .txt", accept_multiple_files=True)
        
        if uploaded_files:
            st.write("Converting files...")
            converted_files = []
            for file in uploaded_files:
                try:
                    converted_file = convert_to_txt(file, selected_project)
                    converted_files.append(converted_file)
                    st.success(f"Successfully converted {file.name} to {converted_file}")
                except Exception as e:
                    st.error(f"Error converting {file.name}: {str(e)}")
            
            st.success(f"Successfully converted {len(converted_files)} out of {len(uploaded_files)} file(s) to .txt format.")
        
        # Display existing files
        st.subheader("Existing files in the project:")
        existing_files = get_project_files(selected_project)
        if existing_files:
            for file in existing_files:
                st.write(file)
        else:
            st.write("No files in this project yet.")
    else:
        st.write("Please select a project to continue.")

if __name__ == "__main__":
    main()

def convert_pdf_to_txt(pdf_file, output_path):
    document = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
    text = ""

    for page_num in range(len(document)):
        page = document[page_num]
        text += page.get_text()

    with open(output_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)