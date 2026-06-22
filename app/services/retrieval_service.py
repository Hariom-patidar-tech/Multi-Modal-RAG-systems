from app.rag.pipeline import rag_pipeline
from typing import Any


def retrieve_answer(question: str, source_type_filter: Any = None):
    """
    Retrieve answer from RAG pipeline (HybridRetriever: vector + BM25 + reranker).
    NOTE: Yeh function abhi koi API route call nahi karta. Active query path
    `app/services/query_service.py -> ask_question()` hai. Yeh function future
    mein behtar retrieval quality (reranking ke saath) ke liye use ho sakta hai.
    """

    return rag_pipeline(question, source_type_filter)