from .config import *

class CompressionOperations:
    @staticmethod
    def compress_pdf(pdf_file: str, output_path: str, quality: str = "medium") -> dict:
        """Compress PDF with different quality settings
        
        Args:
            pdf_file: Input PDF file path
            output_path: Output PDF file path
            quality: Compression quality ('low', 'medium', or 'high')
            
        Returns:
            dict containing compression information:
            - output_path: Path to compressed PDF
            - original_size: Original file size in bytes
            - compressed_size: Compressed file size in bytes
            - reduction_percentage: Size reduction percentage
        """
        try:
            # Get original size
            original_size = os.path.getsize(pdf_file)
            
            def compress_with_params(doc, params, image_scale):
                """Helper function to compress with parameters and check reduction"""
                temp_output = output_path + ".temp"
                doc.save(temp_output, **params)
                temp_size = os.path.getsize(temp_output)
                reduction = ((original_size - temp_size) / original_size) * 100
                return temp_output, temp_size, reduction
            
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
            doc = fitz.open(pdf_file)
            
            for scale in settings["scales"]:
                # Reset document
                doc = fitz.open(pdf_file)
                
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
                temp_output, compressed_size, reduction = compress_with_params(
                    doc, settings["params"], scale
                )
                
                # Check if we achieved target reduction
                if reduction >= settings["target"] or \
                   (reduction >= settings["min_target"] and scale == settings["scales"][-1]):
                    break
            
            # Finalize output
            if os.path.exists(temp_output):
                os.replace(temp_output, output_path)
            else:
                doc.save(output_path, **settings["params"])
                compressed_size = os.path.getsize(output_path)
                reduction = ((original_size - compressed_size) / original_size) * 100
            
            doc.close()
            
            result = {
                "output_path": output_path,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "reduction_percentage": round(reduction, 2)
            }
            
            logger.info(
                f"Compression complete: Original size: {format_size(original_size)}, "
                f"Compressed size: {format_size(compressed_size)}, "
                f"Reduction: {result['reduction_percentage']}%"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error compressing PDF: {str(e)}")
            raise ValueError(f"Failed to compress PDF: {str(e)}") 