from types import SimpleNamespace

from app.core.config import settings
from app.rag import llm as llm_module
from app.services import query_service


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Test answer")
                )
            ]
        )


class FakeClient:
    def __init__(self):
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def test_query_service_uses_configured_groq_model(monkeypatch):
    model_name = "test/configured-model"
    client = FakeClient()

    class FakeVectorDB:
        def query_similarity(self, **kwargs):
            return {
                "documents": [["Relevant context"]],
                "metadatas": [[{"source": "test", "source_type": "document"}]],
            }

    monkeypatch.setattr(settings, "GROQ_MODEL", model_name)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(query_service, "_vector_db", FakeVectorDB())
    monkeypatch.setattr(query_service.groq, "Groq", lambda **kwargs: client)

    result = query_service.ask_question("Test question")

    assert result["status"] == "success"
    assert client.completions.calls[0]["model"] == model_name


def test_llm_engine_uses_configured_groq_model(monkeypatch):
    model_name = "test/configured-model"
    client = FakeClient()

    monkeypatch.setattr(settings, "GROQ_MODEL", model_name)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(llm_module, "Groq", lambda **kwargs: client)

    engine = llm_module.LLMEngine()
    answer = engine.generate_answer("Relevant context", "Test question")

    assert answer == "Test answer"
    assert client.completions.calls[0]["model"] == model_name
