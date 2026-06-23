import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from app.core.logger import logger

class BM25Engine:
    def __init__(self):
        self.bm25 = None
        self.corpus_chunks = []
        self.corpus_metadata = []

    def _preprocess_text(self, text: str) -> List[str]:
        
        lowercased = text.lower()
        tokens = re.findall(r'\b\w+\b', lowercased)
        return tokens

    def fit(self, chunks: List[str], metadatas: List[Dict[str, Any]] = None):
        
        if not chunks:
            logger.warning("Empty chunk dataset passed to BM25 Engine.")
            return

        self.corpus_chunks = chunks
       
        self.corpus_metadata = metadatas if metadatas else [{}] * len(chunks)
        
        logger.info(f"Tokenizing and indexing {len(chunks)} elements into BM25 matrix...")
        tokenized_corpus = [self._preprocess_text(chunk) for chunk in chunks]
        
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info("BM25 Keyword Matching Index successfully built!")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        
        if not self.bm25 or not self.corpus_chunks:
            logger.warning("BM25 Index is not fitted yet. Empty results returned.")
            return []

        logger.info(f"Executing lexical index scan for query: '{query}'")
        tokenized_query = self._preprocess_text(query)
        
        scores = self.bm25.get_scores(tokenized_query)
        
        ranked_results = sorted(
            zip(self.corpus_chunks, self.corpus_metadata, scores),
            key=lambda x: x[2],
            reverse=True
        )

        final_hits = []
        for chunk, meta, score in ranked_results[:top_k]:
            if score > 0: 
                final_hits.append({
                    "content": chunk,
                    "metadata": meta,
                    "lexical_score": float(score),
                    "type": "lexical"
                })
                
        logger.info(f"BM25 Search completed. Extracted top {len(final_hits)} keyword matches.")
        return final_hits