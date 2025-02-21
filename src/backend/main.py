import os
import shutil
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import tempfile
from .utils.pdf_operations import PDFOperations
import logging

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
        
    temp_files = []
    output_path = None
    try:
        files = request.files.getlist("files")
        
        # Validate and save uploaded files
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({"error": "Only PDF files are allowed"}), 400
                
            temp_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
            file.save(temp_path)
            temp_files.append(temp_path)
            logger.info(f"Saved temporary file: {temp_path}")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "merged.pdf")
        
        # Merge PDFs
        PDFOperations.merge_pdfs(temp_files, output_path)
        logger.info(f"Created merged PDF at: {output_path}")
        
        # Verify file exists
        if not os.path.exists(output_path):
            raise ValueError(f"Failed to create merged PDF at {output_path}")
            
        # Send file
        try:
            response = send_file(
                output_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name="merged.pdf"
            )
            return response
        except Exception as e:
            logger.error(f"Error sending file {output_path}: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error in merge_pdfs: {str(e)}")
        return handle_error(e)
    finally:
        # Cleanup temporary files
        PDFOperations.cleanup_temp_files(temp_files)
        if output_path and os.path.exists(output_path):
            PDFOperations.cleanup_temp_files([output_path])
        # Clean up the entire temp directory periodically
        PDFOperations.cleanup_temp_directory()

@app.route("/split-pdf", methods=["POST"])
def split_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    temp_path = None
    output_dir = None
    zip_path = None
    try:
        temp_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
        file.save(temp_path)
        output_dir = os.path.join(TEMP_DIR, "split")
        os.makedirs(output_dir, exist_ok=True)
        
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
        
        output_files = PDFOperations.split_pdf(temp_path, output_dir, split_options if split_options else None)
        
        # Create a zip file containing all split PDFs
        zip_path = os.path.join(TEMP_DIR, "split_pages.zip")
        shutil.make_archive(zip_path[:-4], 'zip', output_dir)
        
        return send_file(zip_path, as_attachment=True, download_name="split_pages.zip")
    except Exception as e:
        return handle_error(e)
    finally:
        # Cleanup temporary files and directories
        cleanup_files = [f for f in [temp_path, zip_path] if f and os.path.exists(f)]
        PDFOperations.cleanup_temp_files(cleanup_files)
        if output_dir and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        # Clean up the entire temp directory periodically
        PDFOperations.cleanup_temp_directory()

@app.route("/pdf-to-images", methods=["POST"])
def pdf_to_images():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
        
    temp_path = None
    output_dir = None
    zip_path = None
    try:
        temp_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
        file.save(temp_path)
        output_dir = os.path.join(TEMP_DIR, "images")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            dpi = int(request.form.get("dpi", 200))
            if dpi < 72 or dpi > 600:
                return jsonify({"error": "DPI must be between 72 and 600"}), 400
        except ValueError:
            return jsonify({"error": "Invalid DPI value"}), 400
        
        output_files = PDFOperations.pdf_to_images(temp_path, output_dir, dpi)
        
        # Create a zip file containing all images
        zip_path = os.path.join(TEMP_DIR, "pdf_images.zip")
        shutil.make_archive(zip_path[:-4], 'zip', output_dir)
        
        return send_file(zip_path, as_attachment=True, download_name="pdf_images.zip")
    except Exception as e:
        return handle_error(e)
    finally:
        # Cleanup temporary files and directories
        cleanup_files = [f for f in [temp_path, zip_path] if f and os.path.exists(f)]
        PDFOperations.cleanup_temp_files(cleanup_files)
        if output_dir and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        # Clean up the entire temp directory periodically
        PDFOperations.cleanup_temp_directory()

@app.route("/images-to-pdf", methods=["POST"])
def images_to_pdf():
    if not request.files.getlist("files"):
        return jsonify({"error": "No files uploaded"}), 400
        
    temp_files = []
    output_path = None
    try:
        files = request.files.getlist("files")
        for file in files:
            if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return jsonify({"error": "Only PNG and JPG images are allowed"}), 400
                
            temp_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
            file.save(temp_path)
            temp_files.append(temp_path)
            
        output_path = os.path.join(TEMP_DIR, "combined.pdf")
        PDFOperations.images_to_pdf(temp_files, output_path)
        
        return send_file(output_path, as_attachment=True, download_name="combined.pdf")
    except Exception as e:
        return handle_error(e)
    finally:
        # Cleanup temporary files
        PDFOperations.cleanup_temp_files(temp_files)
        if output_path and os.path.exists(output_path):
            PDFOperations.cleanup_temp_files([output_path])
        # Clean up the entire temp directory periodically
        PDFOperations.cleanup_temp_directory()

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
        
    temp_path = None
    output_path = None
    try:
        temp_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
        file.save(temp_path)
        output_path = os.path.join(TEMP_DIR, "compressed.pdf")
        
        # Get compression result with size information
        result = PDFOperations.compress_pdf(temp_path, output_path, quality)
        
        # Format sizes for display
        def format_size(size_in_bytes):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_in_bytes < 1024:
                    return f"{size_in_bytes:.2f} {unit}"
                size_in_bytes /= 1024
            return f"{size_in_bytes:.2f} GB"
        
        # Create response with compression info
        response = send_file(
            result['output_path'],
            as_attachment=True,
            download_name="compressed.pdf",
            mimetype='application/pdf'
        )
        
        # Add compression info to response headers
        response.headers['X-Original-Size'] = format_size(result['original_size'])
        response.headers['X-Compressed-Size'] = format_size(result['compressed_size'])
        response.headers['X-Reduction-Percentage'] = str(result['reduction_percentage'])
        
        return response
        
    except Exception as e:
        return handle_error(e)
    finally:
        # Cleanup temporary files
        cleanup_files = [f for f in [temp_path, output_path] if f and os.path.exists(f)]
        PDFOperations.cleanup_temp_files(cleanup_files)
        # Clean up the entire temp directory periodically
        PDFOperations.cleanup_temp_directory()

@app.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400
        
    temp_path = None
    output_path = None
    try:
        temp_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
        file.save(temp_path)
        output_path = os.path.join(TEMP_DIR, "converted.docx")
        PDFOperations.pdf_to_word(temp_path, output_path)
        
        return send_file(output_path, as_attachment=True, download_name="converted.docx")
    except Exception as e:
        return handle_error(e)
    finally:
        # Cleanup temporary files
        cleanup_files = [f for f in [temp_path, output_path] if f and os.path.exists(f)]
        PDFOperations.cleanup_temp_files(cleanup_files)
        # Clean up the entire temp directory periodically
        PDFOperations.cleanup_temp_directory()

@app.route("/word-to-pdf", methods=["POST"])
def word_to_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if not file.filename.lower().endswith('.docx'):
        return jsonify({"error": "Only DOCX files are allowed"}), 400
        
    temp_path = None
    output_path = None
    try:
        temp_path = os.path.join(TEMP_DIR, secure_filename(file.filename))
        file.save(temp_path)
        output_path = os.path.join(TEMP_DIR, "converted.pdf")
        PDFOperations.word_to_pdf(temp_path, output_path)
        
        return send_file(output_path, as_attachment=True, download_name="converted.pdf")
    except Exception as e:
        return handle_error(e)
    finally:
        # Cleanup temporary files
        cleanup_files = [f for f in [temp_path, output_path] if f and os.path.exists(f)]
        PDFOperations.cleanup_temp_files(cleanup_files)
        # Clean up the entire temp directory periodically
        PDFOperations.cleanup_temp_directory()

if __name__ == "__main__":
    app.run(debug=True, port=8000)