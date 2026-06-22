from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal

# Loaders and Engine Imports (Aapke existing imports)
from app.loaders.youtube_loader import YouTubeLoader
from app.loaders.website_loader import WebsiteLoader
from app.loaders.github_loader import GitHubLoader
from app.rag.chunker import create_chunks
from app.db.models import Document
from app.core.logger import logger

# Ingestion ka SAARA kaam ab isi shared pipeline se hoga,
# taaki vector_db aur BM25 lexical index dono jagah SYNC rahein
# (document/PDF upload wale flow ke saath bhi)
from app.services.ingestion_service import _rag_pipeline

# Global loader instances
_youtube_loader = YouTubeLoader()
_website_loader = WebsiteLoader()
_github_loader = GitHubLoader()


# 1. Request schema (route mein bhi use hota hai)
class UnifiedIngestRequest(BaseModel):
    url: str
    source_type: Literal["youtube", "website", "github"]


def _save_and_ingest(url: str, source_type: str, raw_text: str, db: Session, single_chunk: bool = False) -> dict:
    """
    Common helper: chunk banao, DB me Document entry banao,
    aur RAGPipeline ke through vector DB + lexical index me daalo.
    Isse doc_id sahi se set hota hai aur query time pe filter kaam karta hai.

    single_chunk=True: poora raw_text EK hi chunk ke roop mein store hoga
    (chote YouTube videos ke liye useful, taaki context fragment na ho).
    Agar text bahut lamba hai (>12000 chars, LLM context limit ke liye risky),
    to safety ke liye normal chunking par fallback hota hai.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError(f"No content extracted from {source_type} source: {url}")

    MAX_SINGLE_CHUNK_CHARS = 12000  # ~3000 tokens, Groq context ke liye safe

    if single_chunk and len(raw_text) <= MAX_SINGLE_CHUNK_CHARS:
        chunks = [raw_text.strip()]
        logger.info(f"Storing {source_type} content as a SINGLE chunk ({len(raw_text)} chars).")
    else:
        if single_chunk:
            logger.warning(
                f"{source_type} content too long ({len(raw_text)} chars) for single-chunk mode, "
                f"falling back to normal chunking."
            )
        chunks = create_chunks(raw_text)

    # DB entry pehle banao taaki doc_id mil jaye
    db_doc = Document(
        source_name=url,
        source_type=source_type,
        total_chunks=len(chunks),
        metadata_dict={"url": url},
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Vector DB + lexical (BM25) index — dono ek hi pipeline se
    _rag_pipeline.run_ingestion(
        chunks=chunks,
        source_name=url,
        source_type=source_type,
        doc_id=db_doc.id,
    )

    return {
        "status": "success",
        "document_id": db_doc.id,
        "source_type": source_type,
        "chunks_added": len(chunks),
    }


# --- Ingestion Functions (ab yeh fully kaam karte hain) ---
def ingest_youtube(url: str, db: Session) -> dict:
    loader_response = _youtube_loader.load(url)
    raw_text = loader_response[0]["text"] if loader_response else ""
    logger.info(f"YouTube transcript loaded for {url}, length={len(raw_text)}")
    # single_chunk=True: chote/medium videos ka poora transcript ek context mein jaata hai
    return _save_and_ingest(url, "youtube", raw_text, db, single_chunk=True)


def ingest_website(url: str, db: Session) -> dict:
    # WebsiteLoader.load() seedha plain string return karta hai (list of dicts NAHI)
    raw_text = _website_loader.load(url)
    logger.info(f"Website content loaded for {url}, length={len(raw_text) if raw_text else 0}")
    return _save_and_ingest(url, "website", raw_text, db)


def ingest_github(url: str, db: Session) -> dict:
    repo_files = _github_loader.load(url)
    # GitHubLoader assumed to return a list of files like [{"text": "...", "path": "..."}]
    raw_text = "\n\n".join([f.get("text", "") for f in repo_files]) if repo_files else ""
    logger.info(f"GitHub repo loaded for {url}, files={len(repo_files) if repo_files else 0}")
    return _save_and_ingest(url, "github", raw_text, db)


# 2. UNIFIED ROUTER — ek hi function, sab source types ke liye
def route_ingestion(payload: UnifiedIngestRequest, db: Session) -> dict:
    """
    Ab se sirf ye ek function call hoga, chahe source kuch bhi ho.
    """
    if payload.source_type == "youtube":
        return ingest_youtube(payload.url, db)
    elif payload.source_type == "website":
        return ingest_website(payload.url, db)
    elif payload.source_type == "github":
        return ingest_github(payload.url, db)
    else:
        raise ValueError("Invalid source_type! Use: youtube, website, or github.")