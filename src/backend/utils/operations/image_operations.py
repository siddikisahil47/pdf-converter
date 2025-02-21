from .config import *

class ImageOperations:
    @staticmethod
    def pdf_to_images(pdf_data: Union[str, bytes, BytesIO], dpi: int = 200) -> List[BytesIO]:
        """Convert PDF pages to images with size optimization
        
        Args:
            pdf_data: PDF data as file path, bytes, or BytesIO
            dpi: Resolution in dots per inch (default: 200)
            
        Returns:
            List of BytesIO objects containing the generated images
        """
        try:
            # Calculate zoom factor
            zoom = dpi / 72  # standard PDF resolution is 72 DPI
            magnify = fitz.Matrix(zoom, zoom)
            
            # Open PDF from various input types
            if isinstance(pdf_data, str):
                doc = fitz.open(pdf_data)
            elif isinstance(pdf_data, bytes):
                doc = fitz.open(stream=pdf_data)
            elif isinstance(pdf_data, BytesIO):
                doc = fitz.open(stream=pdf_data.getvalue())
            else:
                raise ValueError("Invalid PDF input type")
            
            output_buffers = []
            
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
                
                # Save to BytesIO buffer
                img_buffer = BytesIO()
                img.save(
                    img_buffer,
                    "PNG",
                    optimize=True,
                    quality=85,
                    dpi=(dpi, dpi)
                )
                img_buffer.seek(0)
                output_buffers.append(img_buffer)
                
                logger.info(f"Converted page {page_num + 1} to image")
            
            doc.close()
            return output_buffers
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise ValueError(f"Failed to convert PDF to images: {str(e)}")

    @staticmethod
    def images_to_pdf(image_data: List[Union[str, bytes, BytesIO]]) -> BytesIO:
        """Convert images to PDF with size validation and optimization
        
        Args:
            image_data: List of image data (file paths, bytes, or BytesIO objects)
            
        Returns:
            BytesIO object containing the PDF data
        """
        if not image_data:
            raise ValueError("No image data provided")
            
        def resize_if_needed(img: Image.Image) -> Image.Image:
            """Resize image if it exceeds maximum dimensions"""
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                ratio = min(MAX_DIMENSION / img.width, MAX_DIMENSION / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                return img.resize(new_size, Image.Resampling.LANCZOS)
            return img
        
        def open_image(data: Union[str, bytes, BytesIO]) -> Image.Image:
            """Open image from various input types"""
            if isinstance(data, str):
                return Image.open(data)
            elif isinstance(data, bytes):
                return Image.open(BytesIO(data))
            elif isinstance(data, BytesIO):
                return Image.open(data)
            else:
                raise ValueError("Invalid image input type")
        
        try:
            # Process first image
            first_image = open_image(image_data[0])
            if first_image.mode != 'RGB':
                first_image = first_image.convert('RGB')
            first_image = resize_if_needed(first_image)
            
            # Process other images
            other_images = []
            for img_data in image_data[1:]:
                img = open_image(img_data)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img = resize_if_needed(img)
                other_images.append(img)
            
            # Save to BytesIO buffer
            pdf_buffer = BytesIO()
            first_image.save(pdf_buffer, "PDF", save_all=True, append_images=other_images)
            pdf_buffer.seek(0)
            
            logger.info(f"Successfully created PDF from {len(image_data)} images")
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error converting images to PDF: {str(e)}")
            raise ValueError(f"Failed to convert images to PDF: {str(e)}") 