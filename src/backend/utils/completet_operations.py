# import os
# from typing import List
# from PyPDF2 import PdfReader, PdfWriter, PdfMerger
# from PIL import Image
# from docx import Document
# from pdf2docx import Converter
# import tempfile
# import sys
# import subprocess
# import logging
# import shutil

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class PDFOperations:

#     @staticmethod
#     def safe_read_pdf(pdf_file: str) -> PdfReader:
#         """Safely read a PDF file with error handling"""
#         try:
#             return PdfReader(pdf_file, strict=False)
#         except Exception as e:
#             logger.error(f"Error reading PDF {pdf_file}: {str(e)}")
#             raise ValueError(f"Failed to read PDF file: {str(e)}")

#     @staticmethod
#     def merge_pdfs(pdf_files: List[str], output_path: str) -> str:
#         """Merge multiple PDF files into one"""
#         if not pdf_files:
#             raise ValueError("No PDF files provided for merging")
            
#         merger = None
#         try:
#             merger = PdfMerger()
            
#             # Process each PDF file
#             for pdf_file in pdf_files:
#                 # Verify file exists
#                 if not os.path.exists(pdf_file):
#                     raise ValueError(f"PDF file not found: {pdf_file}")
                    
#                 # Verify file is readable
#                 if not os.access(pdf_file, os.R_OK):
#                     raise ValueError(f"PDF file is not readable: {pdf_file}")
                    
#                 # Get file size
#                 file_size = os.path.getsize(pdf_file)
#                 if file_size == 0:
#                     raise ValueError(f"PDF file is empty: {pdf_file}")
                
#                 logger.info(f"Processing PDF file: {pdf_file} (size: {file_size} bytes)")
                
#                 try:
#                     # Try to read and append the PDF
#                     with open(pdf_file, 'rb') as file:
#                         merger.append(fileobj=file)
#                         logger.info(f"Successfully appended: {pdf_file}")
#                 except Exception as e:
#                     logger.error(f"Error processing {pdf_file}: {str(e)}")
#                     raise ValueError(f"Failed to process PDF file {pdf_file}: {str(e)}")
            
#             # Ensure output directory exists
#             os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
#             # Write the merged PDF
#             with open(output_path, "wb") as output_file:
#                 merger.write(output_file)
#                 logger.info(f"Successfully wrote merged PDF to: {output_path}")
            
#             # Verify the output file was created and is not empty
#             if not os.path.exists(output_path):
#                 raise ValueError("Failed to create output file")
#             if os.path.getsize(output_path) == 0:
#                 raise ValueError("Created output file is empty")
                
#             return output_path
            
#         except Exception as e:
#             logger.error(f"Error merging PDFs: {str(e)}")
#             raise ValueError(f"Failed to merge PDFs: {str(e)}")
#         finally:
#             if merger:
#                 merger.close()
#                 logger.info("Closed PDF merger")

#     @staticmethod
#     def split_pdf(pdf_file: str, output_dir: str, split_options: dict = None) -> List[str]:
#         """Split PDF based on various options
        
#         split_options can contain:
#         - pages: List of specific page numbers to extract (each page becomes a separate PDF)
#         - ranges: List of [start, end] ranges (each range becomes a single PDF)
#         - first_n: Extract first N pages as a single PDF
#         - last_n: Extract last N pages as a single PDF
#         """
#         reader = PDFOperations.safe_read_pdf(pdf_file)
#         output_files = []
#         total_pages = len(reader.pages)
        
#         try:
#             # Create output directory if it doesn't exist
#             os.makedirs(output_dir, exist_ok=True)
            
#             if not split_options:
#                 # Default behavior: split all pages into separate PDFs
#                 for page_num in range(total_pages):
#                     writer = PdfWriter()
#                     writer.add_page(reader.pages[page_num])
#                     output_path = os.path.join(output_dir, f"page_{page_num + 1}.pdf")
#                     with open(output_path, "wb") as output_file:
#                         writer.write(output_file)
#                     output_files.append(output_path)
#                 return output_files
            
