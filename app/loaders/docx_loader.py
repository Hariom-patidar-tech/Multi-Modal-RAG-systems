import os
from docx import Document
from app.core.logger import logger

class DocxLoader:
    def __init__(self):
        pass

    def load(self, file_path: str) -> str:
        """
        DOCX file se paragraphs aur tables dono ka content extract karta hai.
        Tables ko Markdown/Structured format me convert kiya jata hai taaki LLM context samajh sake.
        """
        if not os.path.exists(file_path):
            logger.error(f"DOCX file not found at path: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Extracting content from DOCX: {file_path}")
        try:
            doc = Document(file_path)
            extracted_elements = []

            # 1. Paragraphs Extract Karein
            for para in doc.paragraphs:
                if para.text.strip():  # Khali lines ko skip karein
                    extracted_elements.append(para.text.strip())

            # 2. Tables Extract Karein (Structured Format me)
            for table_idx, table in enumerate(doc.tables):
                extracted_elements.append(f"\n--- Table {table_idx + 1} Start ---")
                
                for row in table.rows:
                    # Har cell ka text extract karke pipe (|) se join karein (Markdown-like structure)
                    row_text = [cell.text.strip() for cell in row.cells]
                    # Duplicate neighbor cells handle karne ke liye (merged cells clean-up)
                    row_string = " | ".join(row_text)
                    if row_string.strip():
                        extracted_elements.append(row_string)
                        
                extracted_elements.append(f"--- Table {table_idx + 1} End ---\n")

            # 3. Poore extracted parts ko join karein
            final_text = "\n".join(extracted_elements)
            logger.info(f"Successfully extracted DOCX content. Total length: {len(final_text)} characters.")
            return final_text

        except Exception as e:
            logger.error(f"Error while parsing DOCX file {file_path}: {str(e)}")
            raise Exception(f"DOCX parsing failed: {str(e)}")