import enum
import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class JobStatus(str, enum.Enum):
    QUEUED = "Queued"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content_type = Column(String)
    size = Column(Integer)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    extracted_data = relationship("ExtractedData", back_populates="document", uselist=False, cascade="all, delete-orphan")

class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    title = Column(String, nullable=True)
    category = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)
    is_finalized = Column(Boolean, default=False)
    
    document = relationship("Document", back_populates="extracted_data")
