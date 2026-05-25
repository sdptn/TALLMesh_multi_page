import os
import chardet
import fitz # PyMuPDF
from docx import Document
from striprtf.striprtf import rtf_to_text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from project_utils import get_user_project_dir

DEFAULT_LOGO_PATH = "pages/static/tmeshlogo.png"

def detect_encoding(file_content: bytes) -> str:
    """
    Detect the encoding of the given file content.
"""
    result = chardet.detect(file_content)
    return result['encoding']

def convert_pdf_to_txt(pdf_file, output_path: str) -> None:
    """
    Convert a PDF file to a text file.
    """
    try:
        document = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
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
    """
    try:
        document = Document(docx_file)
        text = "\n".join([paragraph.text for paragraph in document.paragraphs])

        with open(output_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)
    except Exception as e:
        logger.error(f"Error converting DOCX to text: {str(e)}")
        raise


def convert_rtf_to_txt(rtf_content, output_path: str) -> None:
    """
    Convert an RTF file to a text file.
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
    Convert an uploaded file to a text file with appropriate encoding
    """
    file_extension = os.path.splitext(file.name)[1].lower()
    file_name = os.path.splitext(file.name)[0] + ".txt"
    file_path = os.path.join(get_user_project_dir(), project_name, "data", file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        if file_extension == '.pdf':
            convert_pdf_to_txt(file, file_path)
        elif file_extension == '.docx':
            convert_docx_to_txt(file, file_path)
        elif file_extension == '.rtf':
            convert_rtf_to_txt(file, file_path)
        else:
            file_content = file.getvalue()
            encoding = detect_encoding(file_content) or 'utf-8'

            try:
                decoded_content = file_content.decode(encoding)
            except UnicodeDecodeError:
                try:
                    decoded_content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_content = file_content.decode('latin-1')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(decoded_content)
        
        logger.info(f"Successfully converted {file.name} to {file_path}")
        return file_name
        
    except Exception as e:
        logger.error(f"Error converting file {file.name}: {str(e)}")
        raise