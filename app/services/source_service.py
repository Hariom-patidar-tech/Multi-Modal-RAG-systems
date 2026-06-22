from sqlalchemy.orm import Session
from app.loaders.youtube_loader import YouTubeLoader  
from app.loaders.website_loader import WebsiteLoader
from app.loaders.github_loader import GitHubLoader
from app.rag.chunker import create_chunks
from app.rag.vectordb import VectorDBEngine
from app.rag.pipeline import RAGPipeline
from app.db.models import Document
from app.core.logger import logger

# Single instances initialization for performance scaling
_youtube_loader = YouTubeLoader()  
_website_loader = WebsiteLoader()
_github_loader = GitHubLoader()
_vector_db = VectorDBEngine()
_rag_pipeline = RAGPipeline()

def ingest_youtube(url: str, db: Session) -> dict:
    """
    YouTube URL parsing, vector embedding upsertion, aur transactional database log logging.
    """
    logger.info(f"Triggering YouTube ingestion service for URL: {url}")
    try:
        # Loader response se raw string text extract kar rahe hain
        loader_response = _youtube_loader.load(url)
        raw_text = loader_response[0]["text"] if loader_response else ""
        
        chunks = create_chunks(raw_text)
        
        if not chunks:
            raise ValueError("No extractable transcript found for the provided YouTube URL.")

        _vector_db.upsert_chunks(
            chunks=chunks,
            source_name=url,
            source_type="youtube"
        )
        
        _rag_pipeline.initialize_lexical_index(chunks)

        # Relational MySQL table record population
        db_doc = Document(
            source_name=url,
            source_type="youtube",
            total_chunks=len(chunks)
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        logger.info(f"Successfully processed and cataloged YouTube source.")
        return {"document_id": db_doc.id, "status": "success", "total_chunks": len(chunks)}
    except Exception as e:
        db.rollback()
        logger.error(f"YouTube ingestion failed: {str(e)}")
        raise Exception(f"YouTube Pipeline Error: {str(e)}")


def ingest_website(url: str, db: Session) -> dict:
    """
    Web scraper parser data extraction, matrix validation, aur catalog logging.
    """
    logger.info(f"Triggering Website scraping ingestion for URL: {url}")
    try:
        # Loader ko call kiya
        loader_response = _website_loader.load(url)
        
        # 🔥 FIX: Check karo agar response pehle se string hai toh direct use karo, 
        # nahi toh list samajh kar extract karo
        if isinstance(loader_response, str):
            raw_text = loader_response
        else:
            raw_text = loader_response[0]["text"] if loader_response else ""
        
        chunks = create_chunks(raw_text)
        
        if not chunks:
            raise ValueError("No extractable textual data fetched from the webpage URL.")

        _vector_db.upsert_chunks(
            chunks=chunks,
            source_name=url,
            source_type="website"
        )
        
        _rag_pipeline.initialize_lexical_index(chunks)

        db_doc = Document(
            source_name=url,
            source_type="website",
            total_chunks=len(chunks)
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        logger.info(f"Successfully scraped and index mapped website source.")
        return {"document_id": db_doc.id, "status": "success", "total_chunks": len(chunks)}
    except Exception as e:
        db.rollback()
        logger.error(f"Website ingestion broken down: {str(e)}")
        raise Exception(f"Website Pipeline Error: {str(e)}")


def ingest_github(url: str, db: Session) -> dict:
    """
    GitHub deep code-repository clone parse engine integration with multiple file tracking.
    """
    logger.info(f"Triggering GitHub Repository recursive ingestion for URL: {url}")
    try:
        repo_files = _github_loader.load(url)
        
        total_chunks_processed = 0
        all_corpus_chunks = []

        for file_obj in repo_files:
            file_name_path = f"{url}/{file_obj['file_path']}"
            file_text = file_obj["text"]
            
            # GitHub loader already file iteration ke andar pure string de raha hai
            file_chunks = create_chunks(file_text)
            if not file_chunks:
                continue
                
            total_chunks_processed += len(file_chunks)
            all_corpus_chunks.extend(file_chunks)

            _vector_db.upsert_chunks(
                chunks=file_chunks,
                source_name=file_name_path,
                source_type="github"
            )

        if total_chunks_processed == 0:
            raise ValueError("No parsable code assets found inside the target Git repository.")

        _rag_pipeline.initialize_lexical_index(all_corpus_chunks)

        db_doc = Document(
            source_name=url,
            source_type="github",
            total_chunks=total_chunks_processed
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        logger.info(f"Deep scanned and indexed GitHub repository codebase safely.")
        return {"document_id": db_doc.id, "status": "success", "total_chunks": total_chunks_processed}
    except Exception as e:
        db.rollback()
        logger.error(f"GitHub deep ingest runtime collapse: {str(e)}")
        raise Exception(f"GitHub Pipeline Error: {str(e)}")
    
def auto_ingest(url: str, db: Session) -> dict:
    """
    URL check karke automatically sahi loader (YouTube, GitHub, ya Website) select karta hai.
    """
    clean_url = url.strip().lower()
    
    # 1. Check for YouTube
    if "youtube.com" in clean_url or "youtu.be" in clean_url:
        logger.info(f"Auto-detected YouTube URL type for: {url}")
        return ingest_youtube(url, db)
        
    # 2. Check for GitHub
    elif "github.com" in clean_url:
        logger.info(f"Auto-detected GitHub Repository type for: {url}")
        return ingest_github(url, db)
        
    # 3. Fallback to Website
    else:
        logger.info(f"Auto-detected standard Webpage type for: {url}")
        return ingest_website(url, db)