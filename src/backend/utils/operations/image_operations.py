from .config import *

class ImageOperations:
    @staticmethod
    def pdf_to_images(pdf_file: str, output_dir: str, dpi: int = 200) -> List[str]:
        """Convert PDF pages to images with size optimization
        
        Args:
            pdf_file: Input PDF file path
            output_dir: Output directory for images
            dpi: Resolution in dots per inch (default: 200)
            
        Returns:
            List of paths to the generated image files
        """
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Calculate zoom factor
            zoom = dpi / 72  # standard PDF resolution is 72 DPI
            magnify = fitz.Matrix(zoom, zoom)
            
            # Process PDF
            doc = fitz.open(pdf_file)
            output_files = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=magnify)
                
                # Convert to PIL Image for optimization
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Optimize size if needed
                if img.width > 2000 or img.height > 2000:
                    ratio = min(2000/img.width, 2000/img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                output_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
                img.save(
                    output_path,
                    "PNG",
                    optimize=True,
                    quality=85,
                    dpi=(dpi, dpi)
                )
                
                output_files.append(output_path)
                logger.info(f"Converted page {page_num + 1} to image: {output_path}")
            
            doc.close()
            return output_files
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise ValueError(f"Failed to convert PDF to images: {str(e)}")

    @staticmethod
    def images_to_pdf(image_files: List[str], output_path: str) -> str:
        """Convert images to PDF with size validation and optimization
        
        Args:
            image_files: List of image file paths
            output_path: Output PDF file path
            
        Returns:
            Path to the created PDF file
        """
        if not image_files:
            raise ValueError("No image files provided")
            
        def resize_if_needed(img: Image.Image) -> Image.Image:
            """Resize image if it exceeds maximum dimensions"""
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                ratio = min(MAX_DIMENSION / img.width, MAX_DIMENSION / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                return img.resize(new_size, Image.Resampling.LANCZOS)
            return img
        
        try:
            # Process first image
            first_image = Image.open(image_files[0])
            if first_image.mode != 'RGB':
                first_image = first_image.convert('RGB')
            first_image = resize_if_needed(first_image)
            
            # Process other images
            other_images = []
            for image_path in image_files[1:]:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img = resize_if_needed(img)
                other_images.append(img)
            
            # Save as PDF
            first_image.save(output_path, "PDF", save_all=True, append_images=other_images)
            logger.info(f"Successfully created PDF from {len(image_files)} images")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting images to PDF: {str(e)}")
            raise ValueError(f"Failed to convert images to PDF: {str(e)}") 