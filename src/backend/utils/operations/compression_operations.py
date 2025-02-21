from .config import *
from typing import Union
from io import BytesIO

class CompressionOperations:
    @staticmethod
    def compress_pdf(pdf_data: Union[str, bytes, BytesIO], quality: str = "medium") -> BytesIO:
        """Compress PDF with different quality settings
        
        Args:
            pdf_data: PDF data as file path, bytes, or BytesIO
            quality: Compression quality ('low', 'medium', or 'high')
            
        Returns:
            BytesIO object containing the compressed PDF data
        """
        try:
            # Open PDF from various input types
            if isinstance(pdf_data, str):
                doc = fitz.open(pdf_data)
                original_size = os.path.getsize(pdf_data)
            elif isinstance(pdf_data, bytes):
                doc = fitz.open(stream=pdf_data)
                original_size = len(pdf_data)
            elif isinstance(pdf_data, BytesIO):
                doc = fitz.open(stream=pdf_data.getvalue())
                original_size = get_buffer_size(pdf_data)
            else:
                raise ValueError("Invalid PDF input type")
            
            def compress_with_params(doc, params):
                """Helper function to compress with parameters and check reduction"""
                output_buffer = BytesIO()
                doc.save(output_buffer, **params)
                compressed_size = get_buffer_size(output_buffer)
                reduction = ((original_size - compressed_size) / original_size) * 100
                return output_buffer, compressed_size, reduction
            
            # Base compression parameters
            base_params = {
                "deflate": True,
                "clean": True,
                "pretty": False,
                "linear": True,
            }
            
            # Quality-specific settings
            quality_settings = {
                "high": {
                    "params": {**base_params, "garbage": 4},
                    "scales": [0.5, 0.4, 0.3],
                    "target": 50,
                    "min_target": 15
                },
                "medium": {
                    "params": {**base_params, "garbage": 3},
                    "scales": [0.8, 0.7, 0.6],
                    "target": 15,
                    "min_target": 10
                },
                "low": {
                    "params": {**base_params, "garbage": 2},
                    "scales": [0.9, 0.85, 0.8],
                    "target": 5,
                    "min_target": 3
                }
            }
            
            settings = quality_settings[quality]
            best_output = None
            best_reduction = 0
            
            for scale in settings["scales"]:
                # Reset document
                if isinstance(pdf_data, str):
                    doc = fitz.open(pdf_data)
                elif isinstance(pdf_data, bytes):
                    doc = fitz.open(stream=pdf_data)
                else:
                    doc = fitz.open(stream=pdf_data.getvalue())
                
                # Process images
                for page in doc:
                    for img in page.get_images():
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        # Convert CMYK to RGB if needed
                        if pix.n - pix.alpha >= 4:
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                            
                        # Resize image based on quality
                        if quality == "high" or (quality == "medium" and (pix.width > 800 or pix.height > 800)) or \
                           (quality == "low" and (pix.width > 1500 or pix.height > 1500)):
                            new_width = max(100, int(pix.width * scale))
                            new_height = max(100, int(pix.height * scale))
                            pix = fitz.Pixmap(pix, new_width, new_height)
                            
                        page.replace_image(xref, pixmap=pix)
                
                # Try compression
                output_buffer, compressed_size, reduction = compress_with_params(
                    doc, settings["params"]
                )
                
                if reduction > best_reduction:
                    best_reduction = reduction
                    best_output = output_buffer
                
                # Check if we achieved target reduction
                if reduction >= settings["target"] or \
                   (reduction >= settings["min_target"] and scale == settings["scales"][-1]):
                    break
            
            # If no good compression was achieved, use basic compression
            if not best_output:
                best_output, compressed_size, reduction = compress_with_params(doc, settings["params"])
            
            doc.close()
            
            # Log compression results
            logger.info(
                f"Compression complete: Original size: {format_size(original_size)}, "
                f"Compressed size: {format_size(get_buffer_size(best_output))}, "
                f"Reduction: {best_reduction:.2f}%"
            )
            
            best_output.seek(0)
            return best_output
            
        except Exception as e:
            logger.error(f"Error compressing PDF: {str(e)}")
            raise ValueError(f"Failed to compress PDF: {str(e)}") 