#             # Handle specific pages (each page becomes a separate PDF)
#             if 'pages' in split_options:
#                 pages = split_options['pages']
#                 for page_num in pages:
#                     if 1 <= page_num <= total_pages:
#                         writer = PdfWriter()
#                         writer.add_page(reader.pages[page_num - 1])  # Convert to 0-based index
#                         output_path = os.path.join(output_dir, f"page_{page_num}.pdf")
#                         with open(output_path, "wb") as output_file:
#                             writer.write(output_file)
#                         output_files.append(output_path)
            
#             # Handle page ranges (each range becomes a single PDF)
#             if 'ranges' in split_options:
#                 for range_num, (start, end) in enumerate(split_options['ranges'], 1):
#                     if start < 1:
#                         start = 1
#                     if end > total_pages:
#                         end = total_pages
#                     if start <= end:
#                         writer = PdfWriter()
#                         # Add all pages in the range to the same PDF
#                         for page_num in range(start - 1, end):  # Convert to 0-based index
#                             writer.add_page(reader.pages[page_num])
#                         # Name the file to indicate the page range
#                         output_path = os.path.join(output_dir, f"pages_{start}_to_{end}.pdf")
#                         with open(output_path, "wb") as output_file:
#                             writer.write(output_file)
#                         output_files.append(output_path)
#                         logger.info(f"Created PDF with pages {start} to {end}")
            
#             # Handle first N pages (as a single PDF)
#             if 'first_n' in split_options:
#                 n = min(split_options['first_n'], total_pages)
#                 if n > 0:
#                     writer = PdfWriter()
#                     for page_num in range(n):
#                         writer.add_page(reader.pages[page_num])
#                     output_path = os.path.join(output_dir, f"first_{n}_pages.pdf")
#                     with open(output_path, "wb") as output_file:
#                         writer.write(output_file)
#                     output_files.append(output_path)
#                     logger.info(f"Created PDF with first {n} pages")
            
#             # Handle last N pages (as a single PDF)
#             if 'last_n' in split_options:
#                 n = min(split_options['last_n'], total_pages)
#                 if n > 0:
#                     writer = PdfWriter()
#                     for page_num in range(total_pages - n, total_pages):
#                         writer.add_page(reader.pages[page_num])
#                     output_path = os.path.join(output_dir, f"last_{n}_pages.pdf")
#                     with open(output_path, "wb") as output_file:
#                         writer.write(output_file)
#                     output_files.append(output_path)
#                     logger.info(f"Created PDF with last {n} pages")
            
#             if not output_files:
#                 raise ValueError("No pages were extracted based on the provided options")
                
#             return output_files
            
#         except Exception as e:
#             logger.error(f"Error splitting PDF: {str(e)}")
#             raise ValueError(f"Failed to split PDF: {str(e)}")

#     @staticmethod
#     def pdf_to_images(pdf_file: str, output_dir: str, dpi: int = 200) -> List[str]:
#         """Convert PDF pages to images using PyMuPDF with size optimization
        
#         Args:
#             pdf_file: Input PDF file path
#             output_dir: Output directory for images
#             dpi: Resolution in dots per inch (default: 200)
            
#         Returns:
#             List of paths to the generated image files
#         """
#         try:
#             import fitz  # PyMuPDF
            
#             # Create output directory if it doesn't exist
#             os.makedirs(output_dir, exist_ok=True)
            
#             # Calculate zoom factor based on DPI
#             zoom = dpi / 72  # standard PDF resolution is 72 DPI
#             magnify = fitz.Matrix(zoom, zoom)
            
#             # Open PDF
#             doc = fitz.open(pdf_file)
#             output_files = []
            
#             # Convert each page to an image
#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 pix = page.get_pixmap(matrix=magnify)
                
#                 # Convert pixmap to PIL Image for optimization
#                 img_data = pix.samples
#                 img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
                
#                 # Optimize image size while maintaining quality
#                 output_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
                
#                 # Apply optimization based on image size
#                 if img.width > 2000 or img.height > 2000:
#                     # Calculate new size maintaining aspect ratio
#                     ratio = min(2000/img.width, 2000/img.height)
#                     new_size = (int(img.width * ratio), int(img.height * ratio))
#                     img = img.resize(new_size, Image.Resampling.LANCZOS)
                
