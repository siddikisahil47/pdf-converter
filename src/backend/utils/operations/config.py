import os
import logging
from typing import List, Union
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import shutil
import docx2pdf
import pdf2docx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common constants
TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp"))
MAX_IMAGE_PIXELS = 178956970  # PIL's default limit
MAX_DIMENSION = 4000  # Maximum width/height for any image

def format_size(size_in_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} GB"

def get_buffer_size(buffer: BytesIO) -> int:
    """Get the size of a BytesIO buffer"""
    current_pos = buffer.tell()
    buffer.seek(0, 2)  # Seek to end
    size = buffer.tell()
    buffer.seek(current_pos)  # Restore position
    return size 