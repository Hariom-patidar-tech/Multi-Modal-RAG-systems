from typing import Dict, Any

from app.rag.retriever import HybridRetriever
from app.rag.llm import LLMEngine
from app.rag.vectordb import VectorDBEngine
from app.rag.reranker import RerankerEngine
from app.core.logger import logger


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

    # ---------------------------------------------------------
    # INGESTION
    # ---------------------------------------------------------
    def run_ingestion(
        self,
        file_path: str,
        filename: str
    ) -> list:

        from app.loaders.pdf_loader import PdfLoader
        from app.rag.chunker import create_chunks

        logger.info(
            f"Starting pipeline ingestion for: {filename}"
        )

        loader = PdfLoader()

        pages = loader.load(file_path)

        full_text = "\n".join(
            page["text"] for page in pages
        )

        chunks = create_chunks(full_text)

        if not chunks:
            logger.warning(
                f"No chunks generated for {filename}"
            )
            return []

        # -------------------------------------------------
        # Clear previous uploaded source
        # -------------------------------------------------

        self.vector_db.reset_collection()

        # -------------------------------------------------
        # Store current document
        # -------------------------------------------------

        self.vector_db.upsert_chunks(
            chunks=chunks,
            source_name=filename,
            source_type="document",
        )

        # -------------------------------------------------
        # Reset BM25
        # -------------------------------------------------

        self.initialize_lexical_index(chunks)

        logger.info(
            f"Ingestion completed successfully ({len(chunks)} chunks)"
        )

        return chunks

    # ---------------------------------------------------------
    # BM25
    # ---------------------------------------------------------

    def initialize_lexical_index(
        self,
        chunks: list
    ):

        self.lexical_chunks = chunks

        self.retriever.fit_bm25(
            self.lexical_chunks
        )

        logger.info(
            "Lexical index updated successfully."
        )

    # ---------------------------------------------------------
    # ASK
    # ---------------------------------------------------------

    def ask(
        self,
        question: str,
        source_type_filter: str = None
    ) -> Dict[str, Any]:

        logger.info(
            f"Question received: {question}"
        )

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
                doc["content"]
                for doc in retrieved_docs
            )

            answer = self.llm.generate_answer(
                context=context,
                question=question
            )

            citations = []

            for doc in retrieved_docs:

                citations.append({
                    "source": doc.get(
                        "metadata",
                        {}
                    ).get(
                        "source",
                        "Unknown"
                    )
                })

            return {
                "question": question,
                "answer": answer,
                "citations": citations
            }

        except Exception as e:

            logger.exception(e)

            return {
                "question": question,
                "answer": f"Pipeline Error: {str(e)}",
                "citations": []
            }


# ---------------------------------------------------------
# Global Singleton
# ---------------------------------------------------------

pipeline = RAGPipeline()


def rag_pipeline(
    question: str,
    source_type_filter: str = None
):
    return pipeline.ask(
        question,
        source_type_filter
    )