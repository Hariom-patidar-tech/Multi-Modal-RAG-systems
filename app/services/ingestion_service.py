import os
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Document
from app.core.logger import logger
from app.utils.file_utils import save_uploaded_file

# Retrieval aur Ingestion ke liye important components imports
from app.rag.retriever import HybridRetriever
from app.rag.llm import LLMEngine
from app.rag.vectordb import VectorDBEngine
from app.rag.reranker import RerankerEngine

BASE_UPLOAD_DIR = "storage/uploads"

# ==========================================
# 1. CORE RAG PIPELINE ORCHESTRATOR CLASS
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

    def run_ingestion(self, file_path: str, filename: str, doc_id: int) -> list:
        from app.loaders.pdf_loader import PdfLoader
        from app.rag.chunker import create_chunks

        logger.info(f"Starting pipeline core ingestion execution for: {filename} with ID: {doc_id}")
        
        loader = PdfLoader()
        pages = loader.load(file_path)
        full_text = "\n".join([page["text"] for page in pages])
        chunks = create_chunks(full_text)
        
        if not chunks:
            return []

        # FIX: Yahan ab doc_id pass ho raha hai
        self.vector_db.upsert_chunks(
            chunks=chunks,
            source_name=filename,
            source_type="document", # Uniform type 'document' rakha hai
            doc_id=doc_id 
        )

        self.initialize_lexical_index(chunks)
        return chunks

    def initialize_lexical_index(self, chunks: list):
        """
        In-memory chunk state ko extend karta hai aur hybrid retriever 
        ke BM25 engine matrix ko forcefully update karta hai.
        """
        self.lexical_chunks.extend(chunks)
        self.retriever.fit_bm25(self.lexical_chunks)
        logger.info("Pipeline lexical index state synchronized successfully.")

    def ask(
        self,
        question: str,
        source_type_filter: str = None
    ) -> Dict[str, Any]:

        logger.info(f"RAG Pipeline triggered for question: {question}")

        try:
            retrieved_docs = self.retriever.retrieve(
                query=question,
                final_top_k=5,
                source_type_filter=source_type_filter
            )

            if not retrieved_docs:
                return {
                    "question": question,
                    "answer": "No relevant information found.",
                    "citations": []
                }

            context = "\n\n".join([doc["content"] for doc in retrieved_docs])
            answer = self.llm.generate_answer(context=context, question=question)

            citations = []
            for doc in retrieved_docs:
                meta = doc.get("metadata", {})
                citations.append({
                    "source_name": meta.get("source", "Unknown Source"),
                    "source_type": meta.get("source_type", "unknown"),
                    "chunk_id": meta.get("chunk_id", "N/A")
                })

            return {
                "question": question,
                "answer": answer,
                "citations": citations
            }

        except Exception as e:
            logger.error(str(e))
            return {
                "question": question,
                "answer": f"Pipeline Error: {str(e)}",
                "citations": []
            }


# Global module singleton instance instantiate kiya
_rag_pipeline = RAGPipeline()


def rag_pipeline(question: str, source_type_filter: str = None):
    return _rag_pipeline.ask(question, source_type_filter)


# ==========================================
# 2. FIXED: INGESTION SERVICE LAYER FUNCTION
# ==========================================
def process_pdf(file, db: Session) -> dict:
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else "pdf"
    target_dir = os.path.join(BASE_UPLOAD_DIR, file_extension)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, file.filename)
    
    try:
        save_uploaded_file(file, file_path)
        
        # Step 1: Pehle DB mein entry karo taaki ID mil sake
        db_doc = Document(
            source_name=file.filename,
            source_type="document", # Uniformity maintain ki
            total_chunks=0, 
            metadata_dict={"file_path": file_path}
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        
        # Step 2: Pipeline ko ID ke saath call karo
        all_chunks = _rag_pipeline.run_ingestion(file_path, file.filename, doc_id=db_doc.id)

        if not all_chunks:
            raise ValueError("No chunks generated.")

        # Step 3: Chunks count update karo
        db_doc.total_chunks = len(all_chunks)
        db.commit()
        
        return {
            "document_id": db_doc.id,
            "filename": file.filename,
            "total_chunks": len(all_chunks),
            "status": "Indexed Successfully Across System Specs"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Ingestion service system failure: {str(e)}")
        raise Exception(f"Ingestion processing broken down: {str(e)}")