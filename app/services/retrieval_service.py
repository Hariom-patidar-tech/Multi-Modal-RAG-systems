from app.rag.pipeline import rag_pipeline
from typing import Any


def retrieve_answer(question: str, source_type_filter: Any = None):
    

    return rag_pipeline(question, source_type_filter)