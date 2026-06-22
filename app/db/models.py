import json
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(255), nullable=False)   
    source_type = Column(String(50), nullable=False)    
    status = Column(String(50), default="pending")      
    total_chunks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    _metadata = Column("metadata", Text, nullable=True, default="{}")

    
    chunks = relationship("DocumentChunk", back_populates="source", cascade="all, delete-orphan")

    @property
    def metadata_dict(self):
        return json.loads(self._metadata or "{}")

    @metadata_dict.setter
    def metadata_dict(self, value):
        self._metadata = json.dumps(value or {})


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)       
    content = Column(Text, nullable=False)             
    chroma_id = Column(String(100), unique=True, index=True)  
    
    chunk_metadata = Column(Text, nullable=True, default="{}") 

  
    source = relationship("Source", back_populates="chunks")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Document = Source