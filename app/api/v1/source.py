from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.source import UnifiedIngestRequest
from app.services.source_service import ingest_youtube, ingest_website, ingest_github

router = APIRouter()


@router.post("/ingest")
def ingest_unified(payload: UnifiedIngestRequest, db: Session = Depends(get_db)):
    """
    Ab se sirf ye ek endpoint use hoga sabhi sources ke liye.
    """
    try:
        if payload.source_type == "youtube":
            return ingest_youtube(payload.url, db)
        elif payload.source_type == "website":
            return ingest_website(payload.url, db)
        elif payload.source_type == "github":
            return ingest_github(payload.url, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))