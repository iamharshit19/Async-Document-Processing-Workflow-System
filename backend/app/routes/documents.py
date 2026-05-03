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
from ..worker import process_document_task, celery_app
from ..storage import storage
from ..auth import get_current_user

router = APIRouter()

@router.post("/upload", response_model=List[DocumentResponse])
def upload_documents(files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    results = []
    for file in files:
        file_path = storage.save_file(file.filename, file)
        file_size = storage.get_file_size(file_path)

        db_doc = Document(
            filename=file.filename,
            content_type=file.content_type,
            size=file_size,
            status=JobStatus.QUEUED
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        task = process_document_task.delay(db_doc.id)
        db_doc.task_id = task.id
        db.commit()
        
        results.append(db_doc)

    return results

@router.get("", response_model=PaginatedDocumentResponse)
def list_documents(
    skip: int = 0, 
    limit: int = 20, 
    status: Optional[JobStatus] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status)
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))
        
    total = query.count()
    
    if hasattr(Document, sort_by):
        sort_attr = getattr(Document, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(desc(Document.created_at))

    items = query.offset(skip).limit(limit).all()
    
    return {"items": items, "total": total}

@router.get("/{id}", response_model=DocumentResponse)
def get_document(id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.put("/{id}/data", response_model=DocumentResponse)
def update_extracted_data(id: int, update_data: ExtractedDataUpdate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc or not doc.extracted_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
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
def finalize_document(id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc or not doc.extracted_data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    doc.extracted_data.is_finalized = True
    db.commit()
    db.refresh(doc)
    return doc

@router.post("/{id}/retry", response_model=DocumentResponse)
def retry_job(id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != JobStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    
    doc.status = JobStatus.QUEUED

    if doc.extracted_data:
        db.delete(doc.extracted_data)
        
    db.commit()
    db.refresh(doc)
    
    task = process_document_task.delay(doc.id)
    doc.task_id = task.id
    db.commit()
    return doc

@router.post("/{id}/cancel", response_model=DocumentResponse)
def cancel_job(id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status not in [JobStatus.QUEUED, JobStatus.PROCESSING]:
        raise HTTPException(status_code=400, detail="Only queued or processing jobs can be cancelled")
    
    if doc.task_id:
        celery_app.control.revoke(doc.task_id, terminate=True)
        
    doc.status = JobStatus.FAILED
    db.commit()
    db.refresh(doc)
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
