from .config import *
from typing import Union, List
from io import BytesIO

class MergeOperations:
    @staticmethod
    def merge_pdfs(pdf_data_list: List[Union[str, bytes, BytesIO]]) -> BytesIO:
        """Merge multiple PDFs into one
        
        Args:
            pdf_data_list: List of PDFs as file paths, bytes, or BytesIO objects
            
        Returns:
            BytesIO object containing the merged PDF data
        """
        if not pdf_data_list:
            raise ValueError("No PDF files provided for merging")
            
        merger = None
        try:
            merger = PdfMerger()
            
            # Process each PDF
            for pdf_data in pdf_data_list:
                try:
                    if isinstance(pdf_data, str):
                        # Verify file exists and is valid
                        if not os.path.exists(pdf_data):
                            raise ValueError(f"PDF file not found: {pdf_data}")
                        if not os.access(pdf_data, os.R_OK):
                            raise ValueError(f"PDF file is not readable: {pdf_data}")
                        if os.path.getsize(pdf_data) == 0:
                            raise ValueError(f"PDF file is empty: {pdf_data}")
                        with open(pdf_data, 'rb') as file:
                            merger.append(fileobj=file)
                    elif isinstance(pdf_data, bytes):
                        merger.append(BytesIO(pdf_data))
                    elif isinstance(pdf_data, BytesIO):
                        merger.append(pdf_data)
                    else:
                        raise ValueError(f"Invalid PDF input type")
                    
                    logger.info("Successfully appended PDF")
                except Exception as e:
                    logger.error(f"Error processing PDF: {str(e)}")
                    raise ValueError(f"Failed to process PDF: {str(e)}")
            
            # Write merged PDF to buffer
            output_buffer = BytesIO()
            merger.write(output_buffer)
            output_buffer.seek(0)
            
            logger.info("Successfully merged PDFs")
            return output_buffer
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            raise ValueError(f"Failed to merge PDFs: {str(e)}")
        finally:
            if merger:
                merger.close()
                logger.info("Closed PDF merger") 