from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, field_validator

class Settings(BaseSettings):
    MYSQL_HOST: str = Field(default="localhost")
    MYSQL_PORT: int = Field(default=3306)
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str

    
    GROQ_API_KEY: str

    
    CHROMA_DB_PATH: str = Field(default="storage/chroma")
    COLLECTION_NAME: str = "rag_collection"
    
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")

    
    PROJECT_NAME: str = "Modular RAG System"
    API_V1_STR: str = "/api/v1"

   
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" 
    )

    @field_validator("MYSQL_PORT")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("MySQL Port must be between 1 and 65535")
        return v

settings = Settings()