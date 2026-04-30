import os
import shutil
import csv
from io import StringIO
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models import Document, ExtractedData, JobStatus
from ..schemas import DocumentResponse, ExtractedDataUpdate, PaginatedDocumentResponse
from ..config import settings
from ..worker import process_document_task

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    
    # Create DB entry
    db_doc = Document(
        filename=file.filename,
        content_type=file.content_type,
        size=file_size,
        status=JobStatus.QUEUED
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Dispatch Celery task
    process_document_task.delay(db_doc.id)

    return db_doc

@router.get("", response_model=PaginatedDocumentResponse)
def list_documents(
    skip: int = 0, 
    limit: int = 20, 
    status: Optional[JobStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status)
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))
        
    total = query.count()
    items = query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
    
    return {"items": items, "total": total}

@router.get("/{id}", response_model=DocumentResponse)
def get_document(id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.put("/{id}/data", response_model=DocumentResponse)
def update_extracted_data(id: int, update_data: ExtractedDataUpdate, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc or not doc.extracted_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    # Update fields
    if update_data.title is not None:
        doc.extracted_data.title = update_data.title
    if update_data.category is not None:
        doc.extracted_data.category = update_data.category
    if update_data.summary is not None:
        doc.extracted_data.summary = update_data.summary
    if update_data.keywords is not None:
        doc.extracted_data.keywords = update_data.keywords
        
    db.commit()
    db.refresh(doc)
    return doc

@router.post("/{id}/finalize", response_model=DocumentResponse)
def finalize_document(id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc or not doc.extracted_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    doc.extracted_data.is_finalized = True
    db.commit()
    db.refresh(doc)
    return doc

@router.post("/{id}/retry", response_model=DocumentResponse)
def retry_job(id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != JobStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    
    doc.status = JobStatus.QUEUED
    # Delete old extracted data if any
    if doc.extracted_data:
        db.delete(doc.extracted_data)
        
    db.commit()
    db.refresh(doc)
    
    # Dispatch
    process_document_task.delay(doc.id)
    return doc

@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    docs = db.query(Document).join(ExtractedData).filter(ExtractedData.is_finalized == True).all()
    
    f = StringIO()
    writer = csv.writer(f)
    writer.writerow(["ID", "Filename", "Title", "Category", "Summary", "Keywords"])
    
    for doc in docs:
        writer.writerow([
            doc.id,
            doc.filename,
            doc.extracted_data.title,
            doc.extracted_data.category,
            doc.extracted_data.summary,
            ",".join(doc.extracted_data.keywords) if doc.extracted_data.keywords else ""
        ])
        
    response = Response(content=f.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return response

@router.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    docs = db.query(Document).join(ExtractedData).filter(ExtractedData.is_finalized == True).all()
    data = []
    for doc in docs:
        data.append({
            "id": doc.id,
            "filename": doc.filename,
            "title": doc.extracted_data.title,
            "category": doc.extracted_data.category,
            "summary": doc.extracted_data.summary,
            "keywords": doc.extracted_data.keywords
        })
    return data
