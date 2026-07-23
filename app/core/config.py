from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    GROQ_API_KEY: str

    CHROMA_DB_PATH: str = "storage/chroma"
    COLLECTION_NAME: str = "rag_collection"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    PROJECT_NAME: str = "Modular RAG System"
    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()