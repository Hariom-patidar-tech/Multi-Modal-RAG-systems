from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends
)
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.ingestion_service import (
    process_pdf
)

router = APIRouter()


@router.post("/upload")
async def upload_documents(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload PDF document and ingest into RAG pipeline.
    """

    result = process_pdf(
        file=file,
        db=db
    )

    return result