from .config import *
import docx2pdf
import pdf2docx
import tempfile
import platform
import subprocess
from docx import Document
from typing import Union
from io import BytesIO
from PyPDF2 import PdfReader

class DocumentOperations:
    @staticmethod
    def pdf_to_word(pdf_data: Union[str, bytes, BytesIO]) -> BytesIO:
        """Convert PDF to Word document
        
        Args:
            pdf_data: PDF data as file path, bytes, or BytesIO
            
        Returns:
            BytesIO object containing the Word document
        """
        try:
            # Create temporary files for conversion
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_temp, \
                 tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as docx_temp:
                
                # Write PDF data to temp file
                if isinstance(pdf_data, str):
                    with open(pdf_data, 'rb') as f:
                        pdf_temp.write(f.read())
                elif isinstance(pdf_data, bytes):
                    pdf_temp.write(pdf_data)
                elif isinstance(pdf_data, BytesIO):
                    pdf_temp.write(pdf_data.getvalue())
                else:
                    raise ValueError("Invalid PDF input type")
                
                pdf_temp.flush()
                
                try:
                    # Convert PDF to Word
                    converter = pdf2docx.Converter(pdf_temp.name)
                    converter.convert(docx_temp.name)
                    converter.close()
                    
                    # Read the converted file into BytesIO
                    with open(docx_temp.name, 'rb') as f:
                        output_buffer = BytesIO(f.read())
                    
                    logger.info("Successfully converted PDF to Word")
                    return output_buffer
                    
                except Exception as e:
                    logger.error(f"Error in PDF to Word conversion: {str(e)}")
                    
                    # Fallback to simple text extraction
                    logger.info("Falling back to simple text extraction")
                    reader = PdfReader(pdf_temp.name)
                    doc = Document()
                    
                    for page in reader.pages:
                        text = page.extract_text()
                        if text.strip():
                            doc.add_paragraph(text.strip())
                        
                        # Add page break after each page except the last one
                        if page != reader.pages[-1]:
                            doc.add_page_break()
                    
                    # Save to BytesIO
                    output_buffer = BytesIO()
                    doc.save(output_buffer)
                    output_buffer.seek(0)
                    
                    logger.info("Successfully extracted text to Word document")
                    return output_buffer
                    
        except Exception as e:
            logger.error(f"Error converting PDF to Word: {str(e)}")
            raise ValueError(f"Failed to convert PDF to Word: {str(e)}")

    @staticmethod
    def word_to_pdf(docx_data: Union[str, bytes, BytesIO]) -> BytesIO:
        """Convert Word document to PDF
        
        Args:
            docx_data: Word document data as file path, bytes, or BytesIO
            
        Returns:
            BytesIO object containing the PDF data
        """
        try:
            # Create temporary files for conversion
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as docx_temp, \
                 tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_temp:
                
                # Write Word data to temp file
                if isinstance(docx_data, str):
                    with open(docx_data, 'rb') as f:
                        docx_temp.write(f.read())
                elif isinstance(docx_data, bytes):
                    docx_temp.write(docx_data)
                elif isinstance(docx_data, BytesIO):
                    docx_temp.write(docx_data.getvalue())
                else:
                    raise ValueError("Invalid Word document input type")
                
                docx_temp.flush()
                
                # Convert Word to PDF
                if platform.system() == 'Windows':
                    # Use Word's COM interface on Windows
                    docx2pdf.convert(docx_temp.name, pdf_temp.name)
                else:
                    # On non-Windows platforms, use LibreOffice
                    try:
                        subprocess.run([
                            'soffice',
                            '--headless',
                            '--convert-to',
                            'pdf',
                            '--outdir',
                            os.path.dirname(pdf_temp.name),
                            docx_temp.name
                        ], check=True)
                        
                        # Rename the output file if necessary
                        generated_pdf = os.path.splitext(docx_temp.name)[0] + '.pdf'
                        if generated_pdf != pdf_temp.name:
                            os.rename(generated_pdf, pdf_temp.name)
                            
                    except subprocess.CalledProcessError:
                        raise RuntimeError(
                            "LibreOffice conversion failed. Please install LibreOffice:\n"
                            "- On macOS: brew install libreoffice\n"
                            "- On Ubuntu/Debian: sudo apt-get install libreoffice\n"
                        )
                    except FileNotFoundError:
                        raise RuntimeError(
                            "LibreOffice not found. Please install LibreOffice:\n"
                            "- On macOS: brew install libreoffice\n"
                            "- On Ubuntu/Debian: sudo apt-get install libreoffice\n"
                        )
                
                # Read the converted file into BytesIO
                with open(pdf_temp.name, 'rb') as f:
                    output_buffer = BytesIO(f.read())
                
                logger.info("Successfully converted Word document to PDF")
                return output_buffer
                
        except Exception as e:
            logger.error(f"Error converting Word to PDF: {str(e)}")
            raise ValueError(f"Failed to convert Word to PDF: {str(e)}") 