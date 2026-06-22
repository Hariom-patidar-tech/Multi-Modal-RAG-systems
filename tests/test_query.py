from app.rag.pipeline import rag_pipeline


def test_rag_pipeline():

    question = "What is machine learning?"

    result = rag_pipeline(question)

    assert isinstance(result, dict)

    assert "answer" in result

    assert "question" in result