from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal


from app.loaders.youtube_loader import YouTubeLoader
from app.loaders.website_loader import WebsiteLoader
from app.loaders.github_loader import GitHubLoader
from app.rag.chunker import create_chunks
from app.db.models import Document
from app.core.logger import logger


from app.services.ingestion_service import _rag_pipeline

_youtube_loader = YouTubeLoader()
_website_loader = WebsiteLoader()
_github_loader = GitHubLoader()


class UnifiedIngestRequest(BaseModel):
    url: str
    source_type: Literal["youtube", "website", "github"]


def _save_and_ingest(url: str, source_type: str, raw_text: str, db: Session, single_chunk: bool = False) -> dict:
    
    if not raw_text or not raw_text.strip():
        raise ValueError(f"No content extracted from {source_type} source: {url}")

    MAX_SINGLE_CHUNK_CHARS = 12000 

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

    db_doc = Document(
        source_name=url,
        source_type=source_type,
        total_chunks=len(chunks),
        metadata_dict={"url": url},
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

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


def ingest_youtube(url: str, db: Session) -> dict:
    loader_response = _youtube_loader.load(url)
    raw_text = loader_response[0]["text"] if loader_response else ""
    logger.info(f"YouTube transcript loaded for {url}, length={len(raw_text)}")
    return _save_and_ingest(url, "youtube", raw_text, db, single_chunk=True)


def ingest_website(url: str, db: Session) -> dict:
    raw_text = _website_loader.load(url)
    logger.info(f"Website content loaded for {url}, length={len(raw_text) if raw_text else 0}")
    return _save_and_ingest(url, "website", raw_text, db)


def ingest_github(url: str, db: Session) -> dict:
    repo_files = _github_loader.load(url)
    raw_text = "\n\n".join([f.get("text", "") for f in repo_files]) if repo_files else ""
    logger.info(f"GitHub repo loaded for {url}, files={len(repo_files) if repo_files else 0}")
    return _save_and_ingest(url, "github", raw_text, db)


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