from typing import List
import chromadb

from app.core.config import settings
from app.core.logger import logger
from app.rag.embedding import EmbeddingEngine


class VectorDBEngine:

    def __init__(self):
        self.chroma_path = settings.CHROMA_DB_PATH
        self.collection_name = settings.COLLECTION_NAME

        self.embedding_engine = EmbeddingEngine()

        self.client = chromadb.PersistentClient(
            path=self.chroma_path
        )

        logger.info(
            f"Chroma Collection '{self.collection_name}' initialized."
        )

    # -------------------------------------------------
    # Always return latest collection
    # -------------------------------------------------
    def get_collection(self):
        return self.client.get_or_create_collection(
            name=self.collection_name
        )

    # -------------------------------------------------
    # Reset Collection
    # -------------------------------------------------
    def reset_collection(self):
        """
        Delete previous vectors and create a fresh collection.
        """

        try:
            self.client.delete_collection(self.collection_name)
            logger.info("Previous Chroma collection deleted.")
        except Exception:
            pass

        self.client.get_or_create_collection(
            name=self.collection_name
        )

        logger.info("Fresh Chroma collection created.")

    # -------------------------------------------------
    # Upsert Chunks
    # -------------------------------------------------
    def upsert_chunks(
        self,
        chunks: List[str],
        source_name: str,
        source_type: str,
        chunk_metadatas=None
    ):

        collection = self.get_collection()

        embeddings = self.embedding_engine.get_embeddings(
            chunks
        ).tolist()

        ids = []
        metadatas = []

        for i, chunk in enumerate(chunks):

            ids.append(f"{source_type}_{i}")

            metadata = {
                "source": source_name,
                "source_type": source_type,
                "chunk_id": i
            }

            if chunk_metadatas and i < len(chunk_metadatas):
                metadata.update(chunk_metadatas[i])

            metadatas.append(metadata)

        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )

        logger.info(f"{len(chunks)} chunks stored.")

    # -------------------------------------------------
    # Query
    # -------------------------------------------------
    def query_similarity(
        self,
        query_text: str,
        top_k: int = 4,
        source_type=None
    ):

        collection = self.get_collection()

        query_vector = self.embedding_engine.get_query_embedding(
            query_text
        )

        where = None

        if source_type:

            if isinstance(source_type, list):

                where = {
                    "source_type": {
                        "$in": source_type
                    }
                }

            else:

                where = {
                    "source_type": source_type
                }

        return collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where
        )