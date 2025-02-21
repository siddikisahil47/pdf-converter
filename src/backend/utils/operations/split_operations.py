from .config import *
from typing import Union, List
from io import BytesIO

class SplitOperations:
    @staticmethod
    def split_pdf(pdf_data: Union[str, bytes, BytesIO], split_options: dict = None) -> List[BytesIO]:
        """Split PDF based on various options
        
        Args:
            pdf_data: PDF data as file path, bytes, or BytesIO
            split_options: Dictionary containing split options:
                - pages: List of specific page numbers to extract
                - ranges: List of [start, end] ranges
                - first_n: Extract first N pages
                - last_n: Extract last N pages
                
        Returns:
            List of BytesIO objects containing the split PDFs
        """
        try:
            # Open PDF from various input types
            if isinstance(pdf_data, str):
                reader = PdfReader(pdf_data)
            elif isinstance(pdf_data, bytes):
                reader = PdfReader(BytesIO(pdf_data))
            elif isinstance(pdf_data, BytesIO):
                reader = PdfReader(pdf_data)
            else:
                raise ValueError("Invalid PDF input type")
            
            total_pages = len(reader.pages)
            output_buffers = []
            
            if not split_options:
                # Default: split all pages into separate PDFs
                for page_num in range(total_pages):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[page_num])
                    output_buffer = BytesIO()
                    writer.write(output_buffer)
                    output_buffer.seek(0)
                    output_buffers.append(output_buffer)
                    logger.info(f"Created PDF for page {page_num + 1}")
                return output_buffers
            
            # Handle specific pages
            if 'pages' in split_options:
                pages = split_options['pages']
                for page_num in pages:
                    if 1 <= page_num <= total_pages:
                        writer = PdfWriter()
                        writer.add_page(reader.pages[page_num - 1])
                        output_buffer = BytesIO()
                        writer.write(output_buffer)
                        output_buffer.seek(0)
                        output_buffers.append(output_buffer)
                        logger.info(f"Created PDF for page {page_num}")
            
            # Handle page ranges
            if 'ranges' in split_options:
                for range_num, (start, end) in enumerate(split_options['ranges'], 1):
                    if start < 1:
                        start = 1
                    if end > total_pages:
                        end = total_pages
                    if start <= end:
                        writer = PdfWriter()
                        for page_num in range(start - 1, end):
                            writer.add_page(reader.pages[page_num])
                        output_buffer = BytesIO()
                        writer.write(output_buffer)
                        output_buffer.seek(0)
                        output_buffers.append(output_buffer)
                        logger.info(f"Created PDF with pages {start} to {end}")
            
            # Handle first N pages
            if 'first_n' in split_options:
                n = min(split_options['first_n'], total_pages)
                if n > 0:
                    writer = PdfWriter()
                    for page_num in range(n):
                        writer.add_page(reader.pages[page_num])
                    output_buffer = BytesIO()
                    writer.write(output_buffer)
                    output_buffer.seek(0)
                    output_buffers.append(output_buffer)
                    logger.info(f"Created PDF with first {n} pages")
            
            # Handle last N pages
            if 'last_n' in split_options:
                n = min(split_options['last_n'], total_pages)
                if n > 0:
                    writer = PdfWriter()
                    for page_num in range(total_pages - n, total_pages):
                        writer.add_page(reader.pages[page_num])
                    output_buffer = BytesIO()
                    writer.write(output_buffer)
                    output_buffer.seek(0)
                    output_buffers.append(output_buffer)
                    logger.info(f"Created PDF with last {n} pages")
            
            if not output_buffers:
                raise ValueError("No pages were extracted based on the provided options")
                
            return output_buffers
            
        except Exception as e:
            logger.error(f"Error splitting PDF: {str(e)}")
            raise ValueError(f"Failed to split PDF: {str(e)}") 