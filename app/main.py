from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.models import Base
from app.db.session import engine

# Base.metadata.create_all(bind=engine)
from app.api.v1.health import router as health_router
from app.api.v1.document import router as document_router
from app.api.v1.query import router as query_router
from app.api.v1.source import router as source_router
from app.core.config import settings
from app.core.logger import logger

app = FastAPI(
    title="Multi-Source RAG Platform",
    version="1.0.0",
    description="Enterprise-grade modular RAG platform with Hybrid Search, Reranking & Multi-Source Ingestion"
)
# Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root Gateway"])
async def root():
    """
    RAG Core platform entrance system connectivity baseline test.
    """
    return {
        "status": "online",
        "message": "Production-Grade Multi-Source RAG Platform Running Successfully",
        "documentation": "/docs"  
    }


app.include_router(
    health_router,
    prefix="/api/v1/health",
    tags=["Health Status Check"]
)


app.include_router(
    document_router,
    prefix="/api/v1/document",
    tags=["Structured Documents Engine"]
)


app.include_router(
    query_router,
    prefix="/api/v1/query",
    tags=["Advanced RAG Query Processing Engine"]
)


app.include_router(
    source_router,
    prefix="/api/v1/source",
    tags=["External Source Ingestion Channels"]
)


logger.info("FastAPI Matrix Root App successfully aggregated and structured hooks armed!")