#                 # Save with optimization
#                 img.save(
#                     output_path,
#                     "PNG",
#                     optimize=True,
#                     quality=85,  # Slightly reduce quality for better compression
#                     dpi=(dpi, dpi)
#                 )
                
#                 output_files.append(output_path)
#                 logger.info(f"Converted page {page_num + 1} to image: {output_path}")
            
#             doc.close()
#             return output_files
            
#         except Exception as e:
#             logger.error(f"Error converting PDF to images: {str(e)}")
#             raise ValueError(f"Failed to convert PDF to images: {str(e)}")

#     @staticmethod
#     def images_to_pdf(image_files: List[str], output_path: str) -> str:
#         if not image_files:
#             raise ValueError("No image files provided")
            
#         # Open the first image
#         first_image = Image.open(image_files[0])
#         # Convert to RGB if necessary
#         if first_image.mode != 'RGB':
#             first_image = first_image.convert('RGB')
            
#         # Get all other images
#         other_images = []
#         for image_path in image_files[1:]:
#             img = Image.open(image_path)
#             if img.mode != 'RGB':
#                 img = img.convert('RGB')
#             other_images.append(img)
            
#         # Save as PDF
#         first_image.save(output_path, "PDF", save_all=True, append_images=other_images)
#         return output_path

#     @staticmethod
#     def compress_pdf(pdf_file: str, output_path: str, quality: str = "medium") -> dict:
#         """Compress PDF and return information about the compression
        
#         Args:
#             pdf_file: Input PDF file path
#             output_path: Output PDF file path
#             quality: Compression quality ('low', 'medium', or 'high')
            
#         Returns:
#             dict containing:
#             - output_path: Path to compressed PDF
#             - original_size: Original file size in bytes
#             - compressed_size: Compressed file size in bytes
#             - reduction_percentage: Size reduction percentage
#         """
#         try:
#             import fitz  # PyMuPDF
            
#             # Get original file size
#             original_size = os.path.getsize(pdf_file)
            
#             def compress_with_params(doc, params, image_scale):
#                 """Helper function to compress with given parameters and check reduction"""
#                 temp_output = output_path + ".temp"
#                 doc.save(temp_output, **params)
#                 temp_size = os.path.getsize(temp_output)
#                 reduction = ((original_size - temp_size) / original_size) * 100
#                 return temp_output, temp_size, reduction
            
#             # Open the PDF
#             doc = fitz.open(pdf_file)
            
#             # Base compression parameters
#             base_params = {
#                 "deflate": True,
#                 "clean": True,
#                 "pretty": False,
#                 "linear": True,
#             }
            
#             if quality == "high":  # Target: up to 50% compression
#                 compression_params = {**base_params, "garbage": 4}
                
#                 # Try increasingly aggressive compression until we achieve desired reduction
#                 scales = [0.5, 0.4, 0.3, 0.25]  # Start with 50% reduction, go up to 75% reduction
                
#                 for scale in scales:
#                     # Reset to original document
#                     doc = fitz.open(pdf_file)
                    
#                     # Apply image compression
#                     for page in doc:
#                         for img in page.get_images():
#                             xref = img[0]
#                             image = doc.extract_image(xref)
#                             if image:
#                                 pix = fitz.Pixmap(doc, xref)
#                                 if pix.n - pix.alpha >= 4:  # CMYK
#                                     pix = fitz.Pixmap(fitz.csRGB, pix)
#                                 # Calculate new dimensions
#                                 new_width = max(100, int(pix.width * scale))
#                                 new_height = max(100, int(pix.height * scale))
#                                 pix = fitz.Pixmap(pix, new_width, new_height)
#                                 page.replace_image(xref, pixmap=pix)
                    
#                     temp_output, compressed_size, reduction = compress_with_params(doc, compression_params, scale)
                    
