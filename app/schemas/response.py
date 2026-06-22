from pydantic import BaseModel
from typing import List


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]


class UploadResponse(BaseModel):
    filename: str
    total_chunks: int
    status: str


class SourceResponse(BaseModel):
    status: str
    source_type: str