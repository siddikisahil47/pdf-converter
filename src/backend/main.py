import os
import shutil
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import tempfile
from .utils.pdf_operations import PDFOperations
import logging
from io import BytesIO
import zipfile
from PyPDF2 import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Create a temporary directory for file operations
TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp"))
os.makedirs(TEMP_DIR, exist_ok=True)

def handle_error(e):
    """Handle errors and return appropriate response"""
    logger.error(f"Error occurred: {str(e)}")
    if isinstance(e, RuntimeError):
        return jsonify({"error": str(e)}), 500
    elif isinstance(e, ValueError):
        return jsonify({"error": str(e)}), 400
    elif isinstance(e, NotImplementedError):
        return jsonify({"error": str(e)}), 501
    else:
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route("/merge-pdfs", methods=["POST"])
def merge_pdfs():
    if not request.files.getlist("files"):
        return jsonify({"error": "No files uploaded"}), 400
        
    try:
        files = request.files.getlist("files")
        
        # Validate files
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({"error": "Only PDF files are allowed"}), 400
        
        # Get PDF data from files
        pdf_data_list = [file.read() for file in files]
        
        # Merge PDFs
        merged_pdf = PDFOperations.merge_pdfs(pdf_data_list)
        logger.info("Created merged PDF in memory")
        
        return send_file(
            merged_pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name="merged.pdf"
        )
            
    except Exception as e:
        logger.error(f"Error in merge_pdfs: {str(e)}")
        return handle_error(e)

@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    try:
        # Get PDF data
        pdf_data = file.read()
        
        # Get splitting options from the request
        split_options = {}
        
        # Handle specific pages
        pages = request.form.get("pages", "")
        if pages:
            try:
                split_options['pages'] = [int(p.strip()) for p in pages.split(',') if p.strip()]
            except ValueError:
                return jsonify({"error": "Invalid page numbers provided"}), 400
        
        # Handle page ranges
        ranges = request.form.get("ranges", "")
        if ranges:
            try:
                range_pairs = []
                for r in ranges.split(','):
                    if r.strip():
                        start, end = map(int, r.strip().split('-'))
                        range_pairs.append([start, end])
                split_options['ranges'] = range_pairs
                logger.info(f"Parsed ranges: {range_pairs}")
            except Exception as e:
                logger.error(f"Error parsing ranges: {str(e)}")
                return jsonify({"error": "Invalid page ranges provided"}), 400
        
        # Handle first N pages
        first_n = request.form.get("first_n", "")
        if first_n:
            try:
                split_options['first_n'] = int(first_n)
            except ValueError:
                return jsonify({"error": "Invalid number for first pages"}), 400
        
        # Handle last N pages
        last_n = request.form.get("last_n", "")
        if last_n:
            try:
                split_options['last_n'] = int(last_n)
            except ValueError:
                return jsonify({"error": "Invalid number for last pages"}), 400
        
        # Split PDF and get list of BytesIO buffers
        split_pdfs = PDFOperations.split_pdf(pdf_data, split_options if split_options else None)
        
        # Create a ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, pdf_buffer in enumerate(split_pdfs, 1):
                zf.writestr(f"page_{i}.pdf", pdf_buffer.getvalue())
        
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name="split_pages.zip"
        )
        
    except Exception as e:
        return handle_error(e)

@app.route("/pdf-to-images", methods=["POST"])
def pdf_to_images():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
        
    try:
        # Get DPI setting
        try:
            dpi = int(request.form.get("dpi", 200))
            if dpi < 72 or dpi > 600:
                return jsonify({"error": "DPI must be between 72 and 600"}), 400
        except ValueError:
            return jsonify({"error": "Invalid DPI value"}), 400
        
        # Convert PDF to images (returns list of BytesIO buffers)
        image_buffers = PDFOperations.pdf_to_images(file.read(), dpi=dpi)
        
        # Create a ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, img_buffer in enumerate(image_buffers, 1):
                zf.writestr(f"page_{i}.png", img_buffer.getvalue())
        
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name="pdf_images.zip"
        )
        
    except Exception as e:
        return handle_error(e)

@app.route("/images-to-pdf", methods=["POST"])
def images_to_pdf():
    if not request.files.getlist("files"):
        return jsonify({"error": "No files uploaded"}), 400
        
    try:
        files = request.files.getlist("files")
        image_data = []
        
        for file in files:
            if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return jsonify({"error": "Only PNG and JPG images are allowed"}), 400
            image_data.append(file.read())
        
        # Convert images to PDF (returns BytesIO buffer)
        pdf_buffer = PDFOperations.images_to_pdf(image_data)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name="combined.pdf"
        )
        
    except Exception as e:
        return handle_error(e)

@app.route("/compress-pdf", methods=["POST"])
def compress_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
        
    quality = request.form.get("quality", "medium")
    if quality not in ["low", "medium", "high"]:
        return jsonify({"error": "Invalid quality value"}), 400
        
    try:
        # Get PDF data
        pdf_data = file.read()
        
        # Compress PDF
        compressed_pdf = PDFOperations.compress_pdf(pdf_data, quality)
        
        # Get sizes for response headers
        original_size = len(pdf_data)
        compressed_size = get_buffer_size(compressed_pdf)
        reduction_percentage = round(((original_size - compressed_size) / original_size) * 100, 2)
        
        # Create response
        response = send_file(
            compressed_pdf,
            as_attachment=True,
            download_name="compressed.pdf",
            mimetype='application/pdf'
        )
        
        # Add compression info to response headers
        response.headers['X-Original-Size'] = format_size(original_size)
        response.headers['X-Compressed-Size'] = format_size(compressed_size)
        response.headers['X-Reduction-Percentage'] = str(reduction_percentage)
        
        return response
        
    except Exception as e:
        return handle_error(e)

@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
        
    try:
        # Get PDF data
        pdf_data = file.read()
        
        # Convert to Word
        word_doc = PDFOperations.pdf_to_word(pdf_data)
        
        return send_file(
            word_doc,
            as_attachment=True,
            download_name="converted.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return handle_error(e)

@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.docx'):
        return jsonify({"error": "Only DOCX files are allowed"}), 400
        
    try:
        # Get Word document data
        docx_data = file.read()
        
        # Convert to PDF
        pdf_doc = PDFOperations.word_to_pdf(docx_data)
        
        return send_file(
            pdf_doc,
            as_attachment=True,
            download_name="converted.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return handle_error(e)

@app.route("/get-pdf-info", methods=["POST"])
def get_pdf_info():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
        
    try:
        # Read PDF data and get total pages
        pdf_data = file.read()
        pdf = PdfReader(BytesIO(pdf_data))
        total_pages = len(pdf.pages)
        
        return jsonify({
            "total_pages": total_pages,
            "filename": file.filename
        })
        
    except Exception as e:
        logger.error(f"Error getting PDF info: {str(e)}")
        return handle_error(e)

if __name__ == "__main__":
    app.run(debug=True, port=8000)