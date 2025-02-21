import streamlit as st
from io import BytesIO
import zipfile
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from PIL import Image
import fitz  # PyMuPDF
import os
import tempfile
from pdf2docx import Converter
import docx2pdf
import platform
import subprocess
from docx import Document
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="PDF Converter",
    page_icon="📄",
    layout="wide"
)

def format_size(size_in_bytes):
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} GB"

def get_buffer_size(buffer):
    """Get size of BytesIO buffer"""
    current_pos = buffer.tell()
    buffer.seek(0, 2)  # Seek to end
    size = buffer.tell()
    buffer.seek(current_pos)  # Restore position
    return size

def merge_pdfs(pdf_data_list):
    """Merge multiple PDFs"""
    merger = PdfMerger()
    for pdf_data in pdf_data_list:
        merger.append(BytesIO(pdf_data))
    
    output_buffer = BytesIO()
    merger.write(output_buffer)
    merger.close()
    output_buffer.seek(0)
    return output_buffer

def split_pdf(pdf_data, split_options=None):
    """Split PDF based on options"""
    reader = PdfReader(BytesIO(pdf_data))
    total_pages = len(reader.pages)
    output_buffers = []
    
    if not split_options:
        # Split all pages
        for page_num in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            buffer = BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            output_buffers.append(buffer)
        return output_buffers
    
    # Handle specific pages
    if 'pages' in split_options:
        for page_num in split_options['pages']:
            if 1 <= page_num <= total_pages:
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num - 1])
                buffer = BytesIO()
                writer.write(buffer)
                buffer.seek(0)
                output_buffers.append(buffer)
    
    # Handle page ranges
    if 'ranges' in split_options:
        for start, end in split_options['ranges']:
            if start < 1:
                start = 1
            if end > total_pages:
                end = total_pages
            if start <= end:
                writer = PdfWriter()
                for page_num in range(start - 1, end):
                    writer.add_page(reader.pages[page_num])
                buffer = BytesIO()
                writer.write(buffer)
                buffer.seek(0)
                output_buffers.append(buffer)
    
    # Handle first N pages
    if 'first_n' in split_options:
        n = min(split_options['first_n'], total_pages)
        if n > 0:
            writer = PdfWriter()
            for page_num in range(n):
                writer.add_page(reader.pages[page_num])
            buffer = BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            output_buffers.append(buffer)
    
    # Handle last N pages
    if 'last_n' in split_options:
        n = min(split_options['last_n'], total_pages)
        if n > 0:
            writer = PdfWriter()
            for page_num in range(total_pages - n, total_pages):
                writer.add_page(reader.pages[page_num])
            buffer = BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            output_buffers.append(buffer)
    
    return output_buffers