#                     if reduction > 50:  # If we exceed 50%, try the previous scale
#                         doc = fitz.open(pdf_file)
#                         prev_scale = scales[max(0, scales.index(scale) - 1)]
#                         # Recompress with previous scale
#                         for page in doc:
#                             for img in page.get_images():
#                                 xref = img[0]
#                                 image = doc.extract_image(xref)
#                                 if image:
#                                     pix = fitz.Pixmap(doc, xref)
#                                     if pix.n - pix.alpha >= 4:
#                                         pix = fitz.Pixmap(fitz.csRGB, pix)
#                                     new_width = max(100, int(pix.width * prev_scale))
#                                     new_height = max(100, int(pix.height * prev_scale))
#                                     pix = fitz.Pixmap(pix, new_width, new_height)
#                                     page.replace_image(xref, pixmap=pix)
#                         temp_output, compressed_size, reduction = compress_with_params(doc, compression_params, prev_scale)
                    
#                     if reduction >= 15:  # Accept any reduction above 15%
#                         break
                        
#             elif quality == "medium":  # Target: minimum 15% compression
#                 compression_params = {**base_params, "garbage": 3}
                
#                 # Try different scales until we achieve at least 15% reduction
#                 scales = [0.8, 0.7, 0.6, 0.5]
                
#                 for scale in scales:
#                     # Reset to original document
#                     doc = fitz.open(pdf_file)
                    
#                     # Apply image compression
#                     for page in doc:
#                         for img in page.get_images():
#                             xref = img[0]
#                             image = doc.extract_image(xref)
#                             if image:
#                                 pix = fitz.Pixmap(doc, xref)
#                                 if pix.n - pix.alpha >= 4:
#                                     pix = fitz.Pixmap(fitz.csRGB, pix)
#                                 if pix.width > 800 or pix.height > 800:
#                                     new_width = int(pix.width * scale)
#                                     new_height = int(pix.height * scale)
#                                     pix = fitz.Pixmap(pix, new_width, new_height)
#                                     page.replace_image(xref, pixmap=pix)
                    
#                     temp_output, compressed_size, reduction = compress_with_params(doc, compression_params, scale)
                    
#                     if reduction >= 15:  # Stop when we achieve at least 15% reduction
#                         break
                        
#             else:  # low - Target: minimum 5% compression
#                 compression_params = {**base_params, "garbage": 2}
                
#                 # Try different scales until we achieve at least 5% reduction
#                 scales = [0.9, 0.85, 0.8, 0.75]
                
#                 for scale in scales:
#                     # Reset to original document
#                     doc = fitz.open(pdf_file)
                    
#                     # Apply image compression
#                     for page in doc:
#                         for img in page.get_images():
#                             xref = img[0]
#                             image = doc.extract_image(xref)
#                             if image:
#                                 pix = fitz.Pixmap(doc, xref)
#                                 if pix.n - pix.alpha >= 4:
#                                     pix = fitz.Pixmap(fitz.csRGB, pix)
#                                 if pix.width > 1500 or pix.height > 1500:
#                                     new_width = int(pix.width * scale)
#                                     new_height = int(pix.height * scale)
#                                     pix = fitz.Pixmap(pix, new_width, new_height)
#                                     page.replace_image(xref, pixmap=pix)
                    
#                     temp_output, compressed_size, reduction = compress_with_params(doc, compression_params, scale)
                    
#                     if reduction >= 5:  # Stop when we achieve at least 5% reduction
#                         break
            
#             # Move the temp file to final output if it exists
#             if os.path.exists(temp_output):
#                 os.replace(temp_output, output_path)
#             else:
#                 # If no temp file was created, save with basic compression
#                 doc.save(output_path, **compression_params)
#                 compressed_size = os.path.getsize(output_path)
#                 reduction = ((original_size - compressed_size) / original_size) * 100
            
#             doc.close()
            
#             result = {
#                 "output_path": output_path,
#                 "original_size": original_size,
#                 "compressed_size": compressed_size,
#                 "reduction_percentage": round(reduction, 2)
#             }
            
#             logger.info(
#                 f"Compression complete: Original size: {original_size} bytes, "
#                 f"Compressed size: {compressed_size} bytes, "
#                 f"Reduction: {result['reduction_percentage']}%"
#             )
            
