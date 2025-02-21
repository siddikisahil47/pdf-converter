from .config import *

class MergeOperations:
    @staticmethod
    def merge_pdfs(pdf_files: List[str], output_path: str) -> str:
        """Merge multiple PDF files into one
        
        Args:
            pdf_files: List of PDF file paths to merge
            output_path: Output path for merged PDF
            
        Returns:
            Path to the merged PDF file
        """
        if not pdf_files:
            raise ValueError("No PDF files provided for merging")
            
        merger = None
        try:
            merger = PdfMerger()
            
            # Process each PDF file
            for pdf_file in pdf_files:
                # Verify file exists and is valid
                if not os.path.exists(pdf_file):
                    raise ValueError(f"PDF file not found: {pdf_file}")
                if not os.access(pdf_file, os.R_OK):
                    raise ValueError(f"PDF file is not readable: {pdf_file}")
                if os.path.getsize(pdf_file) == 0:
                    raise ValueError(f"PDF file is empty: {pdf_file}")
                
                logger.info(f"Processing PDF file: {pdf_file}")
                
                # Append PDF to merger
                with open(pdf_file, 'rb') as file:
                    merger.append(fileobj=file)
                    logger.info(f"Successfully appended: {pdf_file}")
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write merged PDF
            with open(output_path, "wb") as output_file:
                merger.write(output_file)
                logger.info(f"Successfully wrote merged PDF to: {output_path}")
            
            # Verify output
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise ValueError("Failed to create valid output file")
                
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            raise ValueError(f"Failed to merge PDFs: {str(e)}")
        finally:
            if merger:
                merger.close()
                logger.info("Closed PDF merger") 