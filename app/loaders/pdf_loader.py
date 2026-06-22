import os
from pypdf import PdfReader
from app.core.logger import logger
from typing import List, Dict, Any

class PdfLoader:
    def __init__(self):
        pass

    def load(self, file_path: str) -> List[Dict[str, Any]]:
        """
        PDF file se page-by-page text extract karta hai taaki proper citation (page tracking) ho sake.
        Corrupt PDFs ke liye proper error catch aur logging handle karta hai.
        
        Returns:
            List[Dict]: [{'page': 1, 'text': '...'}, {'page': 2, 'text': '...'}]
        """
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found at path: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Opening and parsing PDF: {file_path}")
        pages_content = []

        try:
            # Safe Initialization: Corrupt PDF hone par yahi catch ho jayega
            reader = PdfReader(file_path)
            
            # Encrypted PDFs check
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise Exception("PDF is encrypted and password-protected.")

            total_pages = len(reader.pages)
            logger.info(f"Total pages detected: {total_pages}")

            for page_idx, page in enumerate(reader.pages):
                page_number = page_idx + 1
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        pages_content.append({
                            "page": page_number,
                            "text": page_text.strip()
                        })
                except Exception as page_err:
                    # Agar kisi ek specific page par parsing error aaye, toh poori file fail nahi hogi
                    logger.warning(f"Skipping page {page_number} in {file_path} due to extraction error: {str(page_err)}")
                    continue

            logger.info(f"Successfully extracted {len(pages_content)} valid pages from PDF.")
            return pages_content

        except Exception as e:
            logger.error(f"Critical error while reading PDF {file_path}: {str(e)}")
            raise Exception(f"PDF Parsing Failed: {str(e)}")