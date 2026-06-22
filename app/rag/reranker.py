from sentence_transformers import CrossEncoder

class RerankerEngine:
    def __init__(self):
        # Production-ready cross-encoder model initialize kiya
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(self, query: str, documents: list, top_k: int = 5):
        """
        Takes raw candidates pool and matches semantically against query 
        using deep attention mechanism.
        """
        if not documents:
            return []
            
        # FIXED: Dictionary objects se raw text 'content' extract kiya pairs banane ke liye
        pairs = [
            [query, doc["content"]]
            for doc in documents
        ]

        # Cross-Encoder framework se inference/scores predict kiye
        scores = self.reranker.predict(pairs)

        # FIXED: Originals candidate structures (with metadata) ko raw model scores ke saath zip karke sort kiya
        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        # Top K structured objects dictionary ke sath properly sliced return karein
        return [doc for doc, _ in ranked[:top_k]]