# app/schemas/source.py
from pydantic import BaseModel
from typing import Literal

class UnifiedIngestRequest(BaseModel):
    url: str
    source_type: Literal["youtube", "github", "website"]  # Sirf yehi types accept hongi