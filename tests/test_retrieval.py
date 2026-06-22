# FIXED: Purana functional import hatakar proper class-based RerankerEngine import kiya
from app.rag.reranker import RerankerEngine

def test_reranker():
    # FIXED: Engine ka instance create kiya
    reranker = RerankerEngine()

    # FIXED: Step 2 ke matching data structure ke mutabik documents ko dict format me convert kiya
    docs = [
        {"content": "Machine learning is AI.", "metadata": {"source_type": "text"}},
        {"content": "Python is a programming language.", "metadata": {"source_type": "text"}},
        {"content": "Deep learning is a subset of ML.", "metadata": {"source_type": "text"}}
    ]

    # FIXED: Instance variable se method call kiya aur top_k pass kiya
    result = reranker.rerank(
        query="What is machine learning?",
        documents=docs,
        top_k=2
    )

    # Asset check for pipeline output length limits
    assert len(result) == 2
    # Quality check: Pehla result Machine Learning se related hi hona chahiye
    assert "AI" in result[0]["content"] or "ML" in result[0]["content"]