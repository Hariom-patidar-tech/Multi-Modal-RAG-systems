from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.ingestion_service import process_document

router = APIRouter()


@router.post("/upload")
async def upload_documents(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload document (PDF, DOCX, ya TXT) and ingest into RAG pipeline.
    File extension ke hisaab se sahi loader automatically use hota hai.
    """
    try:
        result = process_document(
            file=file,
            db=db
        )
        return result
    except ValueError as e:
        # Unsupported file type ya empty content
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))