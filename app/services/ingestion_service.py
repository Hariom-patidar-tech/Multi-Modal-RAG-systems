import os
from typing import Dict, Any, List

from app.core.logger import logger
from app.utils.file_utils import save_uploaded_file

from app.rag.retriever import HybridRetriever
from app.rag.llm import LLMEngine
from app.rag.vectordb import VectorDBEngine
from app.rag.reranker import RerankerEngine

BASE_UPLOAD_DIR = "storage/uploads"


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

    def run_ingestion(
        self,
        chunks: List[str],
        source_name: str,
        source_type: str
    ) -> list:

        logger.info(
            f"Processing ingestion for: {source_name} | Type: {source_type}"
        )

        if not chunks:
            return []

        # Har naye upload par purana data clear hoga
        self.vector_db.reset_collection()

        self.vector_db.upsert_chunks(
            chunks=chunks,
            source_name=source_name,
            source_type=source_type
        )

        self.initialize_lexical_index(chunks)
        return chunks

    def initialize_lexical_index(self, chunks: List[str]):
        self.lexical_chunks = chunks
        self.retriever.fit_bm25(self.lexical_chunks)
        logger.info("BM25 index initialized.")

    def ask(
        self,
        question: str,
        source_type_filter: Any = None
    ) -> Dict[str, Any]:

        logger.info(f"Question : {question}")

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

            context = "\n\n".join(
                [doc["content"] for doc in retrieved_docs]
            )

            answer = self.llm.generate_answer(
                context=context,
                question=question
            )

            citations = [
                {
                    "source": doc.get("metadata", {}).get("source")
                }
                for doc in retrieved_docs
            ]

            return {
                "question": question,
                "answer": answer,
                "citations": citations
            }

        except Exception as e:

            logger.error(e)

            return {
                "question": question,
                "answer": "Error processing request.",
                "citations": []
            }


_rag_pipeline = RAGPipeline()


def ingest_source_to_pipeline(
    source_name: str,
    source_type: str,
    content_chunks: List[str],
    metadata: dict = {}
):

    _rag_pipeline.run_ingestion(
        chunks=content_chunks,
        source_name=source_name,
        source_type=source_type
    )

    return {
        "status": "success",
        "source_name": source_name,
        "source_type": source_type,
        "chunks": len(content_chunks)
    }


def process_pdf(file):

    from app.loaders.pdf_loader import PdfLoader
    from app.rag.chunker import create_chunks

    file_path = os.path.join(
        BASE_UPLOAD_DIR,
        "pdf",
        file.filename
    )

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    save_uploaded_file(file, file_path)

    pages = PdfLoader().load(file_path)

    text = "\n".join([p["text"] for p in pages])

    chunks = create_chunks(text)

    return ingest_source_to_pipeline(
        file.filename,
        "document",
        chunks,
        {
            "path": file_path
        }
    )


SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


def process_document(file):

    from app.rag.chunker import create_chunks

    filename = file.filename or ""

    _, ext = os.path.splitext(filename)

    ext = ext.lower()

    if ext not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}"
        )

    subfolder = ext.lstrip(".")

    file_path = os.path.join(
        BASE_UPLOAD_DIR,
        subfolder,
        filename
    )

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    save_uploaded_file(file, file_path)

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

    else:
        text = ""

    if not text.strip():
        raise ValueError("No text found.")

    chunks = create_chunks(text)

    return ingest_source_to_pipeline(
        filename,
        "document",
        chunks,
        {
            "path": file_path,
            "file_type": ext
        }
    )