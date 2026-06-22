
from pydantic import BaseModel


class SourceRequest(BaseModel):
    url: str