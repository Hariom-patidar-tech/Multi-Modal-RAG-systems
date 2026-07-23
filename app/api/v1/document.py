from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)


from app.services.ingestion_service import process_document

router = APIRouter()


@router.post("/upload")
async def upload_documents(
    file: UploadFile = File(...),
    
):
    """
    Upload document (PDF, DOCX, ya TXT) and ingest into RAG pipeline.
    File extension ke hisaab se sahi loader automatically use hota hai.
    """
    try:
        result = process_document(
            file=file,
            
        )
        return result
    except ValueError as e:
        
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))