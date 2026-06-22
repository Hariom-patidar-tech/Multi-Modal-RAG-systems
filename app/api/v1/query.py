from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.query import QueryRequest
from app.services.query_service import ask_question

router = APIRouter()

@router.post("/documents")
async def query_documents(
    request: QueryRequest, 
    doc_id: Optional[int] = None, # Optional: Specific document ke liye
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
    doc_id: Optional[int] = None, # Optional: Specific link ke liye
    db: Session = Depends(get_db)
):
    """
    Web, Github aur YouTube mein search.
    """
    return ask_question(
        question=request.question, 
        db=db, 
        doc_id=doc_id, 
        source_type=["web", "github", "youtube"]
    )