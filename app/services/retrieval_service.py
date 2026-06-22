from app.rag.pipeline import rag_pipeline


def retrieve_answer(question: str):
    """
    Retrieve answer from RAG pipeline
    """

    return rag_pipeline(question)