# app/api/v1/source.py

from fastapi import APIRouter, Depends, HTTPException  # 👈 HTTPException yahan se aayega
from sqlalchemy.orm import Session
from pydantic import BaseModel  # 👈 BaseModel yahan se aayega
from app.db.session import get_db
from app.services.source_service import auto_ingest, ingest_youtube, ingest_website, ingest_github

router = APIRouter()

# 👈 IngestRequest class ko yahan define kar diya
class IngestRequest(BaseModel):
    url: str

@router.post("/auto-ingest")
def api_auto_ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    try:
        response = auto_ingest(payload.url, db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Agar aapko purane teenon endpoints bhi rakhne hain toh unhe niche rehne de sakte hain:
@router.post("/youtube")
def youtube_source(payload: IngestRequest, db: Session = Depends(get_db)):
    return ingest_youtube(payload.url, db)

@router.post("/website")
def website_source(payload: IngestRequest, db: Session = Depends(get_db)):
    return ingest_website(payload.url, db)

@router.post("/github")
def github_source(payload: IngestRequest, db: Session = Depends(get_db)):
    return ingest_github(payload.url, db)