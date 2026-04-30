from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import JobStatus

class ExtractedDataBase(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_finalized: bool = False

class ExtractedDataResponse(ExtractedDataBase):
    id: int
    document_id: int

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    extracted_data: Optional[ExtractedDataResponse] = None

    class Config:
        from_attributes = True

class ExtractedDataUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None

class PaginatedDocumentResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
