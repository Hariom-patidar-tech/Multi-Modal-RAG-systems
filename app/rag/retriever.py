from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.rag.vectordb import VectorDBEngine
from app.rag.reranker import RerankerEngine  # Jo humne pichle step me banaya
from app.core.logger import logger

class HybridRetriever:
    def __init__(self, vector_db: VectorDBEngine, reranker: RerankerEngine):
        self.vector_db = vector_db
        self.reranker = reranker
        self.bm25 = None
        self.corpus_chunks = []

    def fit_bm25(self, chunks: List[str]):
        """
        Database me store saare current chunks se BM25 index ko prepare/fit karta hai.
        Jab bhi koi naya document upload/ingest hoga, is index ko refresh karna hoga.
        """
        if not chunks:
            logger.warning("No chunks provided to fit BM25 index.")
            return
        
        self.corpus_chunks = chunks
        # Tokenizing documents by lowercasing and splitting on whitespace
        tokenized_corpus = [chunk.lower().split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 Index successfully fitted with {len(chunks)} chunks.")

    def _bm25_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Internal helper: Keyword matching lexical search stream"""
        if not self.bm25 or not self.corpus_chunks:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        ranked_pairs = sorted(
            zip(self.corpus_chunks, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        results = []
        for chunk, score in ranked_pairs[:top_k]:
            if score > 0:  # Only pick nodes that have at least some keyword overlap
                results.append({
                    "content": chunk,
                    "metadata": {"source": "BM25 Keyword Engine", "source_type": "text"},
                    "score": float(score),
                    "type": "lexical"
                })
        return results

    def _vector_search(self, query: str, top_k: int = 10, source_type_filter: Any = None) -> List[Dict[str, Any]]:
        """Internal helper: Semantic concept vector search stream"""
        chroma_results = self.vector_db.query_similarity(
            query_text=query, 
            top_k=top_k, 
            source_type=source_type_filter
        )
        
        results = []
        if chroma_results and chroma_results.get('documents') and chroma_results['documents']:
            documents = chroma_results['documents'][0]
            metadatas = chroma_results.get('metadatas') or [{}] * len(documents)
            metadatas = metadatas[0] if metadatas and metadatas[0] is not None else [{}] * len(documents)
            distances_raw = chroma_results.get('distances') or [0.0] * len(documents)
            distances = distances_raw[0] if distances_raw and distances_raw[0] is not None else [0.0] * len(documents)
            
            for doc, meta, dist in zip(documents, metadatas, distances):
                results.append({
                    "content": doc,
                    "metadata": meta or {},
                    "score": float(1 - dist),  # Distance matrix inversion to get absolute score
                    "type": "semantic"
                })
        return results

    def retrieve(self, query: str, final_top_k: int = 5, source_type_filter: str = None) -> List[Dict[str, Any]]:
        """
        Main Entrance Strategy:
        Vector (Top 10) + BM25 (Top 10) ➔ Deduplication ➔ Reranker ➔ Strict Top 5
        """
        logger.info(f"Executing Multi-Source Hybrid Search for: '{query}'")
        
        # Reranker ko high-quality pool dene ke liye thode zyada candidates uthayenge
        candidate_pool_size = final_top_k * 2  # e.g., Top 10
        
        vector_candidates = self._vector_search(query, top_k=candidate_pool_size, source_type_filter=source_type_filter)
        bm25_candidates = self._bm25_search(query, top_k=candidate_pool_size)

        # Step 2: Merge streams and Deduplicate identical contents
        seen_contents = set()
        combined_candidates = []

        for item in vector_candidates + bm25_candidates:
            if item["content"] not in seen_contents:
                seen_contents.add(item["content"])
                combined_candidates.append(item)

        # Step 3: Run the production-grade cross encoder pipeline
        logger.info(f"Passing {len(combined_candidates)} deduplicated candidates to Reranker...")
        
        # FIXED: Changed 'top_n' to 'top_k' to match RerankerEngine implementation smoothly
        reranked_results = self.reranker.rerank(
            query=query,
            documents=combined_candidates,
            top_k=final_top_k
        )
        
        logger.info(f"Hybrid retrieval finished seamlessly. Extracted top {len(reranked_results)} items.")
        return reranked_results