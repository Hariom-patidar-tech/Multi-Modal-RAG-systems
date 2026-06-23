import os
from pypdf import PdfReader
from app.core.logger import logger
from typing import List, Dict, Any

class PdfLoader:
    def __init__(self):
        pass

    def load(self, file_path: str) -> List[Dict[str, Any]]:
        
        if not os.path.exists(file_path):
            logger.error(f"PDF file not found at path: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Opening and parsing PDF: {file_path}")
        pages_content = []

        try:
            reader = PdfReader(file_path)
            
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
                    logger.warning(f"Skipping page {page_number} in {file_path} due to extraction error: {str(page_err)}")
                    continue

            logger.info(f"Successfully extracted {len(pages_content)} valid pages from PDF.")
            return pages_content

        except Exception as e:
            logger.error(f"Critical error while reading PDF {file_path}: {str(e)}")
            raise Exception(f"PDF Parsing Failed: {str(e)}")