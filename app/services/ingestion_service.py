import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import Document
from app.core.logger import logger
from app.utils.file_utils import save_uploaded_file

# Retrieval aur Ingestion components
from app.rag.retriever import HybridRetriever
from app.rag.llm import LLMEngine
from app.rag.vectordb import VectorDBEngine
from app.rag.reranker import RerankerEngine

BASE_UPLOAD_DIR = "storage/uploads"

# ==========================================
# 1. CORE RAG PIPELINE ORCHESTRATOR
# ==========================================
class RAGPipeline:
    def __init__(self):
        self.vector_db = VectorDBEngine()
        self.reranker = RerankerEngine()
        self.retriever = HybridRetriever(
            vector_db=self.vector_db,
            reranker=self.reranker
        )
        self.llm = LLMEngine()
        self.lexical_chunks = []

    def run_ingestion(self, chunks: List[str], source_name: str, source_type: str, doc_id: int) -> list:
        """
        Generic ingestion method jo kisi bhi source ke chunks ko process karega.
        """
        logger.info(f"Processing ingestion for: {source_name} | Type: {source_type} | ID: {doc_id}")
        
        if not chunks:
            return []

        # Vector DB mein metadata ke saath store karna
        self.vector_db.upsert_chunks(
            chunks=chunks,
            source_name=source_name,
            source_type=source_type, 
            doc_id=doc_id 
        )

        self.initialize_lexical_index(chunks)
        return chunks

    def initialize_lexical_index(self, chunks: List[str]):
        self.lexical_chunks.extend(chunks)
        self.retriever.fit_bm25(self.lexical_chunks)
        logger.info("Pipeline lexical index state synchronized.")

    def ask(self, question: str, source_type_filter: Any = None) -> Dict[str, Any]:
        logger.info(f"RAG Pipeline triggered for: '{question}' with filter: {source_type_filter}")
        try:
            retrieved_docs = self.retriever.retrieve(
                query=question,
                final_top_k=5,
                source_type_filter=source_type_filter
            )

            if not retrieved_docs:
                return {"question": question, "answer": "No relevant info found.", "citations": []}

            context = "\n\n".join([doc["content"] for doc in retrieved_docs])
            answer = self.llm.generate_answer(context=context, question=question)

            citations = [{"source": doc.get("metadata", {}).get("source")} for doc in retrieved_docs]
            return {"question": question, "answer": answer, "citations": citations}

        except Exception as e:
            logger.error(f"Pipeline Error: {str(e)}")
            return {"question": question, "answer": "Error processing request.", "citations": []}

# Singleton Instance
_rag_pipeline = RAGPipeline()

# ==========================================
# 2. UNIVERSAL INGESTION WRAPPER
# ==========================================
def ingest_source_to_pipeline(
    db: Session, 
    source_name: str, 
    source_type: str, 
    content_chunks: List[str], 
    metadata: dict = {}
) -> dict:
    """
    Yeh function generic hai. Aap PDF, YouTube, ya GitHub sabke liye ise use kar sakte hain.
    """
    try:
        # DB Entry
        db_doc = Document(
            source_name=source_name,
            source_type=source_type,
            total_chunks=len(content_chunks),
            metadata_dict=metadata
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        
        # Pipeline execution
        _rag_pipeline.run_ingestion(content_chunks, source_name, source_type, db_doc.id)
        
        return {"document_id": db_doc.id, "status": "Success"}
    except Exception as e:
        db.rollback()
        raise Exception(f"Ingestion Failed: {str(e)}")

# PDF ke liye specific wrapper (backward compatible — purane PDF-only callers ke liye)
def process_pdf(file, db: Session) -> dict:
    from app.loaders.pdf_loader import PdfLoader
    from app.rag.chunker import create_chunks
    
    file_path = os.path.join(BASE_UPLOAD_DIR, "pdf", file.filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    save_uploaded_file(file, file_path)
    
    pages = PdfLoader().load(file_path)
    text = "\n".join([p["text"] for p in pages])
    chunks = create_chunks(text)
    
    return ingest_source_to_pipeline(db, file.filename, "document", chunks, {"path": file_path})


# ==========================================
# 3. UNIFIED DOCUMENT UPLOAD (PDF / DOCX / TXT)
# ==========================================
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt"}


def process_document(file, db: Session) -> dict:
    """
    Generic document ingestion: file extension ke hisaab se sahi loader
    (PdfLoader / DocxLoader / load_txt_text) choose karta hai.
    PDF, DOCX, aur TXT — teeno yahin se guzarte hain.
    """
    from app.rag.chunker import create_chunks

    filename = file.filename or ""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{ext}'. Supported types: "
            f"{', '.join(sorted(SUPPORTED_DOCUMENT_EXTENSIONS))}"
        )

    # File ko uske type ke hisaab se subfolder mein save karo
    subfolder = ext.lstrip(".")  # "pdf" / "docx" / "txt"
    file_path = os.path.join(BASE_UPLOAD_DIR, subfolder, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    save_uploaded_file(file, file_path)

    logger.info(f"Processing document upload: {filename} | Detected type: {ext}")

    if ext == ".pdf":
        from app.loaders.pdf_loader import PdfLoader
        pages = PdfLoader().load(file_path)
        text = "\n".join([p["text"] for p in pages])

    elif ext == ".docx":
        from app.loaders.docx_loader import DocxLoader
        text = DocxLoader().load(file_path)

    elif ext == ".txt":
        from app.loaders.txt_loader import load_txt_text
        text = load_txt_text(file_path)

    if not text or not text.strip():
        raise ValueError(f"No extractable text found in {filename}")

    chunks = create_chunks(text)

    return ingest_source_to_pipeline(
        db, filename, "document", chunks, {"path": file_path, "file_type": ext}
    )