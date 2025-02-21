import streamlit as st
import requests
import os
import tempfile
from typing import List
import json
from PyPDF2 import PdfReader

# Configure the page
st.set_page_config(
    page_title="PDF Converter",
    page_icon="📄",
    layout="wide"
)

# API endpoint
API_URL = "http://localhost:8000"

def handle_error_response(response):
    """Handle error responses from the API"""
    try:
        error_data = response.json()
        error_message = error_data.get('error', 'Unknown error occurred')
    except:
        error_message = f"Error: {response.status_code}"
    return error_message

def main():
    st.title("📄 PDF Converter")
    st.markdown("""
    A powerful tool for all your PDF needs. Convert, merge, split, and more!
    """)

    # Sidebar for operation selection
    operation = st.sidebar.selectbox(
        "Select Operation",
        [
            "Merge PDFs",
            "Split PDF",
            "PDF to Images",
            "Images to PDF",
            "Compress PDF",
            "PDF to Word",
            "Word to PDF"
        ]
    )

    # Main content area
    if operation == "Merge PDFs":
        merge_pdfs_ui()
    elif operation == "Split PDF":
        split_pdf_ui()
    elif operation == "PDF to Images":
        pdf_to_images_ui()
    elif operation == "Images to PDF":
        images_to_pdf_ui()
    elif operation == "Compress PDF":
        compress_pdf_ui()
    elif operation == "PDF to Word":
        pdf_to_word_ui()
    elif operation == "Word to PDF":
        word_to_pdf_ui()

def merge_pdfs_ui():
    st.header("Merge PDFs")
    st.write("Upload multiple PDF files to combine them into a single PDF.")
    
    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("Merge PDFs"):
        if len(uploaded_files) < 2:
            st.error("Please upload at least 2 PDF files to merge.")
            return
            
        with st.spinner("Merging PDFs..."):
            try:
                files = [("files", file) for file in uploaded_files]
                response = requests.post(f"{API_URL}/merge-pdfs", files=files)
                
                if response.status_code == 200:
                    st.success("PDFs merged successfully!")
                    
                    # Check if the response contains PDF content
                    if response.headers.get('content-type') == 'application/pdf':
                        st.download_button(
                            "Download Merged PDF",
                            response.content,
                            "merged.pdf",
                            "application/pdf"
                        )
                    else:
                        st.error("Invalid response format from server")
                else:
                    error_message = handle_error_response(response)
                    st.error(f"Failed to merge PDFs: {error_message}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

def split_pdf_ui():
    st.header("Split PDF")
    st.write("Upload a PDF file and choose how you want to split it.")
    
    uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
    
    if uploaded_file:
        # Create a reader to get total pages
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Use PyPDF2's PdfReader
            reader = PdfReader(tmp_path)
            total_pages = len(reader.pages)
            st.info(f"Total pages in PDF: {total_pages}")
            
            # Split method selection
            split_method = st.radio(
                "Choose splitting method",
                ["All Pages", "Specific Pages", "Page Range", "First N Pages", "Last N Pages"]
            )
            
            data = {}  # Store form data
            
            if split_method == "Specific Pages":
                st.write("Enter page numbers separated by commas (e.g., 1,3,5)")
                pages = st.text_input("Page numbers")
                if pages:
                    # Validate page numbers
                    try:
                        page_nums = [int(p.strip()) for p in pages.split(',') if p.strip()]
                        invalid_pages = [p for p in page_nums if p < 1 or p > total_pages]
                        if invalid_pages:
                            st.error(f"Invalid page numbers: {invalid_pages}. Pages must be between 1 and {total_pages}")
                            return
                        # Store the actual page numbers list instead of the string
                        data['pages'] = page_nums
                    except ValueError:
                        st.error("Please enter valid page numbers")
                        return
                    
            elif split_method == "Page Range":
                st.write("Enter page ranges (e.g., 1-3,5-7)")
                st.write("Note: Each range will create a separate PDF file containing those pages.")
                ranges = st.text_input("Page ranges")
                if ranges:
                    # Validate ranges
                    try:
                        range_list = []
                        for r in ranges.split(','):
                            if not r.strip():
                                continue
                            if '-' not in r:
                                st.error("Each range must be in format 'start-end' (e.g., 2-4)")
                                return
                            start, end = map(int, r.strip().split('-'))
                            if start < 1 or end > total_pages or start > end:
                                st.error(f"Invalid range: {start}-{end}. Must be between 1 and {total_pages}, and start must be less than end")
                                return
                            range_list.append([start, end])
                        
                        if not range_list:
                            st.error("Please enter at least one valid page range")
                            return
                            
                        # Store the actual range list and format it properly for the backend
                        # Convert [[1, 2], [3, 4]] to "1-2,3-4"
                        data['ranges'] = ','.join(f"{start}-{end}" for start, end in range_list)
                        # Show preview of what will be created
                        st.info(f"This will create {len(range_list)} PDF file(s):")
                        for start, end in range_list:
                            st.write(f"- PDF with pages {start} to {end}")
                    except ValueError:
                        st.error("Please enter valid page ranges in format 'start-end' (e.g., 2-4)")
                        return
                    
            elif split_method == "First N Pages":
                n = st.number_input("Number of pages from start", min_value=1, max_value=total_pages, value=1)
                data['first_n'] = int(n)  # Convert to int
                
            elif split_method == "Last N Pages":
                n = st.number_input("Number of pages from end", min_value=1, max_value=total_pages, value=1)
                data['last_n'] = int(n)  # Convert to int
            
            if st.button("Split PDF"):
                with st.spinner("Splitting PDF..."):
                    try:
                        files = {"file": uploaded_file}
                        # Convert data values to strings for form data
                        form_data = {
                            k: ','.join(map(str, v)) if isinstance(v, list) else str(v)
                            for k, v in data.items()
                        }
                        response = requests.post(f"{API_URL}/split-pdf", files=files, data=form_data)
                        
                        if response.status_code == 200:
                            st.success("PDF split successfully!")
                            st.download_button(
                                "Download Split Pages (ZIP)",
                                response.content,
                                "split_pages.zip",
                                "application/zip"
                            )
                        else:
                            error_message = handle_error_response(response)
                            st.error(f"Failed to split PDF: {error_message}")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
        finally:
            # Cleanup temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

def pdf_to_images_ui():
    st.header("PDF to Images")
    st.write("Convert PDF pages to high-quality images with optimized file sizes.")
    
    uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
    
    # Add more informative DPI selection
    dpi = st.select_slider(
        "Image Quality (DPI)",
        options=[72, 100, 150, 200, 300],
        value=200,
        help="Higher DPI = better quality but larger file size. Recommended: 150-200 for web, 300 for printing"
    )
    
    # Show quality vs size information
    quality_info = {
        72: "Low quality, smallest file size",
        100: "Low-medium quality, very small file size",
        150: "Medium quality, small file size",
        200: "Good quality, moderate file size (recommended for most uses)",
        300: "High quality, large file size (good for printing)",
        # 400: "Very high quality, very large file size",
        # 600: "Ultra high quality, extremely large file size"
    }
    st.info(f"Selected quality: {quality_info[dpi]}")
    
    if uploaded_file and st.button("Convert to Images"):
        with st.spinner("Converting PDF to images..."):
            files = {"file": uploaded_file}
            data = {"dpi": dpi}
            response = requests.post(f"{API_URL}/pdf-to-images", files=files, data=data)
            
            if response.status_code == 200:
                st.success("PDF converted to images successfully!")
                st.download_button(
                    "Download Images (ZIP)",
                    response.content,
                    "pdf_images.zip",
                    "application/zip"
                )
            else:
                error_message = handle_error_response(response)
                st.error(f"Failed to convert PDF to images: {error_message}")

def images_to_pdf_ui():
    st.header("Images to PDF")
    st.write("Combine multiple images into a single PDF file.")
    
    uploaded_files = st.file_uploader(
        "Upload image files",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Convert to PDF"):
        with st.spinner("Converting images to PDF..."):
            files = [("files", file) for file in uploaded_files]
            response = requests.post(f"{API_URL}/images-to-pdf", files=files)
            
            if response.status_code == 200:
                st.success("Images combined into PDF successfully!")
                st.download_button(
                    "Download PDF",
                    response.content,
                    "combined.pdf",
                    "application/pdf"
                )
            else:
                st.error("Failed to convert images to PDF. Please try again.")

def compress_pdf_ui():
    st.header("Compress PDF")
    st.write("Reduce the file size of your PDF while maintaining reasonable quality.")
    
    uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
    
    # Show file size if a file is uploaded
    if uploaded_file:
        original_size = len(uploaded_file.getvalue())
        st.info(f"Original file size: {format_size(original_size)}")
    
    quality = st.select_slider(
        "Compression Quality",
        options=["low", "medium", "high"],
        value="medium",
        help="Low = smallest file size, High = best quality"
    )
    
    if uploaded_file and st.button("Compress PDF"):
        with st.spinner("Compressing PDF..."):
            try:
                files = {"file": uploaded_file}
                data = {"quality": quality}
                response = requests.post(f"{API_URL}/compress-pdf", files=files, data=data)
                
                if response.status_code == 200:
                    # Get compression information from headers
                    original_size = response.headers.get('X-Original-Size', 'N/A')
                    compressed_size = response.headers.get('X-Compressed-Size', 'N/A')
                    reduction = response.headers.get('X-Reduction-Percentage', 'N/A')
                    
                    # Show compression results
                    st.success("PDF compressed successfully!")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Original Size", original_size)
                    with col2:
                        st.metric("Compressed Size", compressed_size)
                    with col3:
                        st.metric("Size Reduction", f"{reduction}%")
                    
                    st.download_button(
                        "Download Compressed PDF",
                        response.content,
                        "compressed.pdf",
                        "application/pdf"
                    )
                else:
                    error_message = handle_error_response(response)
                    st.error(f"Failed to compress PDF: {error_message}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

def format_size(size_in_bytes):
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} GB"

def pdf_to_word_ui():
    st.header("PDF to Word")
    st.write("Convert PDF files to editable Word documents.")
    
    uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
    
    if uploaded_file and st.button("Convert to Word"):
        with st.spinner("Converting PDF to Word..."):
            files = {"file": uploaded_file}
            response = requests.post(f"{API_URL}/pdf-to-word", files=files)
            
            if response.status_code == 200:
                st.success("PDF converted to Word successfully!")
                st.download_button(
                    "Download Word Document",
                    response.content,
                    "converted.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.error("Failed to convert PDF to Word. Please try again.")

def word_to_pdf_ui():
    st.header("Word to PDF")
    st.write("Convert Word documents to PDF format.")
    
    uploaded_file = st.file_uploader("Upload Word file", type="docx")
    
    if uploaded_file and st.button("Convert to PDF"):
        with st.spinner("Converting Word to PDF..."):
            files = {"file": uploaded_file}
            response = requests.post(f"{API_URL}/word-to-pdf", files=files)
            
            if response.status_code == 200:
                st.success("Word document converted to PDF successfully!")
                st.download_button(
                    "Download PDF",
                    response.content,
                    "converted.pdf",
                    "application/pdf"
                )
            else:
                st.error("Failed to convert Word to PDF. Please try again.")

if __name__ == "__main__":
    main() 