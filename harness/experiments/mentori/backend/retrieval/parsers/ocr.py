import pytesseract
from pdf2image import convert_from_path
from typing import List, Dict, Any
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class OCRParser:
    """
    Extracts text from scanned PDFs/images using Tesseract OCR.
    """
    
    def __init__(self, dpi: int = 300):
        self.dpi = dpi
        
    def parse(self, file_path: str, page_numbers: List[int] = None) -> List[Dict[str, Any]]:
        """
        Perform OCR on specific pages of a PDF.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        logger.info(f"Running OCR on {path.name} (pages: {page_numbers or 'all'})")
        
        # Convert PDF to images
        # Note: pdf2image requires poppler installed on system too! 
        # We should add that to the list of requirements for the user.
        try:
            images = convert_from_path(file_path, dpi=self.dpi)
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            raise RuntimeError(f"pdf2image failed. Is poppler installed? Error: {e}")

        results = []
        
        # Determine pages to process
        if page_numbers:
            # Filter images. Page numbers are 1-indexed.
            # safe guard against out of bounds
            pages_to_process = []
            for p in page_numbers:
                idx = p - 1
                if 0 <= idx < len(images):
                    pages_to_process.append((p, images[idx]))
        else:
            pages_to_process = [(i+1, img) for i, img in enumerate(images)]
            
        for page_num, image in pages_to_process:
            try:
                # Run Tesseract
                text = pytesseract.image_to_string(image)
                
                # Get detailed data for confidence (optional, skipped for speed for now)
                # data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                results.append({
                    "page_number": page_num,
                    "text": text,
                    "method": "ocr",
                    "char_count": len(text)
                })
            except Exception as e:
                logger.error(f"OCR failed on page {page_num}: {e}")
                results.append({
                    "page_number": page_num,
                    "text": "",
                    "error": str(e),
                    "method": "ocr_failed"
                })
                
        return results
