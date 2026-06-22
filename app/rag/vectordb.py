from typing import List, Dict, Any, Optional
import chromadb
from app.core.config import settings
from app.core.logger import logger
from app.rag.embedding import EmbeddingEngine

class VectorDBEngine:
    def __init__(self):
        self.chroma_path = settings.CHROMA_DB_PATH
        self.collection_name = settings.COLLECTION_NAME
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.embedding_engine = EmbeddingEngine()
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        logger.info(f"ChromaDB Collection '{self.collection_name}' is ready.")

    def upsert_chunks(self, chunks, source_name, source_type, doc_id=None, chunk_metadatas=None):
        embeddings = self.embedding_engine.get_embeddings(chunks).tolist()
        ids, metadatas = [], []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{source_name}_{source_type}_{i}"
            ids.append(chunk_id)
            meta = {
                "source": source_name, 
                "source_type": source_type, 
                "chunk_id": i, 
                "doc_id": int(doc_id) if doc_id else None
            }
            if chunk_metadatas and i < len(chunk_metadatas): 
                meta.update(chunk_metadatas[i])
            metadatas.append(meta)

        self.collection.upsert(documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)
        return ids

    def query_similarity(
        self, 
        query_text: str, 
        top_k: int = 4, 
        doc_id: int = None, 
        source_type: Any = None
    ) -> Dict[str, Any]:
        """
        Query similarity with optional doc_id and source_type filtering.
        """
        query_vector = self.embedding_engine.get_query_embedding(query_text)
        conditions = []
        
        if doc_id: 
            conditions.append({"doc_id": int(doc_id)})
        
        if source_type:
            # Agar source_type list mein hai (e.g., ["pdf", "document"]), $in use karo
            if isinstance(source_type, list):
                conditions.append({"source_type": {"$in": source_type}})
            else:
                conditions.append({"source_type": source_type})
        
        # Filter construct karo
        where_filter = {"$and": conditions} if len(conditions) > 1 else (conditions[0] if conditions else None)
        
        return self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_filter
        )