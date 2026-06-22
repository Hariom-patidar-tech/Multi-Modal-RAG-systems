from app.rag.retriever import HybridRetriever
from app.rag.llm import LLMEngine
from app.rag.vectordb import VectorDBEngine
from app.rag.reranker import RerankerEngine
from app.core.logger import logger
from typing import Dict, Any


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

    def run_ingestion(self, file_path: str, filename: str, doc_id: int = None) -> list:
        """
        PDF load karega -> Text extract karega -> Chunk banayega -> 
        ChromaDB me store karega -> BM25 fit karega -> Chunks return karega.
        """
        from app.loaders.pdf_loader import PdfLoader
        from app.rag.chunker import create_chunks

        logger.info(f"Starting pipeline core ingestion execution for: {filename}")
        
        # 1. Page-aware loader initialize aur text extraction
        loader = PdfLoader()
        pages = loader.load(file_path)
        
        # 2. Saare pages ke text ko single string me combine karna safely
        full_text = "\n".join([page["text"] for page in pages])
        
        # 3. Text ko semantic sub-chunks me split karna
        chunks = create_chunks(full_text)
        
        if not chunks:
            logger.warning(f"No extractable tokens or chunks generated for {filename}")
            return []

        # 4. ChromaDB/Vector DB storage synchronization mapping
        self.vector_db.upsert_chunks(
            chunks=chunks,
            source_name=filename,
            source_type="pdf",
            doc_id=doc_id
        )

        # 5. BM25 algorithm execution index matching matrix update
        self.initialize_lexical_index(chunks)

        # 6. Chunks list return karna database listing mapping ke liye
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
                    
                }

            context = "\n\n".join([doc["content"] for doc in retrieved_docs])
            answer = self.llm.generate_answer(context=context, question=question)

            citations = [{"source": doc.get("metadata", {}).get("source")} for doc in retrieved_docs]

            return {
                "question": question,
                "answer": answer,
                "citations": citations
            }

        except Exception as e:
            logger.error(str(e))
            return {
                "question": question,
                "answer": f"Pipeline Error: {str(e)}"
                
            }


# Global module singleton instance
pipeline = RAGPipeline()


def rag_pipeline(question: str, source_type_filter: str = None):
    return pipeline.ask(question, source_type_filter)