#             return result
            
#         except Exception as e:
#             logger.error(f"Error compressing PDF: {str(e)}")
#             raise ValueError(f"Failed to compress PDF: {str(e)}")

#     @staticmethod
#     def pdf_to_word(pdf_file: str, output_path: str) -> str:
#         try:
#             # Use pdf2docx for conversion
#             cv = Converter(pdf_file)
#             cv.convert(output_path)
#             cv.close()
#             return output_path
#         except Exception as e:
#             logger.error(f"Error converting PDF to Word: {str(e)}")
            
#             # Fallback to simple text extraction if conversion fails
#             reader = PDFOperations.safe_read_pdf(pdf_file)
#             doc = Document()
            
#             for page in reader.pages:
#                 text = page.extract_text()
#                 if text.strip():
#                     doc.add_paragraph(text.strip())
                    
#                 # Add page break after each page except the last one
#                 if page != reader.pages[-1]:
#                     doc.add_page_break()
            
#             doc.save(output_path)
#             return output_path

#     @staticmethod
#     def word_to_pdf(docx_file: str, output_path: str) -> str:
#         """Convert Word document to PDF using docx2pdf"""
#         try:
#             from docx2pdf import convert
#             import platform
            
#             # Check if we're on Windows
#             if platform.system() == 'Windows':
#                 # Use Word's COM interface on Windows
#                 convert(docx_file, output_path)
#             else:
#                 # On non-Windows platforms, check for LibreOffice
#                 import subprocess
#                 try:
#                     # Try using LibreOffice
#                     subprocess.run([
#                         'soffice',
#                         '--headless',
#                         '--convert-to',
#                         'pdf',
#                         '--outdir',
#                         os.path.dirname(output_path),
#                         docx_file
#                     ], check=True)
                    
#                     # Rename the output file if necessary
#                     generated_pdf = os.path.splitext(docx_file)[0] + '.pdf'
#                     if generated_pdf != output_path:
#                         os.rename(generated_pdf, output_path)
                        
#                 except subprocess.CalledProcessError:
#                     raise RuntimeError(
#                         "LibreOffice conversion failed. Please install LibreOffice:\n"
#                         "- On macOS: brew install libreoffice\n"
#                         "- On Ubuntu/Debian: sudo apt-get install libreoffice\n"
#                     )
#                 except FileNotFoundError:
#                     raise RuntimeError(
#                         "LibreOffice not found. Please install LibreOffice:\n"
#                         "- On macOS: brew install libreoffice\n"
#                         "- On Ubuntu/Debian: sudo apt-get install libreoffice\n"
#                     )
            
#             logger.info(f"Successfully converted Word document to PDF: {output_path}")
#             return output_path
            
#         except ImportError as e:
#             logger.error(f"Required module not found: {str(e)}")
#             raise RuntimeError(
#                 "Please install required dependencies:\n"
#                 "- pip install docx2pdf\n"
#                 "- On Windows: Microsoft Word must be installed\n"
#                 "- On Mac/Linux: LibreOffice must be installed"
#             )
#         except Exception as e:
#             logger.error(f"Error converting Word to PDF: {str(e)}")
#             raise ValueError(f"Failed to convert Word document to PDF: {str(e)}")

#     @staticmethod
#     def cleanup_temp_directory():
#         """Clean up the temporary directory and all its contents"""
#         temp_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp"))
#         try:
#             if os.path.exists(temp_dir):
#                 shutil.rmtree(temp_dir)
#                 os.makedirs(temp_dir, exist_ok=True)
#                 logger.info(f"Cleaned up temporary directory: {temp_dir}")
#         except Exception as e:
#             logger.error(f"Error cleaning up temporary directory: {str(e)}")

#     @staticmethod
#     def cleanup_temp_files(files: List[str]):
#         """Clean up specific temporary files"""
#         for file in files:
#             try:
#                 if os.path.exists(file):
#                     os.remove(file)
#                     logger.info(f"Cleaned up temporary file: {file}")
#             except Exception as e:
#                 logger.error(f"Error cleaning up {file}: {str(e)}") 