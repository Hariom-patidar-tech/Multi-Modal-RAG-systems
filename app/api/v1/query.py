from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, Literal
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.query import QueryRequest
from app.services.query_service import ask_question

router = APIRouter()

@router.post("/documents")
async def query_documents(
    request: QueryRequest,
    doc_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    """
    Sirf PDF/Document mein search.
    Agar doc_id doge to specific file, nahi to saare documents mein.
    """
    return ask_question(
        question=request.question,
        db=db,
        doc_id=doc_id,
        source_type="document"
    )


@router.post("/external")
async def query_external(
    request: QueryRequest,
    source_type: Optional[Literal["youtube", "website", "github"]] = Query(
        default=None,
        description="Optional: sirf ek specific source mein search karne ke liye (youtube/website/github). Khali rakho to teeno mein search hoga."
    ),
    db: Session = Depends(get_db)
):
    """
    YouTube, Website aur GitHub mein search.
    source_type query param doge to sirf wahi source filter hoga, nahi to teeno mein search hoga.
    """
    
    effective_filter = source_type if source_type else ["youtube", "website", "github"]

    return ask_question(
        question=request.question,
        db=db,
        source_type=effective_filter
    )