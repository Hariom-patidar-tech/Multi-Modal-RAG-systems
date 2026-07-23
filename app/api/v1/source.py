from fastapi import APIRouter, Depends, HTTPException

from app.schemas.source import UnifiedIngestRequest
from app.services.source_service import ingest_youtube, ingest_website, ingest_github

router = APIRouter()


@router.post("/ingest")
def ingest_unified(payload: UnifiedIngestRequest):
    """
    Ab se sirf ye ek endpoint use hoga sabhi sources ke liye.
    """
    try:
        if payload.source_type == "youtube":
            return ingest_youtube(payload.url )
        elif payload.source_type == "website":
            return ingest_website(payload.url )
        elif payload.source_type == "github":
            return ingest_github(payload.url)
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))