def pdf_to_images(pdf_data, dpi=200):
    """Convert PDF to images"""
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    zoom = dpi / 72  # base resolution is 72 dpi
    matrix = fitz.Matrix(zoom, zoom)
    output_buffers = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Optimize size if needed
        if img.width > 2000 or img.height > 2000:
            ratio = min(2000/img.width, 2000/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG", optimize=True)
        img_buffer.seek(0)
        output_buffers.append(img_buffer)
    
    doc.close()
    return output_buffers

def images_to_pdf(image_data_list):
    """Convert images to PDF"""
    if not image_data_list:
        raise ValueError("No images provided")
    
    # Process first image
    first_image = Image.open(BytesIO(image_data_list[0]))
    if first_image.mode != 'RGB':
        first_image = first_image.convert('RGB')
    
    # Process other images
    other_images = []
    for img_data in image_data_list[1:]:
        img = Image.open(BytesIO(img_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        other_images.append(img)
    
    # Save to PDF
    pdf_buffer = BytesIO()
    first_image.save(pdf_buffer, format='PDF', save_all=True, append_images=other_images)
    pdf_buffer.seek(0)
    return pdf_buffer

def compress_pdf(pdf_data, quality='medium'):
    """Compress PDF"""
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    output_buffer = BytesIO()
    
    # Compression parameters based on quality
    if quality == 'low':
        doc.save(output_buffer, deflate=True, garbage=4, clean=True)
    elif quality == 'medium':
        doc.save(output_buffer, deflate=True, garbage=3, clean=True)
    else:  # high
        doc.save(output_buffer, deflate=True, garbage=2, clean=True)
    
    doc.close()
    output_buffer.seek(0)
    return output_buffer

def pdf_to_word(pdf_data):
    """Convert PDF to Word"""
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_temp, \
         tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as docx_temp:
        
        pdf_temp.write(pdf_data)
        pdf_temp.flush()
        
        try:
            # Convert using pdf2docx
            converter = Converter(pdf_temp.name)
            converter.convert(docx_temp.name)
            converter.close()
            
            # Read the result
            with open(docx_temp.name, 'rb') as f:
                output_buffer = BytesIO(f.read())
            return output_buffer
            
        except Exception as e:
            # Fallback to simple text extraction
            reader = PdfReader(BytesIO(pdf_data))
            doc = Document()
            
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    doc.add_paragraph(text.strip())
            
            output_buffer = BytesIO()
            doc.save(output_buffer)
            output_buffer.seek(0)
            return output_buffer
        
        finally:
            # Cleanup
            os.unlink(pdf_temp.name)
            os.unlink(docx_temp.name)

def word_to_pdf(docx_data):
    """Convert Word to PDF"""
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as docx_temp, \
         tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_temp:
        
        docx_temp.write(docx_data)
        docx_temp.flush()
        
        try:
            if platform.system() == 'Windows':
                # Use Word's COM interface on Windows
                docx2pdf.convert(docx_temp.name, pdf_temp.name)
            else:
                # Use LibreOffice on other platforms
                subprocess.run([
                    'soffice',
                    '--headless',
                    '--convert-to',
                    'pdf',
                    '--outdir',
                    os.path.dirname(pdf_temp.name),
                    docx_temp.name
                ], check=True)
                
                # Rename if necessary
                generated_pdf = os.path.splitext(docx_temp.name)[0] + '.pdf'
                if generated_pdf != pdf_temp.name:
                    os.rename(generated_pdf, pdf_temp.name)
            
            # Read the result
            with open(pdf_temp.name, 'rb') as f:
                output_buffer = BytesIO(f.read())
            return output_buffer
            
        finally:
            # Cleanup
            os.unlink(docx_temp.name)
            os.unlink(pdf_temp.name)

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

    if operation == "Merge PDFs":
        st.header("Merge PDFs")
        st.write("Upload multiple PDF files to combine them into a single PDF.")
        
        uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)
        
        if uploaded_files:
            if len(uploaded_files) < 2:
                st.error("Please upload at least 2 PDF files to merge.")
                return
                
            if st.button("Merge PDFs"):
                with st.spinner("Merging PDFs..."):
                    try:
                        # Get PDF data from files
                        pdf_data_list = [file.read() for file in uploaded_files]
                        
                        # Merge PDFs
                        merged_pdf = merge_pdfs(pdf_data_list)
                        
                        # Offer download
                        st.success("PDFs merged successfully!")
                        st.download_button(
                            "Download Merged PDF",
                            merged_pdf.getvalue(),
                            file_name="merged.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
    
    elif operation == "Split PDF":
        st.header("Split PDF")
        st.write("Upload a PDF file and choose how you want to split it.")
        
        uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
        
        if uploaded_file:
            try:
                # Get PDF info
                pdf_data = uploaded_file.read()
                reader = PdfReader(BytesIO(pdf_data))
                total_pages = len(reader.pages)
                st.info(f"Total pages in PDF: {total_pages}")
                
                # Split method selection
                split_method = st.radio(
                    "Choose splitting method",
                    ["All Pages", "Specific Pages", "Page Range", "First N Pages", "Last N Pages"]
                )
                
                split_options = {}
                
                if split_method == "Specific Pages":
                    st.write("Enter page numbers separated by commas (e.g., 1,3,5)")
                    pages = st.text_input("Page numbers")
                    if pages:
                        try:
                            page_nums = [int(p.strip()) for p in pages.split(',') if p.strip()]
                            invalid_pages = [p for p in page_nums if p < 1 or p > total_pages]
                            if invalid_pages:
                                st.error(f"Invalid page numbers: {invalid_pages}. Pages must be between 1 and {total_pages}")
                                return
                            split_options['pages'] = page_nums
                        except ValueError:
                            st.error("Please enter valid page numbers")
                            return
                
                elif split_method == "Page Range":
                    st.write("Enter page ranges (e.g., 1-3,5-7)")
                    st.write("Note: Each range will create a separate PDF file.")
                    ranges = st.text_input("Page ranges")
                    if ranges:
                        try:
                            range_list = []
                            for r in ranges.split(','):
                                if r.strip():
                                    start, end = map(int, r.strip().split('-'))
                                    if start < 1 or end > total_pages or start > end:
                                        st.error(f"Invalid range: {start}-{end}. Must be between 1 and {total_pages}")
                                        return
                                    range_list.append([start, end])
                            split_options['ranges'] = range_list
                        except ValueError:
                            st.error("Please enter valid page ranges")
                            return
                
                elif split_method == "First N Pages":
                    n = st.number_input("Number of pages from start", min_value=1, max_value=total_pages, value=1)
                    split_options['first_n'] = n
                
                elif split_method == "Last N Pages":
                    n = st.number_input("Number of pages from end", min_value=1, max_value=total_pages, value=1)
                    split_options['last_n'] = n
                
                if st.button("Split PDF"):
                    with st.spinner("Splitting PDF..."):
                        try:
                            # Split PDF
                            split_pdfs = split_pdf(pdf_data, split_options)
                            
                            # Create ZIP file
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                                for i, pdf_buffer in enumerate(split_pdfs, 1):
                                    zf.writestr(f"page_{i}.pdf", pdf_buffer.getvalue())
                            
                            # Offer download
                            st.success("PDF split successfully!")
                            st.download_button(
                                "Download Split PDFs (ZIP)",
                                zip_buffer.getvalue(),
                                file_name="split_pages.zip",
                                mime="application/zip"
                            )
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
            
            except Exception as e:
                st.error(f"Error reading PDF: {str(e)}")
    
    elif operation == "PDF to Images":
        st.header("PDF to Images")
        st.write("Convert PDF pages to high-quality images.")
        
        uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
        
        dpi = st.select_slider(
            "Image Quality (DPI)",
            options=[72, 100, 150, 200, 300],
            value=150,
            help="Higher DPI = better quality but larger file size"
        )
        
        quality_info = {
            72: "Low quality, smallest file size",
            100: "Low-medium quality, very small file size",
            150: "Medium quality, small file size",
            200: "Good quality, moderate file size",
            300: "High quality, large file size (good for printing)"
        }
        st.info(f"Selected quality: {quality_info[dpi]}")
        
        if uploaded_file and st.button("Convert to Images"):
            with st.spinner("Converting PDF to images..."):
                try:
                    # Convert PDF to images
                    image_buffers = pdf_to_images(uploaded_file.read(), dpi)
                    
                    # Create ZIP file
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for i, img_buffer in enumerate(image_buffers, 1):
                            zf.writestr(f"page_{i}.png", img_buffer.getvalue())
                    
                    # Offer download
                    st.success("PDF converted to images successfully!")
                    st.download_button(
                        "Download Images (ZIP)",
                        zip_buffer.getvalue(),
                        file_name="pdf_images.zip",
                        mime="application/zip"
                    )
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    elif operation == "Images to PDF":
        st.header("Images to PDF")
        st.write("Combine multiple images into a single PDF file.")
        
        uploaded_files = st.file_uploader(
            "Upload image files",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )
        
        if uploaded_files and st.button("Convert to PDF"):
            with st.spinner("Converting images to PDF..."):
                try:
                    # Get image data
                    image_data_list = [file.read() for file in uploaded_files]
                    
                    # Convert to PDF
                    pdf_buffer = images_to_pdf(image_data_list)
                    
                    # Offer download
                    st.success("Images combined into PDF successfully!")
                    st.download_button(
                        "Download PDF",
                        pdf_buffer.getvalue(),
                        file_name="combined.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    elif operation == "Compress PDF":
        st.header("Compress PDF")
        st.write("Reduce the file size of your PDF while maintaining reasonable quality.")
        
        uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
        
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
                    # Compress PDF
                    compressed_pdf = compress_pdf(uploaded_file.read(), quality)
                    
                    # Calculate compression stats
                    compressed_size = get_buffer_size(compressed_pdf)
                    reduction = ((original_size - compressed_size) / original_size) * 100
                    
                    # Show results
                    st.success("PDF compressed successfully!")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Original Size", format_size(original_size))
                    with col2:
                        st.metric("Compressed Size", format_size(compressed_size))
                    with col3:
                        st.metric("Size Reduction", f"{reduction:.1f}%")
                    
                    # Offer download
                    st.download_button(
                        "Download Compressed PDF",
                        compressed_pdf.getvalue(),
                        file_name="compressed.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    elif operation == "PDF to Word":
        st.header("PDF to Word")
        st.write("Convert PDF files to editable Word documents.")
        
        uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
        
        if uploaded_file and st.button("Convert to Word"):
            with st.spinner("Converting PDF to Word..."):
                try:
                    # Convert to Word
                    word_buffer = pdf_to_word(uploaded_file.read())
                    
                    # Offer download
                    st.success("PDF converted to Word successfully!")
                    st.download_button(
                        "Download Word Document",
                        word_buffer.getvalue(),
                        file_name="converted.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    elif operation == "Word to PDF":
        st.header("Word to PDF")
        st.write("Convert Word documents to PDF format.")
        
        uploaded_file = st.file_uploader("Upload Word file", type="docx")
        
        if uploaded_file and st.button("Convert to PDF"):
            with st.spinner("Converting Word to PDF..."):
                try:
                    # Convert to PDF
                    pdf_buffer = word_to_pdf(uploaded_file.read())
                    
                    # Offer download
                    st.success("Word document converted to PDF successfully!")
                    st.download_button(
                        "Download PDF",
                        pdf_buffer.getvalue(),
                        file_name="converted